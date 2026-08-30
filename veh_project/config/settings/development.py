"""
Configuration Django pour le développement local.
Utilise SQLite, DEBUG=True, emails en console.
"""

from .base import *

DEBUG = True

# 10.0.2.2 = alias de l'hôte pour l'émulateur Android (app Flutter).
# Pour un téléphone physique, ajoutez ici l'IP LAN de votre PC (ex: '192.168.1.20').
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '10.0.2.2', '192.168.1.13']

# Base de données SQLite pour le développement
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Afficher les emails dans la console pendant le développement
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Permettre tous les CORS en dev
CORS_ALLOW_ALL_ORIGINS = True

# Barre de débogage (optionnel, à activer si django-debug-toolbar installé)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']
