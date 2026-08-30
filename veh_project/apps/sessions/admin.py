"""
Interface d'administration Django pour les sessions de jeu.
"""

from django.contrib import admin
from .models import GameSession, SessionHistory


class SessionHistoryInline(admin.TabularInline):
    """Affiche l'historique dans l'admin de la session."""
    model = SessionHistory
    extra = 0
    readonly_fields = ('scene', 'choice_made', 'visited_at')
    can_delete = False


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    """Admin complet pour les sessions de jeu."""
    list_display = (
        'user', 'story', 'current_scene',
        'last_played', 'platform', 'is_completed', 'progress_percentage'
    )
    list_filter = ('is_completed', 'platform', 'story')
    search_fields = ('user__username', 'story__title')
    readonly_fields = ('id', 'started_at', 'last_played')
    inlines = [SessionHistoryInline]

    def progress_percentage(self, obj):
        return f"{obj.progress_percentage}%"
    progress_percentage.short_description = 'Progression'


@admin.register(SessionHistory)
class SessionHistoryAdmin(admin.ModelAdmin):
    """Admin pour l'historique des choix."""
    list_display = ('session', 'scene', 'choice_made', 'visited_at')
    list_filter = ('session__story',)
    readonly_fields = ('visited_at',)
