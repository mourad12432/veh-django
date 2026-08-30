"""
URLs principales du projet VEH.
- /          → application web (Django Templates)
- /api/      → REST API pour Flutter
- /admin/    → interface d'administration Django
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Interface d'administration Django
    path('admin/', admin.site.urls),

    # Application web — utilisateurs (login, register, profil)
    path('users/', include('apps.users.urls')),

    # Application web — jeu (accueil, jeu, endings)
    path('', include('apps.stories.urls_web')),
    path('play/', include('apps.sessions.urls_web')),

    # REST API — authentification JWT
    path('api/auth/', include('apps.users.urls_api')),

    # REST API — histoires et jeu
    path('api/', include('apps.stories.urls_api')),

    # REST API — sessions de jeu
    path('api/', include('apps.sessions.urls_api')),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
