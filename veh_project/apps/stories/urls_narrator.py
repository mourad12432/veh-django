"""
URLs de l'interface Narrateur (préfixe /narrateur/).
Toutes les vues sont réservées aux administrateurs — voir views_narrator.
"""

from django.urls import path

from .views_narrator import (
    AccueilView, HistoireCreateView, SceneEditView, CarteView,
)

urlpatterns = [
    path('', AccueilView.as_view(), name='narrateur_accueil'),
    path('histoire/nouvelle/', HistoireCreateView.as_view(), name='narrateur_histoire_nouvelle'),
    path('<slug:story_slug>/carte/', CarteView.as_view(), name='narrateur_carte'),
    path('<slug:story_slug>/scene/nouvelle/', SceneEditView.as_view(), name='narrateur_scene_nouvelle'),
    path('<slug:story_slug>/scene/<str:scene_key>/', SceneEditView.as_view(), name='narrateur_scene'),
]
