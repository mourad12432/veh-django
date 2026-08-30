"""
Modèles principaux du jeu narratif VEH :
- Story    : une histoire complète
- Scene    : une scène au sein d'une histoire
- Choice   : un choix proposé au joueur dans une scène
"""

from django.db import models
from django.utils.text import slugify


class Story(models.Model):
    """Une histoire jouable complète."""
    title = models.CharField(max_length=200, verbose_name='Titre')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Slug URL')
    description = models.TextField(verbose_name='Description')
    cover_image = models.ImageField(
        upload_to='covers/',
        blank=True,
        null=True,
        verbose_name='Image de couverture'
    )
    is_published = models.BooleanField(default=False, verbose_name='Publiée')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créée le')

    class Meta:
        verbose_name = 'Histoire'
        verbose_name_plural = 'Histoires'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-générer le slug depuis le titre si absent
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_starting_scene(self):
        """Retourne la scène de départ de cette histoire."""
        return self.scenes.filter(is_starting_scene=True).first()


class Scene(models.Model):
    """Une scène narrative dans une histoire."""

    # Pistes musicales disponibles (fichiers dans static/music/)
    MUSIC_CALM         = 'calm_ambient.mp3'
    MUSIC_TENSION      = 'tension_rising.mp3'
    MUSIC_HORROR       = 'horror_intense.mp3'
    MUSIC_COMBAT       = 'combat_action.mp3'
    MUSIC_SAD          = 'sad_melancholy.mp3'
    MUSIC_MYSTERIOUS   = 'mysterious_wonder.mp3'
    MUSIC_TRIUMPHANT   = 'triumphant_victory.mp3'
    MUSIC_DRAMATIC     = 'dramatic_reveal.mp3'
    MUSIC_ROMANTIC     = 'romantic_tender.mp3'
    MUSIC_STEALTH      = 'danger_stealth.mp3'
    MUSIC_CHOICES = [
        (MUSIC_CALM,       'Calme / Repos'),
        (MUSIC_TENSION,    'Tension / Suspense'),
        (MUSIC_HORROR,     'Horreur / Angoisse'),
        (MUSIC_COMBAT,     'Combat / Bagarre'),
        (MUSIC_SAD,        'Triste / Mélancolique'),
        (MUSIC_MYSTERIOUS, 'Mystère / Exploration'),
        (MUSIC_TRIUMPHANT, 'Triomphe / Victoire'),
        (MUSIC_DRAMATIC,   'Dramatique / Révélation'),
        (MUSIC_ROMANTIC,   'Romantique / Tendresse'),
        (MUSIC_STEALTH,    'Danger / Furtif'),
    ]

    # Choix de transition musicale
    TRANSITION_FADE = 'fade'
    TRANSITION_INSTANT = 'instant'
    TRANSITION_CONTINUOUS = 'continuous'
    TRANSITION_CHOICES = [
        (TRANSITION_FADE, 'Fondu (fade)'),
        (TRANSITION_INSTANT, 'Instantanée (choc dramatique)'),
        (TRANSITION_CONTINUOUS, 'Continue (même ambiance)'),
    ]

    # Type de fin
    ENDING_GOOD = 'good'
    ENDING_BAD = 'bad'
    ENDING_NEUTRAL = 'neutral'
    ENDING_TYPE_CHOICES = [
        (ENDING_GOOD, 'Bonne fin'),
        (ENDING_BAD, 'Mauvaise fin'),
        (ENDING_NEUTRAL, 'Fin neutre'),
    ]

    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name='scenes',
        verbose_name='Histoire'
    )
    scene_key = models.CharField(
        max_length=100,
        verbose_name='Clé de scène',
        help_text='Identifiant unique dans l\'histoire, ex: scene_01, scene_kidnap'
    )
    narrative = models.TextField(verbose_name='Texte narratif')
    image = models.ImageField(
        upload_to='scenes/',
        blank=True,
        null=True,
        verbose_name='Image d\'ambiance'
    )
    music_file = models.CharField(
        max_length=100,
        choices=MUSIC_CHOICES,
        default=MUSIC_CALM,
        verbose_name='Ambiance musicale',
        help_text='Piste de fond jouée pendant cette scène (fichiers dans static/music/)'
    )
    audio_narration = models.FileField(
        upload_to='narrations/',
        blank=True,
        null=True,
        verbose_name='Narration audio',
        help_text='Fichier audio lu par le narrateur — mp3/ogg/wav, uploadé via l\'admin'
    )
    music_transition = models.CharField(
        max_length=20,
        choices=TRANSITION_CHOICES,
        default=TRANSITION_FADE,
        verbose_name='Transition musicale'
    )
    is_starting_scene = models.BooleanField(
        default=False,
        verbose_name='Scène de départ'
    )
    is_ending = models.BooleanField(
        default=False,
        verbose_name='Scène de fin'
    )
    ending_type = models.CharField(
        max_length=10,
        choices=ENDING_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name='Type de fin'
    )

    class Meta:
        verbose_name = 'Scène'
        verbose_name_plural = 'Scènes'
        # Une clé de scène doit être unique par histoire
        unique_together = [('story', 'scene_key')]

    def __str__(self):
        return f"{self.story.title} — {self.scene_key}"


class Choice(models.Model):
    """Un choix proposé au joueur dans une scène."""
    scene = models.ForeignKey(
        Scene,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name='Scène'
    )
    text = models.CharField(max_length=300, verbose_name='Texte du choix')
    next_scene = models.ForeignKey(
        Scene,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_choices',
        verbose_name='Scène suivante'
    )
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Ordre')

    class Meta:
        verbose_name = 'Choix'
        verbose_name_plural = 'Choix'
        ordering = ['order']

    def __str__(self):
        return f"{self.scene.scene_key} → {self.text[:50]}"
