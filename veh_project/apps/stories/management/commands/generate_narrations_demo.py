"""
Management command : generate_narrations_demo

Version « démonstration » de generate_narrations.
Au lieu de fabriquer les narrations de TOUTES les scènes (91 pour Les Fils du
Destin), cette commande suit un seul parcours linéaire : à chaque scène, elle
prend automatiquement le PREMIER choix (celui d'ordre le plus bas), depuis la
scène de départ jusqu'à une fin. Elle ne génère que les narrations de ce chemin.

Idéal pour préparer rapidement une démo jouable de bout en bout, sans dépenser
d'appels API sur les branches non montrées.

Exemples :
    # Afficher le chemin sans rien générer (aperçu)
    python manage.py generate_narrations_demo --story les-fils-du-destin --dry-run

    # Générer les narrations du chemin de démo
    python manage.py generate_narrations_demo --story les-fils-du-destin

    # Limiter à 8 scènes et diriger le ton de la voix
    python manage.py generate_narrations_demo --story les-fils-du-destin --max 8 \
        --style "d'une voix grave et dramatique"
"""

from django.core.management.base import BaseCommand, CommandError

from apps.stories.models import Story
from apps.stories.services import tts_service
from apps.stories.management.commands.generate_narrations import (
    _narrations_dir,
    generate_narrations_for,
)


class Command(BaseCommand):
    help = ("Génère les narrations du seul chemin de démonstration "
            "(premier choix à chaque scène).")

    def add_arguments(self, parser):
        parser.add_argument('--story', type=str, default=None,
            help="Slug de l'histoire. Par défaut : la seule histoire publiée, sinon obligatoire.")
        parser.add_argument('--dry-run', action='store_true',
            help="Affiche le chemin des premiers choix sans générer d'audio.")
        parser.add_argument('--max', type=int, default=0,
            help="Nombre maximum de scènes à parcourir (0 = illimité).")
        parser.add_argument('--force', action='store_true',
            help="Regénère même si le fichier .wav existe déjà.")
        parser.add_argument('--voice', type=str, default=tts_service.DEFAULT_VOICE,
            help=f"Nom de la voix Gemini (défaut : {tts_service.DEFAULT_VOICE}).")
        parser.add_argument('--model', type=str, default=tts_service.DEFAULT_MODEL,
            help=f"Modèle TTS Gemini (défaut : {tts_service.DEFAULT_MODEL}).")
        parser.add_argument('--style', type=str, default='',
            help="Consigne de style ajoutée avant le texte, ex: \"d'une voix grave\".")
        parser.add_argument('--delay', type=float, default=2.0,
            help="Pause en secondes entre deux appels API. Défaut : 2.")

    def handle(self, *args, **opts):
        story = self._resolve_story(opts['story'])

        # Construire le chemin des premiers choix
        path = self._first_choice_path(story, opts['max'])
        if not path:
            raise CommandError(
                f"Impossible de construire un chemin : « {story.title} » "
                "n'a pas de scène de départ."
            )

        # Aperçu du parcours
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n=== Chemin de démonstration — {story.title} ({len(path)} scènes) ===\n"
        ))
        for i, (scene, choice_text) in enumerate(path, start=1):
            arrow = f"     -> 1er choix : « {choice_text} »" if choice_text else "     -> (fin)"
            marker = ' [FIN]' if scene.is_ending else ''
            self.stdout.write(f"  {i:>2}. {scene.scene_key}{marker}")
            self.stdout.write(self.style.HTTP_INFO(arrow))

        if opts['dry_run']:
            self.stdout.write(self.style.WARNING(
                "\n(--dry-run) Aucun audio généré. "
                "Relancez sans --dry-run pour produire les narrations.\n"
            ))
            return

        # Génération (réutilise exactement la logique de generate_narrations)
        try:
            client = tts_service.get_client()
        except tts_service.TTSError as e:
            raise CommandError(str(e))

        out_dir = _narrations_dir()
        out_dir.mkdir(parents=True, exist_ok=True)

        scenes = [scene for scene, _ in path]
        generate_narrations_for(self, client, scenes, out_dir, opts)

    # ------------------------------------------------------------------ #

    def _resolve_story(self, slug):
        if slug:
            story = Story.objects.filter(slug=slug).first()
            if not story:
                raise CommandError(f"Histoire introuvable : {slug}")
            return story
        published = Story.objects.filter(is_published=True)
        if published.count() == 1:
            return published.first()
        raise CommandError(
            "Plusieurs histoires (ou aucune) publiées : précisez --story <slug>."
        )

    def _first_choice_path(self, story, max_scenes=0):
        """
        Suit le premier choix (ordre le plus bas) de scène en scène.
        Retourne une liste de tuples (scene, texte_du_premier_choix|None).
        S'arrête sur une fin, une impasse, une boucle, ou après max_scenes.
        """
        scene = story.get_starting_scene()
        path = []
        visited = set()

        while scene and scene.scene_key not in visited:
            visited.add(scene.scene_key)

            if scene.is_ending:
                path.append((scene, None))
                break

            first_choice = scene.choices.order_by('order').first()
            if not first_choice or not first_choice.next_scene:
                # Impasse : scène sans choix menant ailleurs
                path.append((scene, first_choice.text if first_choice else None))
                break

            path.append((scene, first_choice.text))
            scene = first_choice.next_scene

            if max_scenes and len(path) >= max_scenes:
                break

        return path
