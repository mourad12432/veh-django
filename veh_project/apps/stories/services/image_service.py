"""
Service d'illustration automatique des scènes.

Deux étapes, chacune avec un chemin GRATUIT et un chemin premium :

    1. texte narratif ──► prompt visuel
         « gemini » si une clé API est configurée (meilleure description),
         sinon extraction locale du texte — gratuit, hors ligne, sans clé.

    2. prompt visuel ──► image
         backends essayés dans l'ordre (réglage SCENE_IMAGE_BACKEND) :
         « pollinations » — gratuit, sans clé, sans facturation
         « gemini »       — meilleure qualité, exige la facturation activée
                            (le palier gratuit de l'API est à quota 0 sur les
                            modèles *-image)

    3. l'image est écrite dans Scene.image (media/scenes/) : elle devient
       aussitôt le fond de scène du web (game.html) et du mobile
       (serializers.image_url → Flutter), sans autre branchement.

Déclenché quand un auteur enregistre une scène dans le back-office (voir
SceneAdmin), ou en masse via :

    python manage.py generate_scene_images

Tout fonctionne sans aucune clé API. GEMINI_API_KEY n'est qu'une amélioration :
dès qu'elle est renseignée, l'étape 1 passe automatiquement sur Gemini.

Ajouter un backend d'image = écrire une fonction (prompt, aspect, client) qui
renvoie (octets, extension), puis l'inscrire dans IMAGE_BACKENDS.
"""

import hashlib
import os
import random
import re
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.files.base import ContentFile


# ─────────────────────────────────────────────────────────────────────────────
#  Réglages par défaut
# ─────────────────────────────────────────────────────────────────────────────

# Backends d'image, essayés dans l'ordre. Le gratuit d'abord : c'est le seul
# qui fonctionne sans facturation, et il ne demande aucune clé.
DEFAULT_IMAGE_BACKENDS = ['pollinations', 'gemini']

# Modèles Gemini essayés dans l'ordre, jusqu'à ce que l'un réponde. Une liste
# plutôt qu'un nom unique parce que Google retire ses modèles sans préavis
# (404) et les surcharge aux heures de pointe (503).
DEFAULT_PROMPT_MODELS = ['gemini-flash-latest', 'gemini-3.5-flash-lite']
DEFAULT_GEMINI_IMAGE_MODELS = ['gemini-3.1-flash-image', 'gemini-2.5-flash-image']

# Format d'un fond de scène : large, jamais carré
DEFAULT_ASPECT_RATIO = '16:9'
# Largeur demandée ; la hauteur se déduit du ratio. Pollinations plafonne son
# rendu gratuit à 1024 de large et renvoie donc du 1024x576 — le ratio, lui,
# est bien respecté, et c'est ce qui compte pour un fond de scène.
BASE_WIDTH = 1280

# Pollinations : génération d'images libre, sans inscription ni clé.
POLLINATIONS_URL = 'https://image.pollinations.ai/prompt/{prompt}'
POLLINATIONS_MODEL = 'flux'
HTTP_TIMEOUT = 180          # ces services sont lents aux heures pleines
USER_AGENT = 'VEH/1.0 (jeu narratif Django)'

# Codes qui signifient « celui-là ne peut pas répondre » : on passe au suivant.
# Toute autre erreur (clé invalide, contenu bloqué) remonte tout de suite.
_UNAVAILABLE = ('404', '429', '503', 'NOT_FOUND', 'RESOURCE_EXHAUSTED', 'UNAVAILABLE')

# Direction artistique commune à TOUTES les scènes. C'est elle qui garantit
# que deux scènes générées à des semaines d'intervalle se ressemblent.
DEFAULT_STYLE = (
    "illustration numérique cinématographique, peinture digitale détaillée, "
    "éclairage dramatique, palette sombre et contrastée, ambiance de roman "
    "interactif, plan large, aucun texte ni logo dans l'image"
)

# Consigne envoyée au modèle texte pour qu'il traduise la narration en prompt.
PROMPT_INSTRUCTION = """\
Tu es directeur artistique pour un jeu narratif. À partir du texte de scène
ci-dessous, écris UN SEUL paragraphe en français qui décrit l'image de fond
illustrant cette scène.

Règles strictes :
- Décris uniquement ce qui est VISIBLE : décor, lieu, moment de la journée,
  météo, lumière, couleurs dominantes, profondeur de champ.
- Plan large, aucun visage en gros plan, aucun personnage reconnaissable.
- Aucun texte, aucune lettre, aucun chiffre, aucun logo dans l'image.
- Pas de dialogue, pas de récit, pas de titre : seulement la description visuelle.
- 60 mots maximum, en une ou deux phrases.

Histoire : {story}
Texte de la scène :
---
{narrative}
---
"""

# Extensions par type MIME
_MIME_EXT = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'image/webp': 'webp',
}


class ImageError(RuntimeError):
    """Erreur de configuration ou d'appel du service d'illustration."""


def conf(name, default):
    """Lit un réglage Django s'il existe, sinon la valeur par défaut du module."""
    return getattr(settings, name, default)


def setting_list(name, defaults):
    """
    Liste ordonnée pour ce réglage. Accepte aussi bien une liste qu'une chaîne
    « a,b,c » — pratique depuis une variable d'environnement.
    """
    value = conf(name, None)
    if not value:
        return list(defaults)
    if isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    return list(value)


def parse_size(aspect):
    """« 16:9 » → (1280, 720). Les dimensions restent multiples de 8."""
    try:
        w, h = (float(n) for n in str(aspect).split(':'))
        height = int(round(BASE_WIDTH * h / w / 8)) * 8
        return BASE_WIDTH, max(height, 8)
    except (ValueError, ZeroDivisionError):
        return BASE_WIDTH, 720


# ─────────────────────────────────────────────────────────────────────────────
#  Client Gemini (facultatif)
# ─────────────────────────────────────────────────────────────────────────────

def get_client(required=True):
    """
    Instancie le client Gemini à partir de GEMINI_API_KEY.

    `required=False` renvoie None au lieu de lever quand la clé ou le SDK
    manque : c'est le mode normal du pipeline, qui sait travailler sans.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        if not required:
            return None
        raise ImageError(
            "GEMINI_API_KEY n'est pas configurée. "
            "Ajoutez-la dans veh_project/.env (la même que celle de la narration)."
        )
    try:
        from google import genai
    except ImportError:
        if not required:
            return None
        raise ImageError(
            "Le SDK google-genai n'est pas installé.\n"
            "Lancez : pip install google-genai"
        )
    return genai.Client(api_key=api_key)


def try_models(call, models, quoi):
    """
    Essaie `call(model)` sur chaque modèle jusqu'à ce que l'un réponde.
    Ne passe au suivant que si le modèle est indisponible (retiré, saturé, hors
    quota) : une vraie erreur d'appel remonte immédiatement.
    """
    derniere = None
    for model in models:
        try:
            return call(model)
        except Exception as e:
            if not any(code in str(e) for code in _UNAVAILABLE):
                raise
            derniere = e

    detail = str(derniere or '')
    if 'limit: 0' in detail:
        raise ImageError(
            f"{quoi} : non inclus dans le palier gratuit de l'API Gemini "
            "(quota limite = 0). Activez la facturation, ou restez sur un "
            "backend gratuit."
        )
    raise ImageError(
        f"{quoi} : aucun modèle disponible parmi {', '.join(models)}. "
        f"Réponse de l'API — {detail[:250]}"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Étape 1 — la narration devient un prompt visuel
# ─────────────────────────────────────────────────────────────────────────────

def local_visual_prompt(scene, max_words=60):
    """
    Repli gratuit et hors ligne : le prompt est tiré directement du texte.

    On enlève les guillemets de dialogue et on coupe à 60 mots. C'est plus
    grossier qu'un prompt écrit par Gemini — le texte raconte au lieu de
    décrire — mais cela suffit à donner un décor cohérent au générateur.
    """
    text = re.sub(r'["«»“”]', ' ', scene.narrative or '')
    text = re.sub(r'\s+', ' ', text).strip()
    mots = text.split(' ')
    if len(mots) > max_words:
        text = ' '.join(mots[:max_words])
    return text


def build_visual_prompt(client, scene, model=None):
    """
    Décrit visuellement la scène. Passe par Gemini si un client est fourni,
    sinon retombe sur l'extraction locale. Lève ImageError si la scène est vide.
    """
    if not (scene.narrative or '').strip():
        raise ImageError("La scène n'a pas de texte narratif à illustrer.")

    if client is None:
        return local_visual_prompt(scene)

    models = [model] if model else setting_list('SCENE_IMAGE_PROMPT_MODEL', DEFAULT_PROMPT_MODELS)
    question = PROMPT_INSTRUCTION.format(story=scene.story.title, narrative=scene.narrative.strip())
    response = try_models(
        lambda m: client.models.generate_content(model=m, contents=question),
        models, "Écriture du prompt visuel",
    )
    prompt = (getattr(response, 'text', '') or '').strip()
    if not prompt:
        # Gemini a répondu à vide (contenu jugé sensible) : le texte fait foi.
        return local_visual_prompt(scene)
    return prompt


def decorate_prompt(prompt, style=None):
    """Ajoute la direction artistique commune derrière le prompt de la scène."""
    style = style if style is not None else conf('SCENE_IMAGE_STYLE', DEFAULT_STYLE)
    prompt = (prompt or '').strip()
    return f"{prompt}\n\nStyle : {style}." if style else prompt


# ─────────────────────────────────────────────────────────────────────────────
#  Étape 2 — le prompt devient une image
# ─────────────────────────────────────────────────────────────────────────────

def _image_config(types, aspect):
    """
    Config Gemini, en ne passant que ce que le SDK installé connaît réellement :
    `image_config` n'existe que dans les versions récentes de google-genai, et
    son absence ne doit pas casser la génération.
    """
    kwargs = {'response_modalities': ['TEXT', 'IMAGE']}
    if aspect and hasattr(types, 'ImageConfig'):
        try:
            kwargs['image_config'] = types.ImageConfig(aspect_ratio=aspect)
        except TypeError:
            pass
    return types.GenerateContentConfig(**kwargs)


def image_via_gemini(prompt, aspect, client=None):
    """Backend Gemini — qualité supérieure, mais exige la facturation activée."""
    if client is None:
        raise ImageError("aucune clé Gemini configurée")
    from google.genai import types

    models = setting_list('SCENE_IMAGE_MODEL', DEFAULT_GEMINI_IMAGE_MODELS)
    config = _image_config(types, aspect)
    response = try_models(
        lambda m: client.models.generate_content(model=m, contents=prompt, config=config),
        models, "Génération de l'image",
    )

    # La réponse mélange des parts texte et une part image : on prend la
    # première part binaire de type image/*.
    try:
        parts = response.candidates[0].content.parts or []
    except (AttributeError, IndexError, TypeError):
        raise ImageError("réponse vide (contenu bloqué ?)")

    for part in parts:
        inline = getattr(part, 'inline_data', None)
        if inline is None or not inline.data:
            continue
        mime = (inline.mime_type or 'image/png').split(';')[0].strip()
        if mime.startswith('image/'):
            return inline.data, _MIME_EXT.get(mime, 'png')
    raise ImageError("aucune image dans la réponse")


def image_via_pollinations(prompt, aspect, client=None):
    """
    Backend gratuit — service public, sans inscription ni clé API.

    L'image est simplement le contenu d'une URL : le prompt est encodé dans le
    chemin, les dimensions en paramètres. Aucune dépendance ajoutée, urllib de
    la bibliothèque standard suffit.
    """
    width, height = parse_size(aspect)
    params = urllib.parse.urlencode({
        'width': width,
        'height': height,
        'model': conf('SCENE_IMAGE_POLLINATIONS_MODEL', '') or POLLINATIONS_MODEL,
        'nologo': 'true',
        'seed': random.randint(0, 2 ** 31 - 1),
    })
    # Le prompt passe dans l'URL : on le borne pour ne pas dépasser les limites
    # de longueur des serveurs intermédiaires.
    chemin = urllib.parse.quote(prompt.strip()[:1200], safe='')
    url = f"{POLLINATIONS_URL.format(prompt=chemin)}?{params}"

    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as reponse:
            mime = (reponse.headers.get('Content-Type') or '').split(';')[0].strip()
            data = reponse.read()
    except OSError as e:      # URLError, HTTPError, timeout socket…
        raise ImageError(f"service injoignable ({e})")

    if not data or not mime.startswith('image/'):
        raise ImageError(f"réponse sans image (Content-Type : {mime or 'inconnu'})")
    return data, _MIME_EXT.get(mime, 'jpg')


# Registre des backends. En ajouter un : écrire une fonction de même signature
# — (prompt, aspect, client) → (octets, extension) — et l'inscrire ici.
IMAGE_BACKENDS = {
    'pollinations': image_via_pollinations,
    'gemini': image_via_gemini,
}


def generate_image(prompt, client=None, backends=None, aspect=None):
    """
    Produit l'image en essayant chaque backend dans l'ordre.
    Retourne (octets, extension, nom du backend qui a répondu).
    """
    aspect = aspect or conf('SCENE_IMAGE_ASPECT_RATIO', DEFAULT_ASPECT_RATIO)
    noms = backends or setting_list('SCENE_IMAGE_BACKEND', DEFAULT_IMAGE_BACKENDS)

    echecs = []
    for nom in noms:
        backend = IMAGE_BACKENDS.get(nom)
        if backend is None:
            echecs.append(f"{nom} : backend inconnu "
                          f"(disponibles : {', '.join(IMAGE_BACKENDS)})")
            continue
        try:
            data, ext = backend(prompt, aspect, client=client)
            return data, ext, nom
        except Exception as e:
            echecs.append(f"{nom} : {e}")

    raise ImageError("aucun backend n'a produit d'image.\n    - " + "\n    - ".join(echecs))


# ─────────────────────────────────────────────────────────────────────────────
#  Orchestration
# ─────────────────────────────────────────────────────────────────────────────

def source_fingerprint(scene, style=None):
    """
    Empreinte « <texte>:<prompt> » de ce qui détermine l'image.

    Deux digests séparés, parce que les deux cas n'appellent pas la même
    réaction : si la NARRATION a bougé, le prompt est périmé et doit être
    réécrit ; si seul le PROMPT a bougé (l'auteur l'a retouché à la main),
    il suffit de redessiner. Si rien n'a bougé, aucun appel réseau.
    """
    style = style if style is not None else conf('SCENE_IMAGE_STYLE', DEFAULT_STYLE)
    art = style + '|' + ','.join(setting_list('SCENE_IMAGE_BACKEND', DEFAULT_IMAGE_BACKENDS))
    return '{}:{}'.format(
        _sha((scene.narrative or '').strip(), art),
        _sha((scene.image_prompt or '').strip()),
    )


def _sha(*parts):
    return hashlib.sha1('|'.join(parts).encode('utf-8')).hexdigest()[:16]


def narrative_changed(scene, style=None):
    """
    True si le texte narratif (ou la direction artistique) a changé depuis la
    dernière illustration — le prompt visuel enregistré ne décrit alors plus la
    bonne scène et doit être réécrit.

    Une scène jamais illustrée répond False : le prompt qu'un auteur y aurait
    écrit à la main fait foi, on ne l'écrase pas.
    """
    stored = scene.image_source_hash or ''
    if not stored:
        return False
    return stored.split(':')[0] != source_fingerprint(scene, style).split(':')[0]


def has_static_artwork(scene):
    """
    True si un visuel a été posé à la main dans static/scenes/{scene_key}.*
    (même convention que serializers._static_asset_url). Ces scènes ont déjà un
    fond : l'IA ne doit pas s'y substituer toute seule.
    """
    from django.contrib.staticfiles import finders

    for ext in ('png', 'jpg', 'jpeg', 'jfif', 'webp'):
        if finders.find(f'scenes/{scene.scene_key}.{ext}'):
            return True
    return False


def needs_illustration(scene):
    """
    True si la scène doit être (re)illustrée automatiquement à l'enregistrement :
    option activée, texte présent, et soit aucune image, soit un contenu modifié
    depuis la dernière génération.
    """
    if not scene.image_auto_generate:
        return False
    if not (scene.narrative or '').strip():
        return False
    if not scene.image:
        # Un fichier static/scenes/ existant fait déjà office de fond.
        return not has_static_artwork(scene)
    # Une image uploadée par l'auteur n'est jamais écrasée.
    if not scene.image_is_generated:
        return False
    return scene.image_source_hash != source_fingerprint(scene)


def illustrate_scene(scene, *, client=None, force=False, rewrite_prompt=False, style=None):
    """
    Illustre une scène de bout en bout et enregistre le résultat dans
    `scene.image`. Retourne (prompt utilisé, nom du backend).

    - `force`          : régénère même si une image à jour existe déjà.
    - `rewrite_prompt` : redemande un prompt même si l'auteur en a écrit un.
    - Ne demande aucune clé API : sans clé, le prompt vient du texte et
      l'image du backend gratuit.
    """
    if not (scene.narrative or '').strip():
        raise ImageError("La scène n'a pas de texte narratif à illustrer.")
    if not force and not needs_illustration(scene):
        return scene.image_prompt, None

    # Le client Gemini n'est qu'un bonus : absent, le pipeline continue.
    client = client or get_client(required=False)

    # 1. Le prompt écrit à la main par l'auteur fait foi ; il est écrit s'il est
    #    vide, ou réécrit si la narration a changé sous ses pieds.
    prompt = (scene.image_prompt or '').strip()
    if not prompt or rewrite_prompt or narrative_changed(scene, style):
        prompt = build_visual_prompt(client, scene)

    # 2. Prompt de la scène + direction artistique commune → l'image.
    data, ext, backend = generate_image(decorate_prompt(prompt, style), client=client)

    # 3. On remplace le fichier précédent seulement s'il venait déjà de l'IA :
    #    un visuel uploadé par l'auteur n'est jamais supprimé du disque.
    if scene.image and scene.image_is_generated:
        scene.image.delete(save=False)

    filename = f'{scene.story.slug}_{scene.scene_key}.{ext}'
    scene.image_prompt = prompt
    scene.image_is_generated = True
    scene.image.save(filename, ContentFile(data), save=False)
    scene.image_source_hash = source_fingerprint(scene, style)
    scene.save(update_fields=[
        'image', 'image_prompt', 'image_is_generated', 'image_source_hash',
    ])
    return prompt, backend
