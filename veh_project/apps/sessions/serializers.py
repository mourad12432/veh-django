"""
Serializers DRF pour les sessions de jeu (API Flutter).
"""

from rest_framework import serializers
from .models import GameSession, SessionHistory


class SessionHistorySerializer(serializers.ModelSerializer):
    """Entrée de l'historique d'une session."""
    scene_key = serializers.CharField(source='scene.scene_key', read_only=True)
    choice_text = serializers.SerializerMethodField()

    class Meta:
        model = SessionHistory
        fields = ('scene_key', 'choice_text', 'visited_at')

    def get_choice_text(self, obj):
        return obj.choice_made.text if obj.choice_made else None


class GameSessionSerializer(serializers.ModelSerializer):
    """Session de jeu complète — partagée web et mobile."""
    story_slug = serializers.CharField(source='story.slug', read_only=True)
    story_title = serializers.CharField(source='story.title', read_only=True)
    current_scene_key = serializers.SerializerMethodField()
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = GameSession
        fields = (
            'id', 'story_slug', 'story_title',
            'current_scene_key', 'started_at', 'last_played',
            'is_completed', 'platform', 'progress_percentage'
        )

    def get_current_scene_key(self, obj):
        return obj.current_scene.scene_key if obj.current_scene else None
