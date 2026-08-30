"""
Interface d'administration Django pour les histoires, scènes et choix.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Story, Scene, Choice


class ChoiceInline(admin.TabularInline):
    model = Choice
    fk_name = 'scene'
    extra = 3
    fields = ('text', 'next_scene', 'order')
    ordering = ('order',)


class SceneInline(admin.StackedInline):
    model = Scene
    extra = 1
    fields = (
        'scene_key', 'narrative', 'image',
        'music_file', 'music_transition', 'audio_narration',
        'is_starting_scene', 'is_ending', 'ending_type'
    )
    show_change_link = True


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'created_at')
    list_filter = ('is_published',)
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [SceneInline]
    list_editable = ('is_published',)
    date_hierarchy = 'created_at'


@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = (
        'scene_key', 'story', 'image_preview',
        'is_starting_scene', 'is_ending', 'ending_type',
        'music_file', 'music_transition'
    )
    list_filter = ('story', 'is_ending', 'is_starting_scene', 'music_file', 'music_transition')
    search_fields = ('scene_key', 'narrative')
    inlines = [ChoiceInline]
    readonly_fields = ('image_preview',)
    fieldsets = (
        ('Identification', {
            'fields': ('story', 'scene_key')
        }),
        ('Contenu narratif', {
            'fields': ('narrative',)
        }),
        ('Image de fond', {
            'fields': ('image', 'image_preview'),
            'description': (
                'Uploadez une image ici ou placez un fichier '
                '<code>static/scenes/{scene_key}.jpg</code> pour un chargement automatique.'
            ),
        }),
        ('Musique de fond', {
            'fields': ('music_file', 'music_transition'),
            'description': (
                'Choisissez l\'ambiance musicale. '
                'Placez vos fichiers MP3 dans <code>static/music/</code>.'
            ),
        }),
        ('Narration audio', {
            'fields': ('audio_narration',),
            'description': (
                'Uploadez un fichier MP3/OGG/WAV ou placez '
                '<code>static/narrations/{scene_key}.mp3</code>.'
            ),
        }),
        ('Statut', {
            'fields': ('is_starting_scene', 'is_ending', 'ending_type')
        }),
    )

    @admin.display(description='Aperçu image')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:80px;max-width:120px;'
                'object-fit:cover;border-radius:4px;" />',
                obj.image.url
            )
        return '—'


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'scene', 'next_scene', 'order')
    list_filter = ('scene__story',)
    search_fields = ('text',)
    ordering = ('scene', 'order')
