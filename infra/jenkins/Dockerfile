# *******************************************************
# infra/jenkins/Dockerfile
#
# Étend l'image officielle Jenkins pour y ajouter :
# - le client Docker (CLI), pour piloter le démon Docker de la machine
#   hôte via /var/run/docker.sock (déjà monté dans docker-compose.yml)
# - Java 17 + Maven, installés DIRECTEMENT dans cette image plutôt que
#   dans un sous-conteneur Docker séparé -- évite un Docker-in-Docker à
#   plusieurs niveaux, source de multiples problèmes avec Testcontainers
#   (self-détection du conteneur, résolution réseau des conteneurs
#   éphémères créés pendant les tests).
# *******************************************************

FROM jenkins/jenkins:lts-jdk17

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        maven && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" \
        > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

RUN usermod -aG root jenkins

USER jenkins