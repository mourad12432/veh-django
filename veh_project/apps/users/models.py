"""
Modèle utilisateur étendu pour VEH.
Hérite de AbstractUser pour conserver toute la logique d'auth Django.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Utilisateur VEH — étend le modèle Django de base.
    Ajoute avatar, bio et date de création.
    """
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Avatar'
    )
    bio = models.TextField(
        blank=True,
        default='',
        verbose_name='Biographie',
        max_length=500
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date d\'inscription'
    )

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        """Retourne le prénom si disponible, sinon le nom d'utilisateur."""
        return self.first_name or self.username
