"""
Management command : seed_chaperon_rouge
Peuple la base de données avec "Le Chaperon Rouge" — histoire COURTE (7 scènes)
et ramifiée, dans le même principe que "Les Fils du Destin" : chaque choix mène
à des événements différents et peut changer le destin de l'héroïne.

Structure : 4 scènes narratives + 3 fins (heureuse / tragique / amère).

Usage : python manage.py seed_chaperon_rouge [--reset]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.stories.models import Story, Scene, Choice

SLUG = 'le-chaperon-rouge'


class Command(BaseCommand):
    help = 'Crée l\'histoire ramifiée "Le Chaperon Rouge" (7 scènes)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime l\'histoire existante avant de la recréer'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '[VEH] Creation de l\'histoire "Le Chaperon Rouge" (7 scenes)...'
        ))

        if options['reset']:
            Story.objects.filter(slug=SLUG).delete()
            self.stdout.write(self.style.WARNING('  -> Histoire existante supprimee.'))

        if Story.objects.filter(slug=SLUG).exists():
            self.stdout.write(self.style.WARNING(
                '  L\'histoire existe deja. Utilisez --reset pour la recreer.'
            ))
            return

        # ─────────────────────────────────────────────────────
        # 1. Histoire
        # ─────────────────────────────────────────────────────
        story = Story.objects.create(
            title='Le Chaperon Rouge',
            slug=SLUG,
            description=(
                'Vous êtes le Chaperon Rouge. Un panier au bras, vous traversez '
                'la forêt pour porter une galette à Mère-Grand malade. Mais le loup '
                'rôde entre les arbres. Chaque sentier, chaque parole, chaque choix '
                'décide qui survivra à la tombée du soir.'
            ),
            is_published=True,
        )
        self.stdout.write(f'  [OK] Histoire creee : {story.title}')

        # ─────────────────────────────────────────────────────
        # 2. Scènes (7)
        # ─────────────────────────────────────────────────────
        scenes_data = {
            'depart_maison': {
                'narrative': (
                    "Le soleil filtre à travers les carreaux de la chaumière. Maman "
                    "glisse une galette encore tiède et un petit pot de beurre dans "
                    "votre panier, puis noue les rubans de votre capuche écarlate.\n\n"
                    "« Va droit chez Mère-Grand, mon Chaperon. Ne quitte pas le sentier, "
                    "et ne parle à personne dans les bois. »\n\n"
                    "La forêt vous attend, immense et bruissante. Trois chemins s'ouvrent "
                    "à la lisière. Lequel prenez-vous ?"
                ),
                'music_file': 'calm_ambient.mp3',
                'music_transition': 'fade',
                'is_starting_scene': True,
            },
            'rencontre_loup': {
                'narrative': (
                    "Vous suivez le large sentier. Les oiseaux chantent, la mousse est "
                    "douce sous vos pas. Puis une ombre élégante se dresse entre deux "
                    "troncs : un grand loup au pelage lustré vous salue d'une courbette "
                    "trop polie.\n\n"
                    "« Bonjour, charmant Chaperon. Où vont donc ces jolis rubans par un "
                    "si beau matin ? » Sa voix est un velours qui cache des crocs.\n\n"
                    "Un frisson vous parcourt. Que répondez-vous à la bête ?"
                ),
                'music_file': 'mysterious_wonder.mp3',
                'music_transition': 'fade',
            },
            'raccourci_bois': {
                'narrative': (
                    "Vous quittez le sentier et vous enfoncez dans les bois. Très vite, "
                    "les arbres se resserrent et la lumière faiblit. Une brindille craque "
                    "derrière vous. Puis une autre.\n\n"
                    "Quelque chose avance à votre rythme, invisible, patient. Entre les "
                    "fougères, deux yeux jaunes vous fixent une seconde avant de "
                    "disparaître.\n\n"
                    "Vous n'êtes plus seule. Le cottage de Mère-Grand est encore loin, "
                    "quelque part au-delà de ces ombres."
                ),
                'music_file': 'danger_stealth.mp3',
                'music_transition': 'instant',
            },
            'cottage': {
                'narrative': (
                    "Vous atteignez enfin le cottage de Mère-Grand. La porte est "
                    "entrouverte, grinçant dans le vent. À l'intérieur, une silhouette "
                    "trop grande repose sous le bonnet de dentelle.\n\n"
                    "« Approche, mon enfant... », souffle une voix étrangement rauque.\n\n"
                    "« Mère-Grand, comme vous avez de grands yeux ! » — « C'est pour "
                    "mieux te voir. » — « Comme vous avez de grandes dents ! » La chose "
                    "se redresse, gueule béante : « C'EST POUR MIEUX TE DÉVORER ! »\n\n"
                    "Le loup bondit. Cet instant décidera de tout."
                ),
                'music_file': 'dramatic_reveal.mp3',
                'music_transition': 'instant',
            },

            # ── FINS ─────────────────────────────────────────
            'fin_heureuse': {
                'narrative': (
                    "Vous criez de toutes vos forces en reculant vers la fenêtre. "
                    "Le bûcheron, qui abattait un chêne tout près, entend le vacarme "
                    "et défonce la porte, hache au poing.\n\n"
                    "L'acier fend l'air : le loup s'effondre. Du grand coffre à "
                    "couvertures surgit alors Mère-Grand, ligotée mais vivante, que la "
                    "bête n'avait pas eu le temps de dévorer.\n\n"
                    "Ce soir, autour de la galette partagée, on raconte déjà l'histoire "
                    "du Chaperon qui a su garder la tête froide. Vous avez été l'héroïne "
                    "que votre famille attendait."
                ),
                'music_file': 'triumphant_victory.mp3',
                'music_transition': 'fade',
                'is_ending': True,
                'ending_type': 'good',
            },
            'fin_tragique': {
                'narrative': (
                    "Vous avez hésité une seconde de trop. Les crocs se referment dans "
                    "un fracas terrible, et les ténèbres vous engloutissent.\n\n"
                    "Quand le bûcheron pousse enfin la porte, il ne reste qu'un bonnet "
                    "de dentelle et un panier renversé. La galette, intacte, gît dans "
                    "la poussière.\n\n"
                    "La forêt garde ses secrets — et ses drames. On dit qu'au crépuscule, "
                    "on entend encore pleurer un ruban écarlate entre les arbres."
                ),
                'music_file': 'horror_intense.mp3',
                'music_transition': 'fade',
                'is_ending': True,
                'ending_type': 'bad',
            },
            'fin_amere': {
                'narrative': (
                    "Vous jetez le pot de beurre à la gueule du loup et fuyez dans les "
                    "bois, le cœur en tempête. Les ronces déchirent votre cape, mais "
                    "vous échappez de justesse à ses crocs.\n\n"
                    "Vous survivez. Mais le loup, lui, s'évanouit dans l'ombre, bien "
                    "vivant. Et vous ignorez encore ce qu'il est advenu de Mère-Grand.\n\n"
                    "Cette nuit-là, vous dormez la porte barricadée, guettant chaque "
                    "craquement. L'histoire n'est pas finie — elle rôde toujours."
                ),
                'music_file': 'sad_melancholy.mp3',
                'music_transition': 'fade',
                'is_ending': True,
                'ending_type': 'neutral',
            },
        }

        scene_objects = {}
        for key, data in scenes_data.items():
            scene = Scene.objects.create(
                story=story,
                scene_key=key,
                narrative=data['narrative'],
                music_file=data['music_file'],
                music_transition=data['music_transition'],
                is_starting_scene=data.get('is_starting_scene', False),
                is_ending=data.get('is_ending', False),
                ending_type=data.get('ending_type', None),
            )
            scene_objects[key] = scene
            self.stdout.write(f'  [OK] Scene creee : {key}')

        # ─────────────────────────────────────────────────────
        # 3. Choix — (texte, scène_suivante, ordre)
        #    Chaque choix mène à un événement DIFFÉRENT.
        # ─────────────────────────────────────────────────────
        choices_data = [
            ('depart_maison', [
                ("Suivre sagement le sentier principal", 'rencontre_loup', 0),
                ("Couper par les bois sombres pour aller plus vite", 'raccourci_bois', 1),
                ("Vous hâter droit vers le cottage sans traîner", 'cottage', 2),
            ]),
            ('rencontre_loup', [
                ("Dire la vérité : Mère-Grand habite au bout du bois", 'cottage', 0),
                ("Mentir pour l'égarer vers le village", 'cottage', 1),
                ("Détaler sans un mot dans les fourrés", 'raccourci_bois', 2),
            ]),
            ('raccourci_bois', [
                ("Courir vers une lueur : la maison de Mère-Grand", 'cottage', 0),
                ("Vous cacher et épier le loup qui file vers le cottage", 'cottage', 1),
                ("Vous enfoncer plus profond, désorientée", 'fin_amere', 2),
            ]),
            ('cottage', [
                ("Crier fort en reculant vers la fenêtre", 'fin_heureuse', 0),
                ("Vous précipiter dans les bras de « Mère-Grand »", 'fin_tragique', 1),
                ("Lancer le pot de beurre et vous enfuir", 'fin_amere', 2),
            ]),
        ]

        total_choices = 0
        for scene_key, choices in choices_data:
            scene = scene_objects[scene_key]
            for text, next_key, order in choices:
                Choice.objects.create(
                    scene=scene,
                    text=text,
                    next_scene=scene_objects.get(next_key),
                    order=order,
                )
                total_choices += 1

        self.stdout.write(f'  [OK] {total_choices} choix crees')

        # ─────────────────────────────────────────────────────
        # 4. Résumé
        # ─────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('  [SUCCESS] "Le Chaperon Rouge" creee avec succes !'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'  Histoire : {story.title}')
        self.stdout.write(f'  Scenes   : {len(scene_objects)}')
        self.stdout.write(f'  Choix    : {total_choices}')
        self.stdout.write(f'  URL      : /play/{SLUG}/auto/')
        self.stdout.write('')
        self.stdout.write('  Lancez le serveur et jouez :')
        self.stdout.write(self.style.HTTP_INFO('  python manage.py runserver'))
