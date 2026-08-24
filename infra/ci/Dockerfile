# =============================================================================
# infra/ci/Dockerfile
#
# Image dédiée à l'exécution des tests de l'agent Edge dans Jenkins.
# Étend python:3.11-slim avec les bibliothèques système nécessaires à
# opencv-python-headless (libGL, requis par le chargement interne d'OpenCV
# même en mode headless, sur une base Debian minimale).
# =============================================================================

FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*
