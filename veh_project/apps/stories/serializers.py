"""
Serializers DRF pour l'API jeu (Flutter).
"""

from rest_framework import serializers
from django.contrib.staticfiles import finders
from django.templatetags.static import static as static_url

from .models import Story, Scene, Choice
from apps.sessions.models import SessionHistory

# Extensions testées pour les images/audio statiques par scène (même ordre que le web)
_IMAGE_EXTS = ('png', 'jpg', 'jpeg', 'jfif', 'webp')
_AUDIO_EXTS = ('mp3', 'wav')


def _static_asset_url(request, subfolder, key, extensions):
    """
    Cherche un fichier statique nommé par scene_key (ex: static/scenes/cottage.png)
    et renvoie son URL absolue si le fichier existe réellement sur le disque.
    Permet au mobile de voir les mêmes images/sons que le web, sans upload admin.
    """
    for ext in extensions:
        rel = f'{subfolder}/{key}.{ext}'
        if finders.find(rel):
            url = static_url(rel)
            return request.build_absolute_uri(url) if request else url
    return None


def _explored_choice_ids(request, scene):
    """
    Ids des choix que ce joueur a déjà empruntés dans cette scène, toutes
    parties confondues (même règle que la vue web `GameView`).
    Sert à mettre en avant les chemins jamais essayés → autres fins.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return frozenset()
    return frozenset(
        SessionHistory.objects
        .filter(session__user=user, scene=scene)
        .exclude(choice_made=None)
        .values_list('choice_made_id', flat=True)
    )


class ChoiceSerializer(serializers.ModelSerializer):
    """Choix proposé au joueur, avec la clé de la scène suivante."""
    next_scene_key = serializers.SerializerMethodField()
    is_explored = serializers.SerializerMethodField()

    class Meta:
        model = Choice
        fields = ('id', 'text', 'next_scene_key', 'order', 'is_explored')

    def get_next_scene_key(self, obj):
        return obj.next_scene.scene_key if obj.next_scene else None

    def get_is_explored(self, obj):
        # Rempli une fois pour toute la scène par SceneSerializer : une seule
        # requête, quel que soit le nombre de choix.
        return obj.id in self.context.get('explored_choice_ids', ())


class SceneSerializer(serializers.ModelSerializer):
    """Scène complète avec ses choix, pour l'API Flutter."""
    choices = ChoiceSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    audio_narration_url = serializers.SerializerMethodField()
    is_revisit = serializers.SerializerMethodField()

    class Meta:
        model = Scene
        fields = (
            'id', 'scene_key', 'narrative', 'image_url',
            'music_file', 'music_transition', 'audio_narration_url',
            'is_ending', 'ending_type', 'is_revisit', 'choices'
        )

    def to_representation(self, instance):
        # Les choix déjà empruntés sont calculés ici, avant la sérialisation des
        # champs : ChoiceSerializer (imbriqué, donc même contexte) y lit son
        # `is_explored` sans requête supplémentaire.
        self.context['explored_choice_ids'] = _explored_choice_ids(
            self.context.get('request'), instance
        )
        return super().to_representation(instance)

    def get_is_revisit(self, obj):
        """True si le joueur est déjà passé par cette scène auparavant."""
        return bool(self.context.get('explored_choice_ids'))

    def get_image_url(self, obj):
        """Image uploadée (admin) en priorité, sinon fallback static/scenes/{scene_key}."""
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return _static_asset_url(request, 'scenes', obj.scene_key, _IMAGE_EXTS)

    def get_audio_narration_url(self, obj):
        """Narration uploadée (admin) en priorité, sinon fallback static/narrations/{scene_key}."""
        request = self.context.get('request')
        if obj.audio_narration:
            return request.build_absolute_uri(obj.audio_narration.url) if request else obj.audio_narration.url
        return _static_asset_url(request, 'narrations', obj.scene_key, _AUDIO_EXTS)


class StoryListSerializer(serializers.ModelSerializer):
    """Liste des histoires disponibles (vue résumée)."""
    cover_image_url = serializers.SerializerMethodField()
    starting_scene_key = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ('id', 'title', 'slug', 'description', 'cover_image_url', 'starting_scene_key')

    def get_cover_image_url(self, obj):
        request = self.context.get('request')
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None

    def get_starting_scene_key(self, obj):
        scene = obj.get_starting_scene()
        return scene.scene_key if scene else None


class StoryDetailSerializer(StoryListSerializer):
    """Détail d'une histoire avec la scène de départ complète."""
    starting_scene = serializers.SerializerMethodField()

    class Meta(StoryListSerializer.Meta):
        fields = StoryListSerializer.Meta.fields + ('starting_scene',)

    def get_starting_scene(self, obj):
        scene = obj.get_starting_scene()
        if scene:
            return SceneSerializer(scene, context=self.context).data
        return None
