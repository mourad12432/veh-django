# VEH — Vous Êtes le Héros

Jeu narratif à embranchements : le joueur lit une scène, choisit, et son choix
décide de la suite. Chaque scène a son ambiance musicale, sa narration audio et
son image de fond — cette dernière étant **générée automatiquement à partir du
texte**.

Deux clients, un seul serveur :
attention la génération des images il demande de rester connecter en ligne pendant 18 à 20  minutes et l'images est crée il sera placé automatique dans static 
même chose pour la voie de lecteur améliorer

| | |
|---|---|
| **Backend + site web** | Django 5 (`veh_project/`) — le jeu se joue dans le navigateur |
| **Application mobile** | Flutter (`veh_flutter/`) — Android / iOS, parle à la même API REST |

---

## Sommaire

1. [Démarrage en 2 minutes (Docker)](#1-démarrage-en-2-minutes-docker)
2. [Installation manuelle](#2-installation-manuelle-sans-docker)
3. [Configuration](#3-configuration)
4. [Jouer](#4-jouer)
5. [Écrire une histoire — l'interface Narrateur](#5-écrire-une-histoire--linterface-narrateur)
6. [Les images de scène](#6-les-images-de-scène)
7. [La narration audio](#7-la-narration-audio)
8. [L'application mobile](#8-lapplication-mobile-flutter)
9. [Commandes disponibles](#9-commandes-disponibles)
10. [Plan des URLs](#10-plan-des-urls)
11. [Structure du projet](#11-structure-du-projet)
12. [Dépannage](#12-dépannage)

---

## 1. Démarrage en 2 minutes (Docker)

C'est la voie recommandée : rien à installer à part Docker, et les trois
histoires d'exemple sont chargées toutes seules.

```bash
git clone <url-du-depot>
cd vouseteshero-main
docker compose up --build
```

Puis ouvrez **http://localhost:8000**.

Pour avoir un compte administrateur dès le démarrage, créez un fichier `.env`
à la racine (à côté de `docker-compose.yml`) avant de lancer :

```ini
DJANGO_SUPERUSER_USERNAME=patron
DJANGO_SUPERUSER_EMAIL=patron@exemple.fr
DJANGO_SUPERUSER_PASSWORD=un-mot-de-passe
```

> La base SQLite et les images générées sont conservées dans un volume Docker
> (`veh_data`) : elles survivent à `docker compose down`. Pour repartir de zéro :
> `docker compose down -v`.

---

## 2. Installation manuelle (sans Docker)

**Prérequis** : Python 3.12 ou plus.

```bash
git clone <url-du-depot>
cd vouseteshero-main/veh_project

# 1. Environnement isolé
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate

# 2. Dépendances
pip install -r requirements.txt

# 3. Configuration (voir §3 — le fichier existe déjà, il suffit de le relire)
#    veh_project/.env

# 4. Base de données
python manage.py migrate

# 5. Histoires d'exemple (facultatif mais conseillé)
python manage.py seed_fils_du_destin
python manage.py seed_chaperon_rouge
python manage.py seed_demo

# 6. Compte administrateur
python manage.py createsuperuser

# 7. Lancer
python manage.py runserver
```

Le site est sur **http://127.0.0.1:8000**.

> `python manage.py devserver` fait la même chose que `runserver`, avec une
> bannière au démarrage. Les deux acceptent les mêmes arguments.

---

## 3. Configuration

Deux fichiers `.env`, et il est facile de se tromper :

| Fichier | Lu par | À remplir quand |
|---|---|---|
| `veh_project/.env` | **Django en local** (`manage.py`) | installation manuelle |
| `.env` (racine) | **docker compose** | vous utilisez Docker |

Les réglages utiles :

```ini
# Django
DEBUG=True
SECRET_KEY=changez-moi-en-production
# Pour jouer depuis un téléphone du réseau local, ajoutez l'IP LAN du PC :
ALLOWED_HOSTS=localhost,127.0.0.1,10.0.2.2,192.168.1.20

# Clé Google Gemini — FACULTATIVE.
# Sans elle : voix du navigateur pour la narration, et prompts d'image
# extraits du texte. Avec elle : narration TTS et prompts nettement meilleurs.
# https://aistudio.google.com/apikey
GEMINI_API_KEY=

# Illustration des scènes (voir §6)
SCENE_IMAGE_AUTOGEN=1
SCENE_IMAGE_BACKEND=
SCENE_IMAGE_STYLE=
```

> **Ne mettez jamais votre clé dans `.env.example`** : ce fichier-là est suivi
> par git et finirait publié. Les `.env` réels sont ignorés.

**Tout le jeu fonctionne sans aucune clé API.** La clé n'améliore que la
qualité de la narration et des descriptions d'images.

---

## 4. Jouer

1. Créez un compte sur `/users/register/` (ou connectez-vous).
2. La page d'accueil liste les histoires publiées.
3. Cliquez, lisez, choisissez. La partie est sauvegardée : vous reprenez où
   vous en étiez.
4. Une fin atteinte, la page de fin récapitule le parcours. Les choix déjà
   empruntés sont signalés lors des parties suivantes, pour trouver les autres fins.

---

## 5. Écrire une histoire — l'interface Narrateur

**http://localhost:8000/narrateur/** — réservée aux comptes **administrateur**
(`is_staff`). Un lien « Narrateur » apparaît dans la barre du site pour eux.

C'est la façon prévue d'écrire ; l'admin Django (`/admin/`) reste disponible
pour les retouches ponctuelles.

### Le parcours

```
/narrateur/                    vos histoires, avec leur avancement
       │
       ▼
  Nouvelle histoire            titre, résumé, couverture
       │
       ▼
  ÉDITEUR DE SCÈNE                                    ┌──────────┐
  ├─ Texte de la scène                                │  Carte   │ ← en haut à droite
  ├─ Ambiance musicale + transition                   └──────────┘
  ├─ Les choix du joueur : de 1 à 4
  └─ Statut : scène de départ / scène de fin
       │
   [Enregistrer]  → l'image de fond est générée au passage
       │
       ▼
  LA SUITE — un encadré par choix
  ├─ « Créer la scène de ce choix → »   branche pas encore écrite
  └─ « Ouvrir la scène »                branche déjà écrite
```

Chaque nouvelle scène est **raccordée automatiquement** au choix d'où vous
venez. L'arbre se construit ainsi de proche en proche.

### Les règles appliquées

- **1 à 4 choix** par scène. Le bouton « + Ajouter un choix » révèle un
  emplacement de plus ; les emplacements laissés vides sont ignorés.
- **Une scène de fin n'a aucun choix**, et doit préciser son type (bonne,
  mauvaise, neutre). L'inverse est refusé : ni choix ni fin = impasse.
- **Une seule scène de départ** par histoire — en cocher une nouvelle décoche
  l'ancienne.
- **Vider le texte d'un choix le supprime.** La scène qu'il visait n'est pas
  détruite : elle devient orpheline et la carte vous la montre en pointillés,
  pour que vous puissiez la raccrocher.
- L'identifiant technique de la scène est **déduit du texte**. Vous pouvez le
  changer sous « Avancé ».

### La carte

Le bouton **Carte**, en haut à droite de l'éditeur, dessine l'arbre complet :

- vert = départ · bleu = scène · vert clair / rouge / ocre = bonne, mauvaise, neutre fin
- **pointillés ocres** = un choix qui ramène à une scène déjà vue (boucle)
- **contour en pointillés** = scène orpheline, qu'aucun choix n'atteint
- le compteur « à écrire » indique les branches encore vides

Chaque nœud est cliquable et ouvre la scène dans l'éditeur.

---

## 6. Les images de scène

À l'enregistrement d'une scène, son texte devient une image de fond, en deux
étapes :

```
texte narratif ──► prompt visuel ──► image ──► Scene.image ──► fond de scène
                                                               (web + mobile)
```

Chaque étape a un chemin **gratuit** et un chemin **premium** :

| Étape | Gratuit (par défaut) | Premium (avec `GEMINI_API_KEY`) |
|---|---|---|
| texte → prompt | extraction locale, hors ligne | Gemini écrit une vraie description |
| prompt → image | **pollinations** — sans clé, sans facturation | Gemini (facturation requise) |

Le basculement est automatique : dès que la clé est renseignée, l'étape 1
passe sur Gemini, sans toucher au code.

> ⚠️ **Le texte de vos scènes est envoyé à un service tiers** (pollinations)
> pour produire l'image. C'est le prix du « sans clé, sans facturation ». Si
> vos scénarios ne doivent pas quitter votre machine, mettez
> `SCENE_IMAGE_BACKEND=gemini` avec facturation activée, ou décochez
> « Générer l'illustration automatiquement » et fournissez vos propres images.

**Rien n'est jamais écrasé** : une image uploadée à la main, ou un fichier posé
dans `static/scenes/{scene_key}.jpg`, a la priorité et n'est pas remplacé.

Une image n'est régénérée que si le texte ou le prompt a changé — réenregistrer
une scène inchangée ne déclenche aucun appel réseau.

### En masse

```bash
# Aperçu : ce qui serait illustré, sans aucun appel réseau
python manage.py generate_scene_images --dry-run

# Illustrer une histoire entière
python manage.py generate_scene_images --story les-fils-du-destin

# Refaire une scène précise, avec une autre direction artistique
python manage.py generate_scene_images --scene prologue_matin --force \
    --style "aquarelle claire, traits doux"
```

Pour changer le rendu de **toutes** les scènes d'un coup, modifiez
`SCENE_IMAGE_STYLE` dans `.env` : c'est la direction artistique commune qui
rend les illustrations cohérentes entre elles.

---

## 7. La narration audio

Trois sources, dans cet ordre de priorité :

1. un fichier envoyé dans l'admin (champ « Narration audio ») ;
2. un fichier `static/narrations/{scene_key}.mp3` ;
3. sinon, synthèse à la volée par **Gemini TTS** (nécessite `GEMINI_API_KEY`),
   mise en cache dans `media/narration_cache/` ;
4. sinon, la **voix du navigateur** prend le relais — donc ça marche toujours.

Pour pré-générer tous les fichiers d'un coup :

```bash
python manage.py generate_narrations --story les-fils-du-destin
python manage.py generate_narrations --voice Charon --style "d'une voix grave"
```

Les musiques d'ambiance sont des MP3 dans `static/music/`, choisis par scène
parmi dix ambiances (calme, tension, horreur, combat…).

---

## 8. L'application mobile (Flutter)

**Prérequis** : Flutter SDK ≥ 3.0, Android Studio + un émulateur (ou un
téléphone), et le serveur Django démarré.

```bash
cd veh_flutter
flutter pub get
flutter run
```

L'app pointe par défaut sur `http://10.0.2.2:8000` — l'alias de « la machine
hôte » vu depuis l'émulateur Android. À adapter dans
[`lib/core/constants.dart`](veh_flutter/lib/core/constants.dart) :

| Cible | `baseUrl` |
|---|---|
| Émulateur Android | `http://10.0.2.2:8000` |
| Simulateur iOS | `http://localhost:8000` |
| Téléphone réel | `http://<IP-LAN-du-PC>:8000` |

Pour un téléphone réel, il faut aussi :
- lancer le serveur sur le réseau : `python manage.py runserver 0.0.0.0:8000` ;
- ajouter l'IP du PC à `ALLOWED_HOSTS` dans `veh_project/.env`.

Si les dossiers `android/` ou `ios/` manquent, ou si le HTTP en clair est
bloqué, suivez
[`veh_flutter/android_setup/INSTRUCTIONS.txt`](veh_flutter/android_setup/INSTRUCTIONS.txt).

---

## 9. Commandes disponibles

Toutes depuis `veh_project/`.

| Commande | Rôle |
|---|---|
| `runserver` / `devserver` | lance le serveur (`devserver` ajoute une bannière) |
| `migrate` | applique les migrations |
| `createsuperuser` | crée un compte administrateur (accès Narrateur + admin) |
| `seed_fils_du_destin` | charge l'histoire « Les Fils du Destin » |
| `seed_chaperon_rouge` | charge « Le Chaperon Rouge » |
| `seed_demo` | charge l'histoire de démonstration |

Les trois `seed_*` sont sans danger à relancer : si l'histoire existe déjà,
ils ne font rien. Ajoutez `--reset` pour la supprimer et la recréer — ce qui
efface aussi les scènes que vous auriez modifiées.
| `generate_scene_images` | illustre les scènes (`--dry-run`, `--story`, `--force`, `--style`) |
| `generate_narrations` | génère les narrations audio (`--voice`, `--style`) |
| `generate_narrations_demo` | idem, limité au chemin principal |

Ajoutez `--help` à n'importe laquelle pour voir toutes ses options.

---

## 10. Plan des URLs

**Site web**

| URL | Page |
|---|---|
| `/` | bibliothèque des histoires |
| `/users/register/`, `/users/login/`, `/users/profile/` | compte |
| `/play/<histoire>/<scene>/` | jouer une scène |
| `/play/<histoire>/ending/` | fin de partie |
| `/narrateur/` | **interface d'écriture** (administrateurs) |
| `/admin/` | administration Django |

**API REST** (consommée par Flutter, JWT)

| Méthode | URL |
|---|---|
| `POST` | `/api/auth/register/`, `/api/auth/login/`, `/api/auth/refresh/` |
| `GET` | `/api/auth/me/` |
| `GET` | `/api/stories/`, `/api/stories/<slug>/` |
| `GET` | `/api/play/<slug>/scene/<scene_key>/` |
| `POST` | `/api/play/<slug>/choose/` |
| `GET` | `/api/sessions/`, `/api/sessions/<slug>/history/` |

---

## 11. Structure du projet

```
vouseteshero-main/
├── docker-compose.yml          lancement en une commande
├── .env                        variables pour docker compose
│
├── veh_project/                BACKEND DJANGO
│   ├── .env                    variables lues par manage.py  ← à ne pas confondre
│   ├── config/settings/        base · development · docker · production
│   ├── apps/
│   │   ├── users/              compte joueur (AbstractUser étendu)
│   │   ├── stories/            histoires, scènes, choix
│   │   │   ├── models.py       Story · Scene · Choice
│   │   │   ├── views_web.py    le jeu côté navigateur
│   │   │   ├── views_narrator.py  l'interface Narrateur
│   │   │   ├── forms.py        formulaires d'écriture (1 à 4 choix)
│   │   │   ├── illustration.py déclencheur d'illustration (admin + Narrateur)
│   │   │   ├── services/
│   │   │   │   ├── image_service.py  texte → prompt → image
│   │   │   │   ├── story_map.py      disposition de l'arbre (SVG)
│   │   │   │   ├── tts_service.py    narration Gemini
│   │   │   │   └── gemini_service.py enrichissement narratif
│   │   │   └── management/commands/  seeds, générateurs, devserver
│   │   └── sessions/           parties en cours, historique des choix
│   ├── static/
│   │   ├── music/              ambiances MP3
│   │   ├── scenes/             images posées à la main
│   │   └── narrations/         narrations pré-générées
│   └── media/                  fichiers produits (images générées, cache TTS)
│
└── veh_flutter/                APPLICATION MOBILE
    ├── lib/core/constants.dart adresse du serveur  ← à adapter
    ├── lib/models/ screens/    écrans et modèles
    └── android_setup/          config réseau Android
```

---

## 12. Dépannage

**« GEMINI_API_KEY n'est pas configurée »**
Normal et sans gravité : le jeu bascule sur les chemins gratuits. Si vous
*voulez* la clé, vérifiez que vous l'avez mise dans **`veh_project/.env`** (pas
dans celui de la racine, ni dans `.env.example`).

**Les images ne se génèrent pas**
Lancez `python manage.py generate_scene_images --dry-run` : il dit quelles
scènes seraient traitées. Une scène qui a déjà un visuel dans `static/scenes/`
est volontairement ignorée. Vérifiez aussi que « Générer l'illustration
automatiquement » est coché sur la scène.

**« quota limite = 0 » sur les modèles `*-image`**
La génération d'images Gemini n'est pas incluse dans le palier gratuit. Restez
sur le backend gratuit (`SCENE_IMAGE_BACKEND=` vide) ou activez la facturation.

**L'app Flutter n'atteint pas le serveur**
Trois causes, dans l'ordre : `baseUrl` mal réglée (§8), serveur lancé sur
`127.0.0.1` au lieu de `0.0.0.0`, ou IP absente de `ALLOWED_HOSTS`.

**`DisallowedHost` dans le navigateur**
Ajoutez l'hôte utilisé à `ALLOWED_HOSTS` dans `veh_project/.env`.

**Accents et cadres illisibles dans la console Windows**
Console en cp1252. Les commandes du projet retombent d'elles-mêmes sur une
sortie ASCII ; pour le rendu complet, utilisez Windows Terminal ou lancez
`chcp 65001`.

**Repartir d'une base vide**
Supprimez `veh_project/db.sqlite3`, puis rejouez `migrate` et les `seed_*`.
En Docker : `docker compose down -v`.

---

## Notes

- Le projet est prévu pour le développement et la démonstration : `DEBUG=True`,
  SQLite, et la validation des mots de passe est désactivée. Avant une mise en
  ligne réelle, il faut au minimum une `SECRET_KEY` neuve, `DEBUG=False`, une
  vraie base et le rétablissement des validateurs de mot de passe.
- Django 5 · Django REST Framework · JWT · Pillow · WhiteNoise · Flutter 3.
