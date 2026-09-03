"""
Interface d'administration Django pour les histoires, scènes et choix.

L'illustration des scènes est automatique : à l'enregistrement, le texte
narratif devient un prompt visuel puis une image, qui atterrit dans
`Scene.image` et devient le fond de scène du jeu (web et mobile).
Voir illustration.py (le déclencheur, partagé avec l'interface Narrateur)
et services/image_service.py (la génération elle-même).
"""

from django.contrib import admin, messages
from django.utils.html import format_html
from .illustration import autogenerate_image, MAX_PAR_ENREGISTREMENT
from .models import Story, Scene, Choice
from .services import image_service


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
        'scene_key', 'narrative', 'image', 'image_auto_generate', 'image_prompt',
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

    def save_formset(self, request, form, formset, change):
        """Illustre les scènes créées ou modifiées depuis la fiche Histoire."""
        instances = formset.save()
        counter = [0]
        for obj in instances:
            if isinstance(obj, Scene):
                autogenerate_image(request, obj, counter)


@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = (
        'scene_key', 'story', 'image_preview',
        'is_starting_scene', 'is_ending', 'ending_type',
        'music_file', 'music_transition'
    )
    list_filter = (
        'story', 'is_ending', 'is_starting_scene',
        'image_is_generated', 'image_auto_generate',
        'music_file', 'music_transition',
    )
    search_fields = ('scene_key', 'narrative')
    inlines = [ChoiceInline]
    readonly_fields = ('image_preview',)
    actions = ('action_illustrate', 'action_rewrite_and_illustrate')
    fieldsets = (
        ('Identification', {
            'fields': ('story', 'scene_key')
        }),
        ('Contenu narratif', {
            'fields': ('narrative',)
        }),
        ('Image de fond', {
            'fields': ('image_auto_generate', 'image_prompt', 'image', 'image_preview'),
            'description': (
                'À l\'enregistrement, le texte narratif devient un prompt visuel, '
                'puis une image qui sert de fond à la scène (web et mobile).<br>'
                'Videz le prompt pour le faire réécrire, modifiez-le pour refaire '
                'l\'image, ou uploadez la vôtre — un visuel envoyé à la main n\'est '
                'jamais écrasé par l\'IA.'
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        autogenerate_image(request, obj)

    @admin.display(description='Aperçu image')
    def image_preview(self, obj):
        if not obj.image:
            return '—'
        badge = ' 🤖 IA' if obj.image_is_generated else ''
        return format_html(
            '<img src="{}" style="max-height:80px;max-width:120px;'
            'object-fit:cover;border-radius:4px;" /><br><small>{}</small>',
            obj.image.url, badge
        )

    # ── Actions groupées ────────────────────────────────────────────────────

    def _run_illustration(self, request, queryset, rewrite_prompt):
        # Sans clé Gemini, client vaut None : le pipeline bascule tout seul sur
        # le prompt local et le backend d'image gratuit.
        client = image_service.get_client(required=False)

        done = failed = 0
        for scene in queryset.select_related('story'):
            try:
                image_service.illustrate_scene(
                    scene, client=client, force=True, rewrite_prompt=rewrite_prompt
                )
                done += 1
            except Exception as e:
                failed += 1
                self.message_user(
                    request, f"« {scene.scene_key} » : {e}", level=messages.WARNING
                )

        if done:
            self.message_user(
                request, f"{done} image(s) générée(s).", level=messages.SUCCESS
            )
        if failed:
            self.message_user(
                request, f"{failed} scène(s) en échec.", level=messages.ERROR
            )

    @admin.action(description="Illustrer avec l'IA (garde le prompt existant)")
    def action_illustrate(self, request, queryset):
        self._run_illustration(request, queryset, rewrite_prompt=False)

    @admin.action(description="Réécrire le prompt visuel puis illustrer")
    def action_rewrite_and_illustrate(self, request, queryset):
        self._run_illustration(request, queryset, rewrite_prompt=True)


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'scene', 'next_scene', 'order')
    list_filter = ('scene__story',)
    search_fields = ('text',)
    ordering = ('scene', 'order')
