"""
Déclenchement de l'illustration depuis une page web.

Partagé par les deux endroits où un auteur enregistre une scène — l'admin
Django et l'interface Narrateur — pour que les deux se comportent pareil :
l'image est générée à l'enregistrement, et un échec n'empêche jamais la scène
d'être sauvegardée.

La logique de génération elle-même vit dans services/image_service.py ; ce
module ne fait que la relier aux messages de l'interface.
"""

from django.conf import settings
from django.contrib import messages

from .services import image_service


# Au-delà de ce nombre d'images dans un même enregistrement, on s'arrête :
# chaque image coûte un ou deux appels réseau et la requête HTTP finirait en
# timeout. Le reste se rattrape par l'action de l'admin ou la commande.
MAX_PAR_ENREGISTREMENT = 3


def autogenerate_image(request, scene, counter=None):
    """
    Illustre `scene` si elle en a besoin, en rapportant le résultat à l'auteur
    via les messages. N'interrompt jamais l'enregistrement : une clé absente,
    un quota dépassé ou un service injoignable laisse simplement la scène sans
    image.

    `counter` est une liste à un élément servant de compteur partagé entre les
    scènes d'un même enregistrement (voir MAX_PAR_ENREGISTREMENT).
    """
    if not getattr(settings, 'SCENE_IMAGE_AUTOGEN', True):
        return
    if not image_service.needs_illustration(scene):
        return

    if counter is not None:
        if counter[0] >= MAX_PAR_ENREGISTREMENT:
            messages.info(
                request,
                f"« {scene.scene_key} » n'a pas été illustrée maintenant "
                f"(limite de {MAX_PAR_ENREGISTREMENT} images par enregistrement). "
                "Sélectionnez-la dans la liste des scènes et lancez l'action "
                "« Illustrer avec l'IA »."
            )
            return
        counter[0] += 1

    try:
        _, backend = image_service.illustrate_scene(scene)
    except image_service.ImageError as e:
        messages.warning(request, f"Illustration de « {scene.scene_key} » impossible : {e}")
    except Exception as e:
        messages.error(request, f"Erreur pendant l'illustration de « {scene.scene_key} » : {e}")
    else:
        messages.success(request, f"Image générée pour « {scene.scene_key} » (via {backend}).")
