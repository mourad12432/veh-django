"""
Enregistrement du modèle utilisateur dans l'admin Django.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin personnalisé avec les champs VEH."""
    list_display = ('username', 'email', 'first_name', 'is_staff', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Profil VEH', {'fields': ('avatar', 'bio')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profil VEH', {'fields': ('email', 'avatar', 'bio')}),
    )
