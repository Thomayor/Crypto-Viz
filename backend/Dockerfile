# =====================================
# CRYPTO VIZ - Backend API Service
# =====================================

FROM python:3.11-slim

# Métadonnées
LABEL maintainer="crypto-viz-team"
LABEL version="1.0"
LABEL description="FastAPI Backend pour CRYPTO VIZ"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

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
    && rm -rf /var/lib/apt/lists/*

# Création de l'utilisateur non-root
RUN groupadd -r backend && useradd -r -g backend backend

# Définir le répertoire de travail
WORKDIR /app

# Copier les requirements en premier pour le cache Docker
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copier le code source
COPY . .

# Créer les répertoires nécessaires et rendre le script executable
RUN mkdir -p /app/data /app/logs /app/static && \
    chmod +x /app/entrypoint.sh && \
    chown -R backend:backend /app

# Passer à l'utilisateur non-root
USER backend

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Port d'exposition
EXPOSE 8000

# Variables d'environnement par défaut
ENV HOST=0.0.0.0
ENV PORT=8000
ENV LOG_LEVEL=INFO

# Point d'entrée
ENTRYPOINT ["/app/entrypoint.sh"]