"""
URLs REST API pour les sessions de jeu (Flutter).
"""

from django.urls import path
from .views_api import (
    SessionListAPIView,
    SessionDetailAPIView,
    SaveSessionAPIView,
    SessionHistoryAPIView,
)

urlpatterns = [
    # Liste de toutes les sessions du joueur
    path('sessions/', SessionListAPIView.as_view(), name='api-sessions-list'),
    # Session pour une histoire spécifique
    path('sessions/<slug:story_slug>/', SessionDetailAPIView.as_view(), name='api-session-detail'),
    # Sauvegarder la progression
    path('sessions/<slug:story_slug>/save/', SaveSessionAPIView.as_view(), name='api-session-save'),
    # Historique des choix
    path('sessions/<slug:story_slug>/history/', SessionHistoryAPIView.as_view(), name='api-session-history'),
]
