"""
Management command : devserver

Le serveur de développement, précédé d'une bannière peu encourageante.

    python manage.py devserver
    python manage.py devserver 0.0.0.0:8000

Purement additif : la commande hérite de `runserver` et accepte donc les mêmes
arguments. `python manage.py runserver` continue de fonctionner à l'identique,
sans bannière.
"""

import os
import random
import unicodedata

from django.contrib.staticfiles.management.commands.runserver import (
    Command as RunserverCommand,
)


MESSAGES = [
    "Compilation en cours... comme ta motivation.",
    "0 erreur. Pour l'instant.",
    "Ce projet fonctionne. Personne ne sait pourquoi.",
    "Café requis avant tout commit.",
    "98 scènes, 3 histoires, et un seul développeur. Bon courage.",
]

# Largeur intérieure du cadre. Le titre est centré dessus : la bannière reste
# alignée même si on change le texte.
_WIDTH = 38
_TITLE = "⚠  MODE DÉVELOPPEUR ACTIVÉ  ⚠"

# Repli pour les consoles Windows en cp1252, qui ne savent pas encoder les
# filets doubles ni les accents : on garde la forme, on perd la décoration.
_ASCII = str.maketrans({
    "╔": "+", "╗": "+", "╚": "+", "╝": "+",
    "║": "|", "═": "=", "⚠": "!",
})


def build_banner(message):
    """Le cadre complet, message aléatoire inclus."""
    return (
        f"\n  ╔{'═' * _WIDTH}╗"
        f"\n  ║{_TITLE.center(_WIDTH)}║"
        f"\n  ╚{'═' * _WIDTH}╝"
        f"\n  {message}\n"
    )


def to_ascii(text):
    """Version sans filets ni accents, pour les consoles récalcitrantes."""
    text = text.translate(_ASCII)
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')


class Command(RunserverCommand):
    help = "Lance le serveur de développement, avec une bannière moqueuse."

    def handle(self, *args, **options):
        # Avec l'autoreloader, handle() tourne dans le processus parent puis dans
        # chaque processus rechargé. RUN_MAIN n'est posé que dans les seconds :
        # la bannière ne s'affiche donc qu'une fois, pas à chaque sauvegarde.
        if os.environ.get('RUN_MAIN') != 'true':
            self.print_banner()
        super().handle(*args, **options)

    def print_banner(self):
        banner = build_banner(random.choice(MESSAGES))
        try:
            self.stdout.write(banner)
        except UnicodeEncodeError:
            self.stdout.write(to_ascii(banner))
