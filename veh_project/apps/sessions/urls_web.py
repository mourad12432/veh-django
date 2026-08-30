"""
URLs web pour les sessions de jeu.
"""

from django.urls import path
from apps.stories.views_web import GameView, ChoiceView, EndingView, SceneNarrationView
from .views_web import ResumeSessionView, RestartSessionView

urlpatterns = [
    # Chemins fixes en premier (avant le wildcard <scene_key>)
    path('<slug:story_slug>/choose/', ChoiceView.as_view(), name='choose'),
    path('<slug:story_slug>/ending/', EndingView.as_view(), name='ending'),
    path('<slug:story_slug>/resume/', ResumeSessionView.as_view(), name='resume'),
    path('<slug:story_slug>/restart/', RestartSessionView.as_view(), name='restart'),
    # Narration TTS à la demande (secours Gemini) — segment supplémentaire, pas de conflit
    path('<slug:story_slug>/<str:scene_key>/narration/',
         SceneNarrationView.as_view(), name='narration'),
    # Wildcard en dernier pour ne pas capturer les routes ci-dessus
    path('<slug:story_slug>/<str:scene_key>/', GameView.as_view(), name='game'),
]
