"""
Vues web pour le jeu narratif VEH (Django Templates).
Gère la navigation entre scènes, les choix, et les fins.
"""

import hashlib
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.conf import settings
from django.http import FileResponse, HttpResponse

from .models import Story, Scene, Choice
from apps.sessions.models import GameSession, SessionHistory
from .services.gemini_service import GeminiService
from .services import tts_service


class HomeView(View):
    """Page d'accueil — liste toutes les histoires publiées."""
    template_name = 'stories/home.html'

    def get(self, request):
        stories = Story.objects.filter(is_published=True).order_by('-created_at')

        # Pour chaque histoire, vérifier si l'utilisateur a une session en cours
        user_sessions = {}
        if request.user.is_authenticated:
            sessions = GameSession.objects.filter(
                user=request.user,
                story__in=stories
            ).select_related('story', 'current_scene')
            user_sessions = {s.story_id: s for s in sessions}

        # Associer chaque histoire à la session de l'utilisateur
        stories_with_sessions = []
        for story in stories:
            session = user_sessions.get(story.id)
            stories_with_sessions.append({
                'story': story,
                'session': session,
            })

        context = {
            'stories_with_sessions': stories_with_sessions,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class GameView(View):
    """
    Vue principale de jeu.
    URL : /play/<story_slug>/<scene_key>/
    Charge la scène demandée et crée/reprend la session du joueur.
    Si scene_key == "auto", reprend la dernière scène sauvegardée.
    """
    template_name = 'stories/game.html'

    def get(self, request, story_slug, scene_key):
        story = get_object_or_404(Story, slug=story_slug, is_published=True)

        # Résoudre "auto" → dernière scène sauvegardée ou scène de départ
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
                    messages.error(request, 'Cette histoire n\'a pas encore de scène de départ.')
                    return redirect('home')
                scene_key = starting.scene_key

        scene = get_object_or_404(Scene, story=story, scene_key=scene_key)

        # Créer ou reprendre la session de jeu
        session, created = GameSession.objects.get_or_create(
            user=request.user,
            story=story,
            defaults={
                'current_scene': scene,
                'platform': 'web'
            }
        )

        # Mettre à jour la scène courante si la session existe déjà
        if not created:
            session.current_scene = scene
            session.platform = 'web'
            update_fields = ['current_scene', 'platform', 'last_played']
            # Le joueur rejoue après avoir vu une fin : la session repart en
            # cours tant qu'il n'est pas sur une scène finale.
            if session.is_completed and not scene.is_ending:
                session.is_completed = False
                update_fields.append('is_completed')
            session.save(update_fields=update_fields)

        # Enrichir le texte narratif avec Gemini (optionnel)
        enriched_narrative = scene.narrative
        if request.GET.get('enrich') == '1':
            gemini = GeminiService()
            enriched_narrative = gemini.enrich_narrative(
                scene_narrative=scene.narrative,
                story_title=story.title
            )

        # Récupérer les choix disponibles
        choices = scene.choices.select_related('next_scene').all()

        # Choix déjà empruntés par ce joueur à cette scène (toutes parties confondues).
        # Sert à mettre en avant les chemins jamais essayés → rejouabilité / autres fins.
        explored_choice_ids = set(
            SessionHistory.objects.filter(
                session__user=request.user, scene=scene
            ).values_list('choice_made_id', flat=True)
        )

        context = {
            'story': story,
            'scene': scene,
            'choices': choices,
            'session': session,
            'narrative': enriched_narrative,
            'music_file': scene.music_file,
            'music_transition': scene.music_transition,
            'explored_choice_ids': explored_choice_ids,
            'is_revisit': bool(explored_choice_ids),
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class ChoiceView(View):
    """
    Vue POST — traite le choix du joueur.
    URL : /play/<story_slug>/choose/
    Met à jour la session et redirige vers la nouvelle scène.
    """
    def post(self, request, story_slug):
        story = get_object_or_404(Story, slug=story_slug, is_published=True)
        choice_id = request.POST.get('choice_id')

        if not choice_id:
            messages.error(request, 'Choix invalide.')
            return redirect('home')

        choice = get_object_or_404(
            Choice,
            id=choice_id,
            scene__story=story
        )

        # Récupérer la session en cours
        session = get_object_or_404(GameSession, user=request.user, story=story)

        # Enregistrer ce choix dans l'historique. La scène d'origine du choix
        # fait foi : elle ne peut pas être désynchronisée de ce que le joueur
        # avait sous les yeux, contrairement à session.current_scene — et c'est
        # elle qui sert ensuite à repérer les chemins déjà explorés.
        SessionHistory.objects.create(
            session=session,
            scene=choice.scene,
            choice_made=choice
        )

        # Si le choix mène à une scène finale
        if choice.next_scene:
            session.current_scene = choice.next_scene
            session.save(update_fields=['current_scene', 'last_played'])

            # Rediriger vers la fin si c'est une scène de fin
            if choice.next_scene.is_ending:
                return redirect('ending', story_slug=story_slug)

            return redirect('game', story_slug=story_slug, scene_key=choice.next_scene.scene_key)

        # Pas de scène suivante → fin de l'histoire
        return redirect('ending', story_slug=story_slug)


@method_decorator(login_required, name='dispatch')
class EndingView(View):
    """
    Vue de fin d'histoire.
    URL : /play/<story_slug>/ending/
    Marque la session comme terminée et affiche le résumé du parcours.
    """
    template_name = 'stories/ending.html'

    def get(self, request, story_slug):
        story = get_object_or_404(Story, slug=story_slug, is_published=True)
        session = get_object_or_404(GameSession, user=request.user, story=story)

        # Marquer la session comme terminée
        if not session.is_completed:
            session.is_completed = True
            session.save(update_fields=['is_completed'])

        # Récupérer l'historique complet du parcours
        history = SessionHistory.objects.filter(
            session=session
        ).select_related('scene', 'choice_made').order_by('visited_at')

        context = {
            'story': story,
            'session': session,
            'ending_scene': session.current_scene,
            'history': history,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class SceneNarrationView(View):
    """
    Narration audio d'une scène, générée à la volée via Gemini TTS puis mise en
    cache dans media/narration_cache/. Sert de secours automatique quand aucun
    fichier audio n'existe (ni upload admin, ni static/narrations/).

    Réponses :
      200 audio/wav  → l'audio (généré, ou relu depuis le cache)
      204 No Content → génération impossible (pas de clé API, quota, texte vide) ;
                       le front bascule alors sur la synthèse vocale du navigateur.
    """

    def get(self, request, story_slug, scene_key):
        story = get_object_or_404(Story, slug=story_slug, is_published=True)
        scene = get_object_or_404(Scene, story=story, scene_key=scene_key)

        # Narration uploadée dans l'admin : on la sert telle quelle.
        if scene.audio_narration:
            return redirect(scene.audio_narration.url)

        text = tts_service.build_prompt(scene.narrative)
        if not text.strip():
            return HttpResponse(status=204)

        cache_dir = Path(settings.MEDIA_ROOT) / 'narration_cache'
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Le hash du texte invalide automatiquement le cache si la scène est modifiée.
        digest = hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]
        cache_path = cache_dir / f'{scene.id}_{digest}.wav'

        if not cache_path.exists():
            try:
                client = tts_service.get_client()
                pcm, rate = tts_service.synthesize(client, text)
                tts_service.write_wav(cache_path, pcm, rate)
            except Exception:
                # Pas de clé, quota dépassé, SDK absent... → repli navigateur (204)
                return HttpResponse(status=204)

        response = FileResponse(open(cache_path, 'rb'), content_type='audio/wav')
        response['Cache-Control'] = 'public, max-age=86400'
        return response
