"""
Formulaires de l'interface Narrateur.

Permettent à un administrateur de bâtir une histoire scène par scène depuis
le site, sans passer par l'admin Django : texte, ambiance musicale, puis un à
quatre choix. La clé technique de la scène est déduite du texte, l'auteur n'a
pas à l'inventer.
"""

from django import forms
from django.forms import inlineformset_factory
from django.utils.text import slugify

from .models import Story, Scene, Choice


# Un joueur ne doit pas avoir plus de quatre portes ouvertes à la fois :
# au-delà, la lecture devient un menu et l'arbre explose.
MAX_CHOIX = 4

# Classes Tailwind communes, pour que les widgets Django ressemblent au reste
# du site sans qu'on ait à styler chaque champ dans le template.
_CHAMP = ('w-full bg-gray-950 border border-gray-700 rounded-xl px-4 py-3 '
          'text-gray-100 text-[15px] focus:outline-none focus:border-purple-700')
_SELECT = _CHAMP + ' appearance-none'


class StoryForm(forms.ModelForm):
    """Création / édition d'une histoire."""

    class Meta:
        model = Story
        fields = ('title', 'description', 'cover_image', 'is_published')
        labels = {
            'title': 'Titre de l\'histoire',
            'description': 'Résumé présenté au joueur',
            'cover_image': 'Image de couverture (facultative)',
            'is_published': 'Publier — visible par les joueurs',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': _CHAMP, 'placeholder': 'Les Fils du Destin', 'autofocus': True}),
            'description': forms.Textarea(attrs={
                'class': _CHAMP, 'rows': 4,
                'placeholder': 'En quelques phrases, ce que le joueur va vivre…'}),
        }


class SceneForm(forms.ModelForm):
    """
    Une scène : son texte, son ambiance, son statut.

    `scene_key` reste modifiable mais devient facultative : laissée vide, elle
    est déduite des premiers mots du texte et rendue unique dans l'histoire.
    """

    class Meta:
        model = Scene
        # L'ordre compte : `narrative` est nettoyé avant `scene_key`, qui en
        # dépend pour se générer toute seule.
        fields = (
            'narrative', 'music_file', 'music_transition',
            'is_starting_scene', 'is_ending', 'ending_type',
            'image_auto_generate', 'scene_key',
        )
        labels = {
            'narrative': 'Texte de la scène',
            'music_file': 'Ambiance musicale',
            'music_transition': 'Transition musicale',
            'is_starting_scene': 'Scène de départ de l\'histoire',
            'is_ending': 'Cette scène termine l\'histoire',
            'ending_type': 'Type de fin',
            'image_auto_generate': 'Générer l\'illustration automatiquement',
            'scene_key': 'Identifiant technique',
        }
        widgets = {
            'narrative': forms.Textarea(attrs={
                'class': _CHAMP + ' font-story text-lg leading-relaxed',
                'rows': 9, 'autofocus': True,
                'placeholder': 'Tu pousses la porte de la crypte. L\'air y est froid…'}),
            'music_file': forms.Select(attrs={'class': _SELECT}),
            'music_transition': forms.Select(attrs={'class': _SELECT}),
            'ending_type': forms.Select(attrs={'class': _SELECT}),
            'scene_key': forms.TextInput(attrs={
                'class': _CHAMP, 'placeholder': 'laissé vide = déduit du texte'}),
        }

    def __init__(self, *args, story=None, **kwargs):
        super().__init__(*args, **kwargs)
        # L'histoire n'est pas un champ du formulaire : elle vient de l'URL.
        self.story = story or getattr(self.instance, 'story_id', None) and self.instance.story
        if self.story:
            self.instance.story = self.story
        self.fields['scene_key'].required = False
        self.fields['ending_type'].required = False

    def clean(self):
        donnees = super().clean()

        if donnees.get('is_ending') and not donnees.get('ending_type'):
            self.add_error('ending_type', "Précisez s'il s'agit d'une bonne, mauvaise ou neutre fin.")

        cle = (donnees.get('scene_key') or '').strip()
        if not cle:
            cle = self._cle_depuis_texte(donnees.get('narrative', ''))
        donnees['scene_key'] = self._cle_unique(cle)
        return donnees

    def _cle_depuis_texte(self, narrative):
        """Les premiers mots du texte font une clé lisible dans la carte."""
        base = slugify(' '.join((narrative or '').split()[:6]))[:40].replace('-', '_')
        return base or 'scene'

    def _cle_unique(self, base):
        """Ajoute un suffixe tant que la clé existe déjà dans cette histoire."""
        if not self.story:
            return base
        frères = Scene.objects.filter(story=self.story)
        if self.instance.pk:
            frères = frères.exclude(pk=self.instance.pk)
        cle, n = base, 2
        while frères.filter(scene_key=cle).exists():
            cle = f'{base}_{n}'
            n += 1
        return cle


class ChoiceForm(forms.ModelForm):
    """Un choix proposé au joueur. Un slot laissé vide est simplement ignoré."""

    class Meta:
        model = Choice
        fields = ('text',)
        labels = {'text': 'Texte du choix'}
        widgets = {
            'text': forms.TextInput(attrs={
                'class': _CHAMP,
                'placeholder': 'Ex. : Pousser la porte malgré la peur'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].required = False


class BaseChoiceFormSet(forms.BaseInlineFormSet):
    """
    Quatre emplacements, dont l'auteur remplit un à quatre. Les vides sont
    ignorés plutôt que refusés : c'est ce qui permet de n'en proposer qu'un.
    Une scène de fin n'en a aucun — c'est la seule façon de terminer.
    """

    # Renseigné par la vue depuis le formulaire de scène, avant is_valid() :
    # les deux formulaires se valident ensemble, une fin n'a pas de choix.
    scene_est_fin = False

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        remplis = [
            f for f in self.forms
            if (f.cleaned_data.get('text') or '').strip()
        ]
        fin = self.scene_est_fin

        if not remplis and not fin:
            raise forms.ValidationError(
                "Ajoutez au moins un choix, ou cochez « Cette scène termine l'histoire »."
            )
        if remplis and fin:
            raise forms.ValidationError(
                "Une scène de fin ne peut pas proposer de choix : "
                "videz les choix, ou décochez la case de fin."
            )
        self.remplis = remplis

    def save(self, commit=True):
        """N'enregistre que les choix effectivement remplis, dans l'ordre affiché."""
        instances = []
        for rang, form in enumerate(self.forms):
            texte = (form.cleaned_data.get('text') or '').strip()
            choix = form.instance
            if not texte:
                # Un choix vidé par l'auteur disparaît — et avec lui sa branche.
                if choix.pk:
                    choix.delete()
                continue
            choix.scene = self.instance
            choix.text = texte
            choix.order = rang
            if commit:
                choix.save()
            instances.append(choix)
        return instances


ChoiceFormSet = inlineformset_factory(
    Scene, Choice,
    # Choice pointe deux fois vers Scene (scene et next_scene) : il faut dire
    # laquelle des deux porte l'inline.
    fk_name='scene',
    form=ChoiceForm,
    formset=BaseChoiceFormSet,
    fields=('text',),
    extra=MAX_CHOIX,
    max_num=MAX_CHOIX,
    validate_max=True,
    # Pas de case « supprimer » : vider le texte d'un choix le retire.
    can_delete=False,
)
