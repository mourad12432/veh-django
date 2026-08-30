"""
WSGI config pour le projet VEH.
Expose la variable 'application' au niveau du module pour les serveurs WSGI.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

application = get_wsgi_application()
