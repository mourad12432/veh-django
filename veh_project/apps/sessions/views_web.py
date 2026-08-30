"""
Vues web pour les sessions de jeu.
Redirige vers le jeu en reprenant la progression sauvegardée.
"""

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View

from apps.stories.models import Story
from .models import GameSession


@method_decorator(login_required, name='dispatch')
class ResumeSessionView(View):
    """
    Reprend une session de jeu existante.
    Redirige vers la dernière scène sauvegardée.
    """
    def get(self, request, story_slug):
        story = get_object_or_404(Story, slug=story_slug, is_published=True)
        session = GameSession.objects.filter(
            user=request.user,
            story=story
        ).select_related('current_scene').first()

        if session and session.current_scene and not session.is_completed:
            return redirect('game', story_slug=story_slug, scene_key=session.current_scene.scene_key)

        # Pas de session ou terminée → reprendre depuis le début
        starting = story.get_starting_scene()
        if starting:
            return redirect('game', story_slug=story_slug, scene_key=starting.scene_key)

        return redirect('home')


@method_decorator(login_required, name='dispatch')
class RestartSessionView(View):
    """
    Repart de zéro sur une histoire (supprime la session existante).
    """
    def post(self, request, story_slug):
        story = get_object_or_404(Story, slug=story_slug, is_published=True)
        GameSession.objects.filter(user=request.user, story=story).delete()

        starting = story.get_starting_scene()
        if starting:
            return redirect('game', story_slug=story_slug, scene_key=starting.scene_key)
        return redirect('home')
