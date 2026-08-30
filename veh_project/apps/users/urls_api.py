"""
URLs REST API pour l'authentification (utilisées par Flutter).
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views_api

urlpatterns = [
    # Inscription
    path('register/', views_api.RegisterAPIView.as_view(), name='api-register'),
    # Connexion → retourne JWT access + refresh tokens
    path('login/', TokenObtainPairView.as_view(), name='api-login'),
    # Rafraîchir le token d'accès
    path('refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    # Profil de l'utilisateur connecté
    path('me/', views_api.ProfileAPIView.as_view(), name='api-profile'),
]
