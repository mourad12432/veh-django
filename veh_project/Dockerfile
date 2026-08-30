# ─────────────────────────────────────────────────────────────
#  VEH — Backend Django (image autonome : SQLite + assets inclus)
#  Build : docker build -t veh-web .
#  Run   : voir docker-compose.yml à la racine
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.docker \
    VEH_DATA_DIR=/data

WORKDIR /app

# 1) Dépendances Python (couche cache séparée du code)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Code source + assets (images de scènes, narrations, musiques)
COPY . .

# 3) Script de démarrage + dossier de données
RUN chmod +x docker/entrypoint.sh && mkdir -p /data/media

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
