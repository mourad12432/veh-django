"""
Disposition de l'arbre d'une histoire, pour la carte du Narrateur.

Calcule des coordonnées côté serveur et les rend en SVG : pas de bibliothèque
JavaScript, pas de CDN, la carte s'affiche même hors ligne.

Principe : un parcours en largeur depuis la scène de départ range chaque scène
dans une colonne = sa distance au début. Les scènes qu'aucun choix n'atteint
sont regroupées dans une colonne « orphelines » à droite, ce qui les rend
visibles au lieu de les laisser invisibles dans la base.
"""

from collections import deque


# Géométrie de la carte, en unités SVG
NODE_W, NODE_H = 210, 74
COL_ECART, LIGNE_ECART = 300, 104
MARGE = 40


def _couleur(scene):
    """Un nœud se lit d'un coup d'œil : départ, fin, ou scène ordinaire."""
    if scene.is_starting_scene:
        return '#2E9E6C'
    if scene.is_ending:
        return {'good': '#3DCC8E', 'bad': '#E85A5A'}.get(scene.ending_type, '#9C8038')
    return '#2A6AAA'


def build_map(story):
    """
    Retourne le dictionnaire attendu par le template : nœuds, arêtes et
    dimensions du dessin.

    Chaque nœud porte sa position, son libellé et l'état de sa branche ; chaque
    arête porte une courbe de Bézier et le texte du choix qu'elle représente.
    """
    scenes = list(story.scenes.prefetch_related('choices__next_scene'))
    par_id = {s.id: s for s in scenes}

    # ── Profondeur de chaque scène : distance à la scène de départ ──────────
    profondeur = {}

    def parcourir(racine, colonne):
        """Parcours en largeur : chaque scène atteinte gagne la colonne suivante."""
        profondeur[racine.id] = colonne
        file = deque([racine])
        while file:
            scene = file.popleft()
            for choix in scene.choices.all():
                suivante = choix.next_scene
                # Un choix peut revenir en arrière : la première visite fait foi.
                if suivante is not None and suivante.id not in profondeur:
                    profondeur[suivante.id] = profondeur[scene.id] + 1
                    file.append(suivante)

    depart = next((s for s in scenes if s.is_starting_scene), None)
    if depart:
        parcourir(depart, 0)

    # Les scènes hors du parcours principal sont dépliées elles aussi, à droite
    # de celui-ci : sans ça, une branche orpheline de trois scènes s'écraserait
    # sur une seule colonne et ses liens ressembleraient à des boucles.
    orphelines = [s for s in scenes if s.id not in profondeur]
    col_orphelines = (max(profondeur.values()) + 1) if profondeur else 0
    cibles = {c.next_scene_id for s in scenes for c in s.choices.all() if c.next_scene_id}
    # On démarre par celles que rien ne vise : ce sont les vraies têtes de branche.
    racines = [s for s in orphelines if s.id not in cibles] or orphelines
    for racine in racines:
        if racine.id not in profondeur:
            parcourir(racine, col_orphelines)
    # Restent les cycles fermés — A mène à B qui remène à A : aucun des deux
    # n'est une tête de branche. On y entre par une scène arbitraire, sinon ils
    # s'empileraient dans la même colonne.
    for scene in orphelines:
        if scene.id not in profondeur:
            parcourir(scene, col_orphelines)

    # ── Position : colonne = profondeur, ligne = rang dans la colonne ───────
    colonnes = {}
    for scene in scenes:
        colonnes.setdefault(profondeur[scene.id], []).append(scene)

    position = {}
    for col, membres in colonnes.items():
        membres.sort(key=lambda s: (not s.is_starting_scene, s.scene_key))
        for ligne, scene in enumerate(membres):
            position[scene.id] = (
                MARGE + col * COL_ECART,
                MARGE + ligne * LIGNE_ECART,
            )

    # ── Nœuds ───────────────────────────────────────────────────────────────
    noeuds = []
    for scene in scenes:
        x, y = position[scene.id]
        sans_suite = [c for c in scene.choices.all() if c.next_scene_id is None]
        noeuds.append({
            'scene': scene,
            'x': x, 'y': y, 'w': NODE_W, 'h': NODE_H,
            'couleur': _couleur(scene),
            'orpheline': scene in orphelines,
            'branches_ouvertes': len(sans_suite),
            'extrait': (scene.narrative or '')[:46].strip(),
        })

    # ── Arêtes ──────────────────────────────────────────────────────────────
    aretes = []
    for scene in scenes:
        for choix in scene.choices.all():
            if choix.next_scene_id is None or choix.next_scene_id not in position:
                continue
            x1, y1 = position[scene.id]
            x2, y2 = position[choix.next_scene_id]
            depart_x, depart_y = x1 + NODE_W, y1 + NODE_H / 2
            arrivee_x, arrivee_y = x2, y2 + NODE_H / 2
            milieu = (arrivee_x - depart_x) / 2
            aretes.append({
                'chemin': (f'M {depart_x} {depart_y} '
                           f'C {depart_x + milieu} {depart_y}, '
                           f'{arrivee_x - milieu} {arrivee_y}, '
                           f'{arrivee_x} {arrivee_y}'),
                'texte': choix.text[:28],
                'tx': (depart_x + arrivee_x) / 2,
                'ty': (depart_y + arrivee_y) / 2 - 6,
                # Un choix qui remonte vers une scène déjà vue : boucle assumée.
                'retour': profondeur[choix.next_scene_id] <= profondeur[scene.id],
            })

    largeur = MARGE * 2 + (max(colonnes) if colonnes else 0) * COL_ECART + NODE_W
    hauteur = MARGE * 2 + max((len(m) for m in colonnes.values()), default=1) * LIGNE_ECART

    return {
        'noeuds': noeuds,
        'aretes': aretes,
        'largeur': largeur,
        'hauteur': hauteur,
        'orphelines': orphelines,
        'depart': depart,
        'total': len(scenes),
        'fins': [s for s in scenes if s.is_ending],
        'branches_ouvertes': sum(n['branches_ouvertes'] for n in noeuds),
    }
