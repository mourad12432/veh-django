"""
Interface Narrateur — création d'histoires et de scènes par les administrateurs.

Réservée au personnel (`is_staff`) : c'est la même barrière que /admin/, mais
avec un parcours pensé pour l'écriture plutôt que pour l'édition de tables.

Le fil conducteur :

    Accueil  →  nouvelle histoire  →  première scène (texte + musique + choix)
                                          │
                                    « Enregistrer »
                                          │
                              chaque choix sans suite affiche
                              « Créer la scène de ce choix »
                                          │
                                     nouvelle scène ─── et ainsi de suite
                                          │
                     bouton « Carte » en haut à droite → l'arbre complet
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View

from .forms import StoryForm, SceneForm, ChoiceFormSet, MAX_CHOIX
from .illustration import autogenerate_image
from .models import Story, Scene, Choice
from .services import story_map


def narrateur_requis(vue):
    """
    N'autorise que les administrateurs. Un joueur connecté reçoit un 403 plutôt
    qu'une redirection : l'interface n'est pas censée exister pour lui.
    """
    @login_required
    def enveloppe(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied(
                "L'interface Narrateur est réservée aux administrateurs."
            )
        return vue(request, *args, **kwargs)
    return enveloppe


narrateur = method_decorator(narrateur_requis, name='dispatch')


@narrateur
class AccueilView(View):
    """Liste des histoires, avec l'état d'avancement de chacune."""
    template_name = 'narrateur/accueil.html'

    def get(self, request):
        histoires = []
        for story in Story.objects.prefetch_related('scenes__choices'):
            scenes = list(story.scenes.all())
            ouvertes = sum(
                1 for s in scenes for c in s.choices.all() if c.next_scene_id is None
            )
            histoires.append({
                'story': story,
                'scenes': len(scenes),
                'fins': sum(1 for s in scenes if s.is_ending),
                'branches_ouvertes': ouvertes,
                'depart': next((s for s in scenes if s.is_starting_scene), None),
            })
        return render(request, self.template_name, {'histoires': histoires})


@narrateur
class HistoireCreateView(View):
    """Création d'une histoire, puis enchaînement direct sur sa première scène."""
    template_name = 'narrateur/histoire_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': StoryForm()})

    def post(self, request):
        form = StoryForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})
        story = form.save()
        messages.success(request, f"Histoire « {story.title} » créée. Écrivez sa première scène.")
        return redirect('narrateur_scene_nouvelle', story_slug=story.slug)


@narrateur
class SceneEditView(View):
    """
    Écriture d'une scène : texte, ambiance, et un à quatre choix.

    Trois entrées possibles :
      - nouvelle scène de départ        /narrateur/<slug>/scene/nouvelle/
      - nouvelle scène issue d'un choix /narrateur/<slug>/scene/nouvelle/?choix=<id>
      - modification                    /narrateur/<slug>/scene/<scene_key>/
    """
    template_name = 'narrateur/scene_form.html'

    def _slots_visibles(self, formset):
        """
        Combien d'emplacements de choix afficher d'emblée : ceux qui portent
        déjà un texte, et au minimum un. Les autres restent masqués derrière le
        bouton « + Ajouter un choix ».
        """
        remplis = 0
        for form in formset.forms:
            if formset.is_bound:
                valeur = form.data.get(form.add_prefix('text'), '')
            else:
                valeur = form.initial.get('text', '')
            if (valeur or '').strip():
                remplis += 1
        return max(1, remplis)

    def _contexte(self, request, story, scene, form, formset, choix_source):
        premiere = not story.scenes.exists()
        return {
            'nb_choix_visibles': self._slots_visibles(formset),
            'story': story,
            'scene': scene if scene.pk else None,
            'form': form,
            'formset': formset,
            'choix_source': choix_source,
            'premiere_scene': premiere,
            'max_choix': MAX_CHOIX,
            # Les choix déjà enregistrés qui n'ont pas encore de suite : c'est
            # la liste sur laquelle l'auteur clique pour continuer son arbre.
            'choix_enregistres': (
                list(scene.choices.select_related('next_scene').order_by('order'))
                if scene.pk else []
            ),
        }

    def _charger(self, request, story_slug, scene_key):
        story = get_object_or_404(Story, slug=story_slug)
        if scene_key:
            scene = get_object_or_404(Scene, story=story, scene_key=scene_key)
        else:
            scene = Scene(story=story)
        # Le choix d'où l'on vient : il sera relié à la scène créée.
        choix_source = None
        choix_id = request.GET.get('choix') or request.POST.get('choix')
        if choix_id:
            choix_source = Choice.objects.filter(
                pk=choix_id, scene__story=story
            ).select_related('scene').first()
        return story, scene, choix_source

    def get(self, request, story_slug, scene_key=None):
        story, scene, choix_source = self._charger(request, story_slug, scene_key)
        initial = {}
        if not scene.pk and not story.scenes.exists():
            # La toute première scène d'une histoire est sa scène de départ.
            initial['is_starting_scene'] = True
        form = SceneForm(instance=scene, story=story, initial=initial)
        formset = ChoiceFormSet(instance=scene)
        return render(request, self.template_name,
                      self._contexte(request, story, scene, form, formset, choix_source))

    def post(self, request, story_slug, scene_key=None):
        story, scene, choix_source = self._charger(request, story_slug, scene_key)
        form = SceneForm(request.POST, instance=scene, story=story)
        formset = ChoiceFormSet(request.POST, instance=scene)

        # Les deux formulaires se valident ensemble : le formset a besoin de
        # savoir si la scène est une fin pour accepter zéro choix.
        scene_ok = form.is_valid()
        formset.scene_est_fin = bool(form.cleaned_data.get('is_ending')) if scene_ok else False
        formset_ok = formset.is_valid()

        if not (scene_ok and formset_ok):
            return render(request, self.template_name,
                          self._contexte(request, story, scene, form, formset, choix_source))

        with transaction.atomic():
            scene = form.save(commit=False)
            scene.story = story
            scene.scene_key = form.cleaned_data['scene_key']
            if scene.is_starting_scene:
                # Une seule scène de départ par histoire.
                Scene.objects.filter(story=story, is_starting_scene=True).exclude(
                    pk=scene.pk).update(is_starting_scene=False)
            scene.save()

            formset.instance = scene
            formset.save()

            # Raccorder la branche d'où l'on vient à la scène qu'on vient d'écrire.
            if choix_source and choix_source.next_scene_id is None:
                choix_source.next_scene = scene
                choix_source.save(update_fields=['next_scene'])
                messages.success(
                    request,
                    f"Scène reliée au choix « {choix_source.text} ».")

        messages.success(request, f"Scène « {scene.scene_key} » enregistrée.")

        # Même comportement que l'admin : l'illustration se déclenche ici, une
        # fois la scène et ses choix enregistrés, et n'empêche rien si elle échoue.
        autogenerate_image(request, scene)

        return redirect('narrateur_scene', story_slug=story.slug, scene_key=scene.scene_key)


@narrateur
class CarteView(View):
    """L'arbre de l'histoire, dessiné en SVG."""
    template_name = 'narrateur/carte.html'

    def get(self, request, story_slug):
        story = get_object_or_404(Story, slug=story_slug)
        return render(request, self.template_name, {
            'story': story,
            'carte': story_map.build_map(story),
        })
