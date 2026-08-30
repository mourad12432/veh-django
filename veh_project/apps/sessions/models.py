"""
Modèles de sauvegarde de la progression du joueur.
GameSession est partagée entre web et mobile (Flutter) via la même DB.
"""

import uuid
from django.db import models
from django.conf import settings


class GameSession(models.Model):
    """
    Session de jeu d'un utilisateur sur une histoire.
    Une seule session par (utilisateur, histoire) — partagée web/mobile.
    """
    PLATFORM_WEB = 'web'
    PLATFORM_MOBILE = 'mobile'
    PLATFORM_CHOICES = [
        (PLATFORM_WEB, 'Web'),
        (PLATFORM_MOBILE, 'Mobile (Flutter)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_sessions',
        verbose_name='Joueur'
    )
    story = models.ForeignKey(
        'stories.Story',
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='Histoire'
    )
    current_scene = models.ForeignKey(
        'stories.Scene',
        on_delete=models.SET_NULL,
        null=True,
        related_name='active_sessions',
        verbose_name='Scène actuelle'
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Démarré le')
    last_played = models.DateTimeField(auto_now=True, verbose_name='Dernière activité')
    is_completed = models.BooleanField(default=False, verbose_name='Terminée')
    platform = models.CharField(
        max_length=10,
        choices=PLATFORM_CHOICES,
        default=PLATFORM_WEB,
        verbose_name='Plateforme'
    )

    class Meta:
        verbose_name = 'Session de jeu'
        verbose_name_plural = 'Sessions de jeu'
        # Une seule session par joueur par histoire (synchronisation web/mobile)
        unique_together = [('user', 'story')]
        ordering = ['-last_played']

    def __str__(self):
        return f"{self.user.username} — {self.story.title} ({self.platform})"

    @property
    def progress_percentage(self):
        """
        Calcule approximativement la progression (scènes visitées / total).
        Retourne un entier entre 0 et 100.
        """
        total = self.story.scenes.count()
        visited = self.history.values('scene').distinct().count()
        if total == 0:
            return 0
        return min(100, int((visited / total) * 100))


class SessionHistory(models.Model):
    """
    Historique de toutes les scènes visitées et choix effectués
    dans une session de jeu.
    """
    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Session'
    )
    scene = models.ForeignKey(
        'stories.Scene',
        on_delete=models.CASCADE,
        related_name='visits',
        verbose_name='Scène visitée'
    )
    choice_made = models.ForeignKey(
        'stories.Choice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_entries',
        verbose_name='Choix effectué'
    )
    visited_at = models.DateTimeField(auto_now_add=True, verbose_name='Visité le')

    class Meta:
        verbose_name = 'Historique de scène'
        verbose_name_plural = 'Historiques de scènes'
        ordering = ['visited_at']

    def __str__(self):
        choice_text = self.choice_made.text[:30] if self.choice_made else 'Fin'
        return f"{self.session.user.username} | {self.scene.scene_key} → {choice_text}"
