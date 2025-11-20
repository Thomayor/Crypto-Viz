# =====================================
# CRYPTO VIZ - Analytics Service
# =====================================

FROM python:3.11-slim-bookworm

# Métadonnées
LABEL maintainer="crypto-viz-team"
LABEL version="1.0"
LABEL description="Service d'analytics avec Ollama, Spark et DuckDB"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    libssl-dev \
    openjdk-17-jdk \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Création de l'utilisateur non-root
RUN groupadd -r analytics && useradd -r -g analytics analytics

# Définir le répertoire de travail
WORKDIR /app

# Copier les requirements en premier pour le cache Docker
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copier le code source
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/data /app/logs /app/config /app/models && \
    chown -R analytics:analytics /app

# Copier les fichiers de configuration par défaut
COPY config/ /app/config/

# Script de démarrage
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Passer à l'utilisateur non-root
# USER analytics  # Temporarily disabled for Bootstrap demo - volume permission issues

# Health check
HEALTHCHECK --interval=60s --timeout=15s --start-period=120s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health', timeout=10)"

# Port d'exposition (pour health check)
EXPOSE 8001

# Point d'entrée
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "analytics_processor.py"]