#!/bin/sh
# ─────────────────────────────────────────────────────────────
#  Démarrage du conteneur VEH : prépare la base puis lance le serveur.
#  Idempotent : peut être relancé sans risque (les seeds se sautent
#  si l'histoire existe déjà).
# ─────────────────────────────────────────────────────────────
set -e

DATA_DIR="${VEH_DATA_DIR:-/data}"
mkdir -p "$DATA_DIR/media"

echo "[VEH] Application des migrations..."
python manage.py migrate --noinput

echo "[VEH] Chargement des histoires (ignore si deja presentes)..."
python manage.py seed_fils_du_destin || true
python manage.py seed_chaperon_rouge || true
python manage.py seed_demo || true

# Superuser optionnel : uniquement si les variables sont fournies.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "[VEH] Creation du superuser (si absent)..."
    python manage.py createsuperuser --noinput || true
fi

echo "[VEH] Serveur pret sur http://localhost:8000"
exec "$@"
