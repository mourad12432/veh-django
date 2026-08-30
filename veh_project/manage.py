#!/usr/bin/env python
"""
Utilitaire de ligne de commande Django pour les tâches administratives.
Usage : python manage.py <commande>
"""

import os
import sys


def main():
    """Lance les tâches administratives."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Impossible d'importer Django. Avez-vous activé votre virtualenv "
            "et installé les dépendances avec 'pip install -r requirements.txt' ?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
