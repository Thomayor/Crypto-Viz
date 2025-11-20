#!/bin/bash

# =====================================
# CRYPTO VIZ - Installation Script
# =====================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

error() {
    echo -e "${RED}❌${NC} $1"
}

echo -e "${BLUE}"
echo "=================================================="
echo "    CRYPTO VIZ - Installation Setup"
echo "=================================================="
echo -e "${NC}"

# Check if .env file exists
log "Vérification du fichier .env..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        log "Création de .env depuis .env.example..."
        cp .env.example .env
        success ".env créé depuis le template"
        warning "⚠️ Veuillez configurer vos clés API dans le fichier .env"
        warning "⚠️ Le système fonctionnera en mode démo sans clés API"
    else
        error ".env.example non trouvé ! Impossible de créer .env"
        exit 1
    fi
else
    success ".env existe déjà"
fi

# Make scripts executable
log "Rendant les scripts exécutables..."
chmod +x scripts/*.sh
success "Scripts rendus exécutables"

# Create necessary directories
log "Création des répertoires nécessaires..."
mkdir -p data/{analytics,parquet,scraping}
mkdir -p logs
mkdir -p services/{scraper,analytics}/config
mkdir -p backend/static
mkdir -p frontend/dist

success "Répertoires créés"

# Check Docker daemon
log "Vérification du daemon Docker..."
if ! docker info &> /dev/null; then
    error "Docker daemon n'est pas démarré!"
    echo "Veuillez démarrer Docker Desktop et réessayer."
    exit 1
fi
success "Docker daemon opérationnel"

# Check available space
log "Vérification de l'espace disque..."
if command -v df &> /dev/null; then
    AVAILABLE_SPACE=$(df . | awk 'NR==2 {print $4}' 2>/dev/null || echo "5242880")
    AVAILABLE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
    
    if [ $AVAILABLE_GB -gt 5 ]; then
        success "Espace disque suffisant (${AVAILABLE_GB}GB disponible)"
    else
        warning "Espace disque limité (${AVAILABLE_GB}GB disponible)"
        warning "5GB minimum recommandé pour les modèles Ollama"
    fi
else
    warning "Impossible de vérifier l'espace disque sur ce système"
fi

echo ""
echo -e "${GREEN}"
echo "=================================================="
echo "    ✅ INSTALLATION TERMINÉE AVEC SUCCÈS!"
echo "=================================================="
echo -e "${NC}"

echo "📝 Prochaines étapes:"
echo "  1. Configurer .env si nécessaire (optionnel pour la démo)"
echo "  2. Démarrer avec: ./scripts/start.sh"
echo "  3. Ou utiliser make si installé: make start"
echo ""
echo "🔍 Validation:"
echo "  • Run './scripts/validate-setup.sh' pour vérifier"
echo "  • Run './scripts/health-check.sh' après démarrage"
echo ""
echo "🌐 Une fois démarré, accédez à:"
echo "  • Dashboard: http://localhost:3000"
echo "  • API: http://localhost:8000"
echo ""