"""
Configuration de base Django — partagée entre développement et production.
VEH — Vous Êtes le Héro
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Racine du projet (veh_project/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Clé secrète Django
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

# Applications installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Packages tiers
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_extensions',

    # Applications VEH
    'apps.users',
    'apps.stories',
    'apps.sessions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Servir les fichiers statiques
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Validation des mots de passe desactivee : n'importe quel mot de passe est accepte.
AUTH_PASSWORD_VALIDATORS = []

# Internationalisation
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Fichiers statiques
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Fichiers media (images, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Modèle utilisateur personnalisé
AUTH_USER_MODEL = 'users.User'

# Clé primaire par défaut
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# URLs d'authentification
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Configuration Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}

# Configuration JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS pour l'application Flutter
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Clé API Gemini
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# ─────────────────────────────────────────────────────────────────────────────
#  Illustration automatique des scènes (apps.stories.services.image_service)
# ─────────────────────────────────────────────────────────────────────────────

# Génère l'image de fond dès qu'un auteur enregistre une scène dans l'admin.
# Mettre SCENE_IMAGE_AUTOGEN=0 dans .env pour ne garder que la génération
# manuelle (action de l'admin + commande generate_scene_images).
SCENE_IMAGE_AUTOGEN = os.environ.get('SCENE_IMAGE_AUTOGEN', '1') not in ('0', 'false', 'False')

# Backends d'image, en liste séparée par des virgules, essayés dans l'ordre.
#   pollinations = gratuit, sans clé, sans facturation
#   gemini       = meilleure qualité, exige la facturation activée
# Vide = les valeurs par défaut du service (pollinations d'abord).
SCENE_IMAGE_BACKEND = os.environ.get('SCENE_IMAGE_BACKEND') or ''
SCENE_IMAGE_POLLINATIONS_MODEL = os.environ.get('SCENE_IMAGE_POLLINATIONS_MODEL') or ''

# Modèles Gemini, en liste séparée par des virgules : ils sont essayés dans l'ordre
# jusqu'à ce que l'un réponde, car Google retire ses modèles sans préavis et
# les surcharge aux heures de pointe. Vide = les valeurs par défaut du service.
SCENE_IMAGE_PROMPT_MODEL = os.environ.get('SCENE_IMAGE_PROMPT_MODEL') or ''
SCENE_IMAGE_MODEL = os.environ.get('SCENE_IMAGE_MODEL') or ''
# Format du fond de scène
SCENE_IMAGE_ASPECT_RATIO = os.environ.get('SCENE_IMAGE_ASPECT_RATIO') or '16:9'

# Direction artistique commune à toutes les scènes : c'est elle qui rend les
# illustrations cohérentes entre elles. La modifier régénère toutes les images.
SCENE_IMAGE_STYLE = os.environ.get('SCENE_IMAGE_STYLE') or (
    "illustration numérique cinématographique, peinture digitale détaillée, "
    "éclairage dramatique, palette sombre et contrastée, ambiance de roman "
    "interactif, plan large, aucun texte ni logo dans l'image"
)
