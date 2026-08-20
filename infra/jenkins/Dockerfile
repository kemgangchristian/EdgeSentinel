# *******************************************************
# infra/jenkins/Dockerfile
#
# Étend l'image officielle Jenkins pour y ajouter le client Docker (CLI).
# Nécessaire pour que les stages Jenkinsfile utilisant "agent { docker {...} }"
# ou "docker build" puissent piloter le démon Docker de la machine hôte
# (via /var/run/docker.sock, déjà monté dans docker-compose.yml).
# *******************************************************

FROM jenkins/jenkins:lts-jdk17

# Passage root temporaire pour installer un paquet système - Jenkins revient
# à un utilisateur non-root ensuite (bonne pratique de sécurité standard).
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" \
        > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# Retour à l'utilisateur non-root standard de l'image Jenkins.
USER jenkins
