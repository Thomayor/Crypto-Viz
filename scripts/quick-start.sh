#!/bin/bash

# =====================================
# CRYPTO VIZ - Quick Start Script
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

error() {
    echo -e "${RED}❌${NC} $1"
}

echo -e "${BLUE}"
echo "=================================================="
echo "    CRYPTO VIZ - Démarrage Rapide Complet"
echo "=================================================="
echo -e "${NC}"

log "Démarrage du processus d'installation et de lancement complet..."

# Step 1: Install
log "🔧 Étape 1/3: Installation et configuration initiale"
echo "---------------------------------------------------"
./scripts/install.sh

# Step 2: Build
log "🏗️ Étape 2/3: Construction des images Docker"
echo "--------------------------------------------"
echo "Cette étape peut prendre 10-15 minutes la première fois..."
echo ""

docker-compose build --parallel
success "Images Docker construites avec succès"

# Step 3: Start
log "🚀 Étape 3/3: Démarrage de tous les services"
echo "--------------------------------------------"
./scripts/start.sh

echo ""
echo -e "${GREEN}"
echo "=================================================="
echo "    🎉 CRYPTO VIZ DÉMARRÉ AVEC SUCCÈS!"
echo "=================================================="
echo -e "${NC}"

echo "🌐 Accès aux services:"
echo "  • Dashboard Principal: http://localhost:3000"
echo "  • API Backend:         http://localhost:8000"
echo "  • Documentation API:   http://localhost:8000/docs"
echo "  • Kafka UI:            http://localhost:8081"
echo "  • Spark Master UI:     http://localhost:8080"
echo ""

echo "🔍 Vérification:"
echo "  • Lancer './scripts/health-check.sh' pour un diagnostic complet"
echo "  • Voir les logs: 'docker-compose logs -f'"
echo ""

echo "🛠️ Gestion:"
echo "  • Arrêter: './scripts/stop.sh'"
echo "  • Redémarrer: './scripts/restart.sh'"
echo "  • Mode dev: './scripts/dev.sh'"
echo ""

echo -e "${BLUE}🎯 Le système est maintenant opérationnel!${NC}"