from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0002_scene_audio_narration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scene',
            name='music_file',
            field=models.CharField(
                choices=[
                    ('calm_ambient.mp3',      'Calme / Repos'),
                    ('tension_rising.mp3',    'Tension / Suspense'),
                    ('horror_intense.mp3',    'Horreur / Angoisse'),
                    ('combat_action.mp3',     'Combat / Bagarre'),
                    ('sad_melancholy.mp3',    'Triste / Mélancolique'),
                    ('mysterious_wonder.mp3', 'Mystère / Exploration'),
                    ('triumphant_victory.mp3','Triomphe / Victoire'),
                    ('dramatic_reveal.mp3',   'Dramatique / Révélation'),
                    ('romantic_tender.mp3',   'Romantique / Tendresse'),
                    ('danger_stealth.mp3',    'Danger / Furtif'),
                ],
                default='calm_ambient.mp3',
                help_text='Piste de fond jouée pendant cette scène (fichiers dans static/music/)',
                max_length=100,
                verbose_name='Ambiance musicale',
            ),
        ),
    ]
