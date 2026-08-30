"""
Management command : seed_demo
Peuple la base de données avec l'histoire de démonstration "La Nuit du Kidnapping".

Usage : python manage.py seed_demo
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.stories.models import Story, Scene, Choice


class Command(BaseCommand):
    help = 'Crée l\'histoire de démonstration "La Nuit du Kidnapping"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime l\'histoire existante avant de la recréer'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('[VEH] Creation de l\'histoire de demonstration...'))

        # Supprimer si --reset demandé
        if options['reset']:
            Story.objects.filter(slug='la-nuit-du-kidnapping').delete()
            self.stdout.write(self.style.WARNING('  ↳ Histoire existante supprimée.'))

        # Vérifier si l'histoire existe déjà
        if Story.objects.filter(slug='la-nuit-du-kidnapping').exists():
            self.stdout.write(self.style.WARNING(
                '  L\'histoire existe déjà. Utilisez --reset pour la recréer.'
            ))
            return

        # ─────────────────────────────────────────────────────
        # 1. Créer l'histoire
        # ─────────────────────────────────────────────────────
        story = Story.objects.create(
            title='La Nuit du Kidnapping',
            slug='la-nuit-du-kidnapping',
            description=(
                'Une nuit ordinaire bascule dans le cauchemar. '
                'Votre frère a disparu. Chaque seconde compte. '
                'Chaque choix peut tout changer. '
                'Serez-vous à la hauteur ?'
            ),
            is_published=True,
        )
        self.stdout.write(f'  [OK] Histoire creee : {story.title}')

        # ─────────────────────────────────────────────────────
        # 2. Créer les scènes
        # ─────────────────────────────────────────────────────
        scenes_data = {
            'scene_01': {
                'narrative': (
                    'Il est 3h du matin. Vous êtes réveillé par un bruit sourd en bas. '
                    'La chambre de votre frère est silencieuse — trop silencieuse. '
                    'Votre cœur s\'emballe. Par la fenêtre, vous apercevez une silhouette '
                    'qui se faufile dans l\'obscurité du jardin. '
                    'Vous devez agir, et vite.'
                ),
                'music_file': 'calm_ambient.mp3',
                'music_transition': 'fade',
                'is_starting_scene': True,
            },
            'scene_corridor': {
                'narrative': (
                    'Vous vous précipitez dans le couloir sombre. '
                    'Les lattes du plancher grincent sous vos pieds. '
                    'Une ombre passe devant la fenêtre du couloir — quelqu\'un est encore là. '
                    'Votre gorge se serre. Le temps joue contre vous.'
                ),
                'music_file': 'tension_rising.mp3',
                'music_transition': 'instant',
            },
            'scene_backyard': {
                'narrative': (
                    'Vous sortez par la porte de derrière. '
                    'L\'air nocturne est glacial. Le jardin est plongé dans les ténèbres. '
                    'Au fond, une lumière de poche balaye frénétiquement l\'espace. '
                    'Deux hommes — ils transportent quelque chose. '
                    'Quelqu\'un... votre frère.'
                ),
                'music_file': 'tension_rising.mp3',
                'music_transition': 'fade',
            },
            'scene_window': {
                'narrative': (
                    'Depuis la fenêtre de l\'étage, vous observez la scène en contrebas. '
                    'Un van blanc est garé dans la ruelle. '
                    'Deux inconnus en tenue sombre poussent violemment votre frère à l\'intérieur. '
                    'La plaque d\'immatriculation s\'éclaire brièvement sous un lampadaire. '
                    'Vous avez quelques secondes pour réagir.'
                ),
                'music_file': 'tension_rising.mp3',
                'music_transition': 'fade',
            },
            'scene_police': {
                'narrative': (
                    'Vous composez le 17. La sonnerie. Une autre. Enfin une voix. '
                    '"Police secours, j\'écoute." '
                    'Votre voix tremble en racontant ce que vous avez vu. '
                    'L\'opératrice reste calme mais vous sentez l\'urgence dans ses questions. '
                    '"Une unité est en route. Restez où vous êtes." '
                    'Mais le van est peut-être déjà loin...'
                ),
                'music_file': 'tension_rising.mp3',
                'music_transition': 'continuous',
            },
            'scene_kidnap': {
                'narrative': (
                    'BANG — la porte d\'entrée explose sous un coup de pied brutal. '
                    'Deux hommes masqués surgissent dans le couloir. '
                    'En un instant, ils empoignent votre frère qui dormait sur le canapé. '
                    'Il hurle votre prénom. '
                    'Paralysé par la terreur, vous assistez impuissant à son enlèvement. '
                    'Puis les phares d\'un van blanc disparaissent dans la nuit.'
                ),
                'music_file': 'horror_intense.mp3',
                'music_transition': 'instant',
            },
            'ending_good': {
                'narrative': (
                    'Vous avez mémorisé la plaque. Trois lettres, quatre chiffres — gravés à jamais. '
                    'La police retrouve le van deux heures plus tard. '
                    'Votre frère est sain et sauf, tremblant mais vivant. '
                    'Dans ses yeux, vous lisez une gratitude infinie. '
                    'Vous avez fait la différence. Vous étiez le héros dont il avait besoin.'
                ),
                'music_file': 'calm_ambient.mp3',
                'music_transition': 'fade',
                'is_ending': True,
                'ending_type': 'good',
            },
            'ending_bad': {
                'narrative': (
                    'Vous vous êtes caché. La peur vous a cloué sur place. '
                    'Les heures ont passé. Les jours aussi. '
                    'Votre frère n\'est jamais revenu. '
                    'La culpabilité ronge chaque moment de silence. '
                    'Si seulement vous aviez agi différemment...'
                ),
                'music_file': 'horror_intense.mp3',
                'music_transition': 'fade',
                'is_ending': True,
                'ending_type': 'bad',
            },
            'ending_neutral': {
                'narrative': (
                    'Vous avez tout tenté, mais les événements vous ont dépassé. '
                    'La police enquête. Des indices existent. '
                    'L\'espoir est mince, mais il est là. '
                    'Vous attendez, la main crispée sur votre téléphone. '
                    'L\'histoire n\'est peut-être pas encore terminée.'
                ),
                'music_file': 'tension_rising.mp3',
                'music_transition': 'fade',
                'is_ending': True,
                'ending_type': 'neutral',
            },
        }

        # Créer toutes les scènes
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
        # 3. Créer les choix
        # ─────────────────────────────────────────────────────
        choices_data = [
            # scene_01 — chambre, 3h du matin
            (
                'scene_01',
                [
                    ('Passer par la porte principale', 'scene_corridor', 0),
                    ('Sortir par la porte de derrière', 'scene_backyard', 1),
                    ('Observer depuis la fenêtre', 'scene_window', 2),
                ]
            ),
            # scene_corridor — couloir sombre
            (
                'scene_corridor',
                [
                    ('Courir vers le jardin', 'scene_kidnap', 0),
                    ('Appeler la police immédiatement', 'scene_police', 1),
                    ('Se cacher et observer', 'ending_bad', 2),
                ]
            ),
            # scene_kidnap — enlèvement du frère
            (
                'scene_kidnap',
                [
                    ('Mémoriser la plaque d\'immatriculation du van', 'ending_good', 0),
                    ('Courir après le van', 'ending_neutral', 1),
                    ('Appeler à l\'aide en criant', 'ending_neutral', 2),
                ]
            ),
            # scene_backyard — jardin
            (
                'scene_backyard',
                [
                    ('Tenter de les intercepter', 'scene_kidnap', 0),
                    ('Appeler la police discrètement', 'scene_police', 1),
                    ('Mémoriser la plaque du van', 'ending_good', 2),
                ]
            ),
            # scene_window — depuis la fenêtre
            (
                'scene_window',
                [
                    ('Photographier la plaque avec votre téléphone', 'ending_good', 0),
                    ('Descendre en courant pour les arrêter', 'scene_kidnap', 1),
                    ('Appeler la police depuis la fenêtre', 'scene_police', 2),
                ]
            ),
            # scene_police — appel aux secours
            (
                'scene_police',
                [
                    ('Donner la plaque d\'immatriculation mémorisée', 'ending_good', 0),
                    ('Courir à l\'extérieur pendant l\'appel', 'ending_neutral', 1),
                    ('Attendre l\'arrivée de la police', 'ending_neutral', 2),
                ]
            ),
        ]

        total_choices = 0
        for scene_key, choices in choices_data:
            scene = scene_objects[scene_key]
            for text, next_key, order in choices:
                next_scene = scene_objects.get(next_key)
                Choice.objects.create(
                    scene=scene,
                    text=text,
                    next_scene=next_scene,
                    order=order
                )
                total_choices += 1

        self.stdout.write(f'  [OK] {total_choices} choix crees')

        # ─────────────────────────────────────────────────────
        # 4. Résumé final
        # ─────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('  [SUCCESS] Histoire de demonstration creee avec succes !'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'  Histoire : {story.title}')
        self.stdout.write(f'  Scènes   : {len(scene_objects)}')
        self.stdout.write(f'  Choix    : {total_choices}')
        self.stdout.write(f'  URL      : /play/la-nuit-du-kidnapping/auto/')
        self.stdout.write('')
        self.stdout.write('  Lancez le serveur et jouez :')
        self.stdout.write(self.style.HTTP_INFO('  python manage.py runserver'))
