"""
Configuration Docker — autonome pour « faire tourner » le projet facilement.

Basée sur le développement (SQLite, DEBUG=True, pas de redirection HTTPS),
mais la base de données et les médias sont stockés dans un volume persistant
(/data) et ALLOWED_HOSTS est configurable par variable d'environnement.
"""

import os
from .development import *  # noqa: F401,F403

DATA_DIR = os.environ.get('VEH_DATA_DIR', '/data')

# Base SQLite persistée hors du code (volume Docker) → survit aux redémarrages.
DATABASES['default']['NAME'] = os.path.join(DATA_DIR, 'db.sqlite3')  # noqa: F405

# Médias (uploads admin, cache de narration Gemini) persistés eux aussi.
MEDIA_ROOT = os.path.join(DATA_DIR, 'media')

# Hôtes autorisés. Ajoutez l'IP LAN de votre PC pour un accès depuis un mobile.
ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,10.0.2.2'
).split(',')
