"""
Management command : generate_scene_images

Illustre les scènes en masse — le même service que la génération automatique
du back-office et de l'interface Narrateur (services/image_service.py), mais
pour tout un scénario d'un coup.

Pour chaque scène :
    texte narratif ──► prompt visuel  (Gemini si une clé est configurée,
                                       sinon extraction locale du texte)
                   ──► image          (backend gratuit, ou Gemini)

L'image atterrit dans media/scenes/ et devient aussitôt le fond de scène du
web et du mobile. Les scènes qui ont déjà un visuel — uploadé à la main ou
posé dans static/scenes/ — ne sont jamais écrasées (sauf --force).

Aucune clé API n'est nécessaire : sans GEMINI_API_KEY, tout passe par le
chemin gratuit. Voir SCENE_IMAGE_BACKEND dans .env.example.

Exemples :
    python manage.py generate_scene_images
    python manage.py generate_scene_images --story les-fils-du-destin
    python manage.py generate_scene_images --scene prologue_matin --force
    python manage.py generate_scene_images --rewrite-prompt
    python manage.py generate_scene_images --style "aquarelle claire, traits doux"
"""

import time

from django.core.management.base import BaseCommand, CommandError

from apps.stories.models import Story, Scene
from apps.stories.services import image_service


class Command(BaseCommand):
    help = "Génère les images de fond des scènes (prompt visuel, puis image)."

    def add_arguments(self, parser):
        parser.add_argument('--story', type=str, default=None,
            help="Slug de l'histoire à traiter (par défaut : toutes les histoires).")
        parser.add_argument('--scene', type=str, default=None,
            help="scene_key d'une seule scène à (re)générer.")
        parser.add_argument('--force', action='store_true',
            help="Régénère même si la scène a déjà une image à jour.")
        parser.add_argument('--rewrite-prompt', action='store_true',
            help="Réécrit le prompt visuel même si la scène en a déjà un.")
        parser.add_argument('--style', type=str, default=None,
            help="Direction artistique pour cette exécution (défaut : SCENE_IMAGE_STYLE).")
        parser.add_argument('--delay', type=float, default=2.0,
            help="Pause en secondes entre deux scènes. Défaut : 2.")
        parser.add_argument('--dry-run', action='store_true',
            help="Liste les scènes qui seraient illustrées, sans aucun appel réseau.")

    def handle(self, *args, **opts):
        scenes = self._select_scenes(opts)
        if not scenes:
            self.stdout.write(self.style.WARNING("Aucune scène à traiter."))
            return

        if opts['dry_run']:
            self._dry_run(scenes, opts)
            return

        # Aucune clé n'est requise : sans GEMINI_API_KEY, le prompt est tiré du
        # texte et l'image vient du backend gratuit.
        client = image_service.get_client(required=False)
        self._generate(client, scenes, opts)

    def _select_scenes(self, opts):
        qs = Scene.objects.select_related('story').order_by('story_id', 'scene_key')
        if opts['story']:
            story = Story.objects.filter(slug=opts['story']).first()
            if not story:
                raise CommandError(f"Histoire introuvable : {opts['story']}")
            qs = qs.filter(story=story)
        if opts['scene']:
            qs = qs.filter(scene_key=opts['scene'])
        return list(qs)

    def _dry_run(self, scenes, opts):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Simulation (--dry-run) ===\n"))
        for scene in scenes:
            if opts['force'] or image_service.needs_illustration(scene):
                self.stdout.write(f"  à illustrer : {scene.scene_key}")
            else:
                self.stdout.write(f"  ignorée     : {scene.scene_key}")
        self.stdout.write("")

    def _generate(self, client, scenes, opts):
        total = len(scenes)
        generated = skipped = errors = 0

        backends = ', '.join(
            image_service.setting_list('SCENE_IMAGE_BACKEND',
                                       image_service.DEFAULT_IMAGE_BACKENDS))
        etape1 = 'Gemini' if client else 'extraction locale (sans clé)'
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n=== Illustration de {total} scène(s) ===\n"
        ))
        self.stdout.write(f"  prompts : {etape1}\n  images  : {backends}\n")

        for i, scene in enumerate(scenes, start=1):
            key = scene.scene_key

            if not opts['force'] and not image_service.needs_illustration(scene):
                self.stdout.write(f"  [{i}/{total}] {key} — déjà à jour (--force pour refaire).")
                skipped += 1
                continue

            if not (scene.narrative or '').strip():
                self.stdout.write(self.style.WARNING(f"  [{i}/{total}] {key} — texte vide, ignorée."))
                skipped += 1
                continue

            self.stdout.write(f"  [{i}/{total}] {key} — génération…", ending=' ')
            self.stdout.flush()

            try:
                _, backend = image_service.illustrate_scene(
                    scene,
                    client=client,
                    force=opts['force'],
                    rewrite_prompt=opts['rewrite_prompt'],
                    style=opts['style'],
                )
                size_kb = scene.image.size // 1024
                self.stdout.write(self.style.SUCCESS(f"OK ({size_kb} Ko, {backend})"))
                generated += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"ERREUR : {e}"))
                errors += 1

            if i < total:
                time.sleep(opts['delay'])

        self.stdout.write(self.style.MIGRATE_HEADING("\n──────── Terminé ────────"))
        self.stdout.write(self.style.SUCCESS(f"  Générées : {generated}"))
        self.stdout.write(f"  Ignorées : {skipped}")
        if errors:
            self.stdout.write(self.style.ERROR(f"  Erreurs  : {errors}"))
        self.stdout.write("\n  Images enregistrées dans media/scenes/ — visibles aussitôt dans le jeu.\n")
