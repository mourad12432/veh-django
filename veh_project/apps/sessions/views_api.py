"""
Vues REST API pour la gestion des sessions de jeu (Flutter).
Permet la synchronisation transparente web ↔ mobile.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.stories.models import Story, Scene
from .models import GameSession
from .serializers import GameSessionSerializer, SessionHistorySerializer


class SessionListAPIView(APIView):
    """
    GET /api/sessions/
    Retourne toutes les sessions du joueur connecté.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = GameSession.objects.filter(
            user=request.user
        ).select_related('story', 'current_scene')
        serializer = GameSessionSerializer(sessions, many=True)
        return Response(serializer.data)


class SessionDetailAPIView(APIView):
    """
    GET /api/sessions/<story_slug>/
    Retourne la session en cours pour une histoire donnée.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, story_slug):
        story = get_object_or_404(Story, slug=story_slug, is_published=True)
        session = get_object_or_404(
            GameSession,
            user=request.user,
            story=story
        )
        serializer = GameSessionSerializer(session)
        return Response(serializer.data)


class SaveSessionAPIView(APIView):
    """
    POST /api/sessions/<story_slug>/save/
    Corps : {"scene_key": "scene_01", "platform": "mobile"}
    Sauvegarde la progression — crée ou met à jour la session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, story_slug):
        story = get_object_or_404(Story, slug=story_slug, is_published=True)
        scene_key = request.data.get('scene_key')
        platform = request.data.get('platform', 'mobile')

        if not scene_key:
            return Response(
                {'error': 'scene_key est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        scene = get_object_or_404(Scene, story=story, scene_key=scene_key)

        session, created = GameSession.objects.get_or_create(
            user=request.user,
            story=story,
            defaults={
                'current_scene': scene,
                'platform': platform
            }
        )

        if not created:
            session.current_scene = scene
            session.platform = platform
            if scene.is_ending:
                session.is_completed = True
            session.save(update_fields=['current_scene', 'platform', 'is_completed', 'last_played'])

        serializer = GameSessionSerializer(session)
        return Response(
            {
                'message': 'Progression sauvegardée.',
                'session': serializer.data
            },
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
        )


class SessionHistoryAPIView(APIView):
    """
    GET /api/sessions/<story_slug>/history/
    Retourne l'historique complet des choix pour une session.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, story_slug):
        story = get_object_or_404(Story, slug=story_slug, is_published=True)
        session = get_object_or_404(GameSession, user=request.user, story=story)
        history = session.history.select_related('scene', 'choice_made').order_by('visited_at')
        serializer = SessionHistorySerializer(history, many=True)
        return Response(serializer.data)
