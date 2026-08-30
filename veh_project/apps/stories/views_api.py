"""
Vues REST API pour les histoires et le jeu (Flutter — Phase 2).
Tous les endpoints requièrent une authentification JWT.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from .models import Story, Scene, Choice
from .serializers import StoryListSerializer, StoryDetailSerializer, SceneSerializer
from apps.sessions.models import GameSession, SessionHistory


class StoryListAPIView(APIView):
    """
    GET /api/stories/
    Retourne la liste de toutes les histoires publiées.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        stories = Story.objects.filter(is_published=True)
        serializer = StoryListSerializer(stories, many=True, context={'request': request})
        return Response(serializer.data)


class StoryDetailAPIView(APIView):
    """
    GET /api/stories/<slug>/
    Retourne le détail d'une histoire avec sa scène de départ.
    """
    permission_classes = [AllowAny]

    def get(self, request, slug):
        story = get_object_or_404(Story, slug=slug, is_published=True)
        serializer = StoryDetailSerializer(story, context={'request': request})
        return Response(serializer.data)


class SceneAPIView(APIView):
    """
    GET /api/play/<slug>/scene/<scene_key>/
    Retourne les données d'une scène (texte, image, musique, choix).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, slug, scene_key):
        story = get_object_or_404(Story, slug=slug, is_published=True)

        # "auto" → reprendre la dernière scène sauvegardée
        if scene_key == 'auto':
            session = GameSession.objects.filter(
                user=request.user,
                story=story
            ).select_related('current_scene').first()
            if session and not session.is_completed:
                scene_key = session.current_scene.scene_key
            else:
                starting = story.get_starting_scene()
                if not starting:
                    return Response(
                        {'error': 'Aucune scène de départ définie.'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                scene_key = starting.scene_key

        scene = get_object_or_404(Scene, story=story, scene_key=scene_key)

        # Mettre à jour ou créer la session
        session, _ = GameSession.objects.get_or_create(
            user=request.user,
            story=story,
            defaults={'current_scene': scene, 'platform': 'mobile'}
        )
        session.current_scene = scene
        session.platform = 'mobile'
        session.save(update_fields=['current_scene', 'platform', 'last_played'])

        serializer = SceneSerializer(scene, context={'request': request})
        return Response(serializer.data)


class MakeChoiceAPIView(APIView):
    """
    POST /api/play/<slug>/choose/
    Corps : {"choice_id": 42}
    Enregistre le choix du joueur et retourne la scène suivante.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        story = get_object_or_404(Story, slug=slug, is_published=True)
        choice_id = request.data.get('choice_id')

        if not choice_id:
            return Response(
                {'error': 'choice_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        choice = get_object_or_404(Choice, id=choice_id, scene__story=story)
        session = get_object_or_404(GameSession, user=request.user, story=story)

        # Enregistrer l'historique
        SessionHistory.objects.create(
            session=session,
            scene=session.current_scene,
            choice_made=choice
        )

        if not choice.next_scene:
            session.is_completed = True
            session.save(update_fields=['is_completed'])
            return Response({'message': 'Histoire terminée.', 'is_completed': True})

        # Mettre à jour la scène courante
        session.current_scene = choice.next_scene
        if choice.next_scene.is_ending:
            session.is_completed = True
        session.save(update_fields=['current_scene', 'is_completed', 'last_played'])

        next_scene_serializer = SceneSerializer(
            choice.next_scene, context={'request': request}
        )
        return Response({
            'next_scene': next_scene_serializer.data,
            'is_completed': session.is_completed
        })
