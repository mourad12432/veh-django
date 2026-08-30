from django.apps import AppConfig


class GameSessionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sessions'
    label = 'game_sessions'  # Évite le conflit avec django.contrib.sessions
    verbose_name = 'Sessions de Jeu'
