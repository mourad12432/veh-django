"""
Management command : generate_narrations

Génère automatiquement les pistes audio de narration pour toutes les scènes
d'une (ou toutes les) histoire, via l'API Gemini TTS — la même IA vocale que
Google AI Studio, mais en un seul appel par scène, sans copier/coller manuel.

Les fichiers sont enregistrés dans static/narrations/{scene_key}.wav
(exactement là où le lecteur du jeu les cherche).

Prérequis :
    - Variable d'environnement GEMINI_API_KEY (déjà utilisée par le jeu)
    - pip install google-genai

Exemples :
    python manage.py generate_narrations
    python manage.py generate_narrations --story les-fils-du-destin
    python manage.py generate_narrations --scene prologue_matin
    python manage.py generate_narrations --force
    python manage.py generate_narrations --voice Charon --style "d'une voix grave et dramatique"
"""

import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.stories.models import Story, Scene
from apps.stories.services import tts_service


class Command(BaseCommand):
    help = "Génère les narrations audio (WAV) de toutes les scènes via Gemini TTS."

    def add_arguments(self, parser):
        parser.add_argument('--story', type=str, default=None,
            help="Slug de l'histoire à traiter (par défaut : toutes les histoires).")
        parser.add_argument('--scene', type=str, default=None,
            help="scene_key d'une seule scène à (re)générer (pour tester une voix).")
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
        try:
            client = tts_service.get_client()
        except tts_service.TTSError as e:
            raise CommandError(str(e))

        out_dir = _narrations_dir()
        out_dir.mkdir(parents=True, exist_ok=True)

        scenes = self._select_scenes(opts)
        if not scenes:
            self.stdout.write(self.style.WARNING("Aucune scène à traiter."))
            return

        generate_narrations_for(self, client, scenes, out_dir, opts)

    def _select_scenes(self, opts):
        qs = Scene.objects.all().order_by('story_id', 'scene_key')
        if opts['story']:
            story = Story.objects.filter(slug=opts['story']).first()
            if not story:
                raise CommandError(f"Histoire introuvable : {opts['story']}")
            qs = qs.filter(story=story)
        if opts['scene']:
            qs = qs.filter(scene_key=opts['scene'])
        return list(qs)


# ─────────────────────────────────────────────────────────────────────────────
#  Fonctions partagées (réutilisées par generate_narrations_demo)
# ─────────────────────────────────────────────────────────────────────────────

def _narrations_dir() -> Path:
    """Localise static/narrations/ de façon robuste."""
    for d in getattr(settings, 'STATICFILES_DIRS', []):
        if Path(d).exists():
            return Path(d) / 'narrations'
    return Path(settings.BASE_DIR) / 'static' / 'narrations'


def generate_narrations_for(command, client, scenes, out_dir, opts):
    """
    Génère les narrations pour une liste ordonnée de scènes.
    `command` sert uniquement à écrire dans stdout avec les styles Django.
    """
    total     = len(scenes)
    generated = skipped = errors = 0

    command.stdout.write(command.style.MIGRATE_HEADING(
        f"\n=== Génération de {total} narration(s) — "
        f"voix « {opts['voice']} », modèle « {opts['model']} » ===\n"
    ))

    for i, scene in enumerate(scenes, start=1):
        key = scene.scene_key
        out_path = out_dir / f"{key}.wav"

        if scene.audio_narration:
            command.stdout.write(f"  [{i}/{total}] {key} — narration uploadée, ignorée.")
            skipped += 1
            continue

        if out_path.exists() and not opts['force']:
            command.stdout.write(f"  [{i}/{total}] {key} — déjà généré (--force pour refaire).")
            skipped += 1
            continue

        text = tts_service.build_prompt(scene.narrative, opts['style'])
        if not text.strip():
            command.stdout.write(command.style.WARNING(f"  [{i}/{total}] {key} — texte vide, ignoré."))
            skipped += 1
            continue

        command.stdout.write(f"  [{i}/{total}] {key} — génération…", ending=' ')
        command.stdout.flush()

        try:
            pcm, rate = tts_service.synthesize(client, text, opts['voice'], opts['model'])
            tts_service.write_wav(out_path, pcm, rate)
            size_kb = out_path.stat().st_size // 1024
            command.stdout.write(command.style.SUCCESS(f"OK ({size_kb} Ko)"))
            generated += 1
        except Exception as e:
            command.stdout.write(command.style.ERROR(f"ERREUR : {e}"))
            errors += 1

        if i < total:
            time.sleep(opts['delay'])

    command.stdout.write(command.style.MIGRATE_HEADING("\n──────── Terminé ────────"))
    command.stdout.write(command.style.SUCCESS(f"  Générées : {generated}"))
    command.stdout.write(f"  Ignorées : {skipped}")
    if errors:
        command.stdout.write(command.style.ERROR(f"  Erreurs  : {errors}"))
    command.stdout.write(
        f"\n  Fichiers dans : {out_dir}\n"
        "  En production, pensez à lancer : python manage.py collectstatic\n"
    )
    return generated, skipped, errors
