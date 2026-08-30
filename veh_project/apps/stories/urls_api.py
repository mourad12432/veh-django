"""
URLs REST API pour les histoires et le jeu (Flutter).
"""

from django.urls import path
from .views_api import (
    StoryListAPIView,
    StoryDetailAPIView,
    SceneAPIView,
    MakeChoiceAPIView,
)

urlpatterns = [
    # Liste des histoires publiées
    path('stories/', StoryListAPIView.as_view(), name='api-stories-list'),
    # Détail d'une histoire + scène de départ
    path('stories/<slug:slug>/', StoryDetailAPIView.as_view(), name='api-story-detail'),
    # Données d'une scène
    path('play/<slug:slug>/scene/<str:scene_key>/', SceneAPIView.as_view(), name='api-scene'),
    # Faire un choix
    path('play/<slug:slug>/choose/', MakeChoiceAPIView.as_view(), name='api-choose'),
]
