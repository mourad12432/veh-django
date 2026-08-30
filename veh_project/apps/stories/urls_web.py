"""
URLs web pour les histoires (accueil, jeu, fin).
"""

from django.urls import path
from .views_web import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
]
