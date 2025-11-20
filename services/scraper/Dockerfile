# =====================================
# CRYPTO VIZ - Web Scraper Service
# =====================================

FROM python:3.11-slim

# Métadonnées
LABEL maintainer="crypto-viz-team"
LABEL version="1.0"
LABEL description="Service de scraping pour données cryptomonnaies"

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
RUN groupadd -r scraper && useradd -r -g scraper scraper

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
RUN mkdir -p /app/data /app/logs /app/config && \
    chown -R scraper:scraper /app

# Copier les fichiers de configuration par défaut
COPY config/ /app/config/

# Script de démarrage
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Passer à l'utilisateur non-root
USER scraper

# Health check - temporarily disabled for debugging
# HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
#     CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Port d'exposition (pour health check)
EXPOSE 8000

# Point d'entrée
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "crypto_news_scraper.py"]