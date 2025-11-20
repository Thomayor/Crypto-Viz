#!/bin/bash

# =====================================
# CRYPTO VIZ - Setup Validation Script
# =====================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅${NC} $1"
    ((PASSED++))
}

error() {
    echo -e "${RED}❌${NC} $1"
    ((FAILED++))
}

warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
    ((WARNINGS++))
}

info() {
    echo -e "${PURPLE}ℹ️${NC} $1"
}

echo -e "${BLUE}"
echo "=================================================================="
echo "    CRYPTO VIZ - Validation Complète du Setup Docker"
echo "=================================================================="
echo -e "${NC}"

log "Démarrage de la validation complète..."
echo ""

# ===========================================
# 1. VALIDATION DE L'ENVIRONNEMENT
# ===========================================

log "🔍 Phase 1: Validation de l'environnement"
echo "----------------------------------------"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    success "Docker installé (version: $DOCKER_VERSION)"
    
    if docker info &> /dev/null; then
        success "Docker daemon est démarré"
    else
        error "Docker daemon n'est pas démarré"
    fi
else
    error "Docker n'est pas installé"
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    success "Docker Compose installé (version: $COMPOSE_VERSION)"
else
    error "Docker Compose n'est pas installé"
fi

# Check available space
AVAILABLE_SPACE=$(df . | awk 'NR==2 {print $4}')
AVAILABLE_GB=$((AVAILABLE_SPACE / 1024 / 1024))

if [ $AVAILABLE_GB -gt 10 ]; then
    success "Espace disque suffisant (${AVAILABLE_GB}GB disponible)"
elif [ $AVAILABLE_GB -gt 5 ]; then
    warning "Espace disque limité (${AVAILABLE_GB}GB disponible, 10GB recommandé)"
else
    error "Espace disque insuffisant (${AVAILABLE_GB}GB disponible, minimum 5GB requis)"
fi

# Check RAM
TOTAL_RAM=$(free -g | awk 'NR==2{printf "%d", $2}')
if [ $TOTAL_RAM -gt 8 ]; then
    success "RAM suffisante (${TOTAL_RAM}GB total)"
elif [ $TOTAL_RAM -gt 4 ]; then
    warning "RAM limitée (${TOTAL_RAM}GB total, 8GB recommandé)"
else
    error "RAM insuffisante (${TOTAL_RAM}GB total, minimum 8GB requis)"
fi

echo ""

# ===========================================
# 2. VALIDATION DES FICHIERS
# ===========================================

log "📁 Phase 2: Validation des fichiers du projet"
echo "-------------------------------------------"

# Required files
REQUIRED_FILES=(
    "docker-compose.yml"
    ".env.example"
    "Makefile"
    "README.md"
    "services/scraper/Dockerfile"
    "services/scraper/requirements.txt"
    "services/scraper/entrypoint.sh"
    "services/analytics/Dockerfile"
    "services/analytics/requirements.txt"
    "services/analytics/entrypoint.sh"
    "backend/Dockerfile"
    "backend/requirements.txt"
    "frontend/Dockerfile"
    "frontend/nginx.conf"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "Fichier présent: $file"
    else
        error "Fichier manquant: $file"
    fi
done

# Check if .env exists
if [ -f ".env" ]; then
    success "Fichier .env configuré"
else
    warning "Fichier .env manquant (sera créé lors de l'installation)"
fi

# Check scripts permissions
SCRIPTS=(
    "scripts/start.sh"
    "scripts/stop.sh"
    "scripts/restart.sh"
    "scripts/dev.sh"
    "scripts/health-check.sh"
    "scripts/validate-setup.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            success "Script exécutable: $script"
        else
            warning "Script non exécutable: $script (sera corrigé par make install)"
        fi
    else
        error "Script manquant: $script"
    fi
done

echo ""

# ===========================================
# 3. VALIDATION DOCKER COMPOSE
# ===========================================

log "🐳 Phase 3: Validation de la configuration Docker Compose"
echo "-------------------------------------------------------"

# Validate docker-compose.yml syntax
if docker-compose config &> /dev/null; then
    success "Syntaxe docker-compose.yml valide"
else
    error "Erreur dans la syntaxe docker-compose.yml"
    docker-compose config 2>&1 | head -5
fi

# Check networks configuration
NETWORKS=$(docker-compose config | grep -A 5 "networks:" | grep -E "^\s+[a-z-]+:" | wc -l)
if [ $NETWORKS -gt 0 ]; then
    success "Réseaux Docker configurés ($NETWORKS réseaux)"
else
    warning "Aucun réseau Docker personnalisé configuré"
fi

# Check volumes configuration
VOLUMES=$(docker-compose config | grep -A 10 "volumes:" | grep -E "^\s+[a-z_-]+:" | wc -l)
if [ $VOLUMES -gt 0 ]; then
    success "Volumes Docker configurés ($VOLUMES volumes)"
else
    error "Aucun volume Docker configuré"
fi

# Check services
SERVICES=$(docker-compose config --services | wc -l)
if [ $SERVICES -gt 8 ]; then
    success "Services Docker configurés ($SERVICES services)"
else
    warning "Peu de services configurés ($SERVICES services)"
fi

echo ""

# ===========================================
# 4. VALIDATION BOOTSTRAP STACK
# ===========================================

log "📊 Phase 4: Validation du Stack Bootstrap EPITECH"
echo "------------------------------------------------"

# Check pandas in requirements
if grep -q "pandas" services/analytics/requirements.txt; then
    success "Bootstrap: pandas configuré dans analytics"
else
    error "Bootstrap: pandas manquant dans analytics/requirements.txt"
fi

if grep -q "pandas" backend/requirements.txt; then
    success "Bootstrap: pandas configuré dans backend"
else
    error "Bootstrap: pandas manquant dans backend/requirements.txt"
fi

# Check DuckDB
if grep -q "duckdb" services/analytics/requirements.txt; then
    success "Bootstrap: DuckDB configuré dans analytics"
else
    error "Bootstrap: DuckDB manquant dans analytics/requirements.txt"
fi

if grep -q "duckdb" backend/requirements.txt; then
    success "Bootstrap: DuckDB configuré dans backend"
else
    error "Bootstrap: DuckDB manquant dans backend/requirements.txt"
fi

# Check Spark configuration
if docker-compose config | grep -q "spark-master"; then
    success "Bootstrap: Spark Master configuré"
else
    error "Bootstrap: Spark Master manquant"
fi

if docker-compose config | grep -q "spark-worker"; then
    WORKERS=$(docker-compose config | grep -c "spark-worker")
    success "Bootstrap: Spark Workers configurés ($WORKERS workers)"
else
    error "Bootstrap: Spark Workers manquants"
fi

# Check if pyspark is in requirements
if grep -q "pyspark" services/analytics/requirements.txt; then
    success "Bootstrap: PySpark configuré"
else
    error "Bootstrap: PySpark manquant dans analytics/requirements.txt"
fi

echo ""

# ===========================================
# 5. VALIDATION DE L'ARCHITECTURE
# ===========================================

log "🏗️ Phase 5: Validation de l'architecture"
echo "----------------------------------------"

# Expected services
EXPECTED_SERVICES=(
    "zookeeper"
    "kafka"
    "ollama"
    "spark-master"
    "spark-worker-1"
    "spark-worker-2"
    "web-scraper"
    "analytics-builder"
    "backend"
    "frontend"
    "kafka-ui"
)

COMPOSE_SERVICES=$(docker-compose config --services)

for service in "${EXPECTED_SERVICES[@]}"; do
    if echo "$COMPOSE_SERVICES" | grep -q "^$service$"; then
        success "Service architecture: $service"
    else
        error "Service manquant: $service"
    fi
done

# Check health checks
HEALTHCHECKS=$(docker-compose config | grep -c "healthcheck:")
if [ $HEALTHCHECKS -gt 5 ]; then
    success "Health checks configurés ($HEALTHCHECKS services)"
else
    warning "Peu de health checks configurés ($HEALTHCHECKS services)"
fi

# Check dependencies
DEPENDS_ON=$(docker-compose config | grep -c "depends_on:")
if [ $DEPENDS_ON -gt 3 ]; then
    success "Dépendances services configurées ($DEPENDS_ON dépendances)"
else
    warning "Peu de dépendances configurées ($DEPENDS_ON dépendances)"
fi

echo ""

# ===========================================
# 6. VALIDATION AVANCÉE
# ===========================================

log "🔬 Phase 6: Validation avancée"
echo "-----------------------------"

# Check port configurations
EXPOSED_PORTS=$(docker-compose config | grep -E "^\s+- \"[0-9]+:" | wc -l)
if [ $EXPOSED_PORTS -gt 5 ]; then
    success "Ports exposés configurés ($EXPOSED_PORTS ports)"
else
    warning "Peu de ports exposés ($EXPOSED_PORTS ports)"
fi

# Check environment variables
ENV_VARS=$(docker-compose config | grep -c "environment:")
if [ $ENV_VARS -gt 8 ]; then
    success "Variables d'environnement configurées ($ENV_VARS services avec env)"
else
    warning "Peu de variables d'environnement ($ENV_VARS services avec env)"
fi

# Check volumes mounts
VOLUME_MOUNTS=$(docker-compose config | grep -E "^\s+- \./|^\s+- [a-z_-]+:" | wc -l)
if [ $VOLUME_MOUNTS -gt 10 ]; then
    success "Montages volumes configurés ($VOLUME_MOUNTS montages)"
else
    warning "Peu de montages volumes ($VOLUME_MOUNTS montages)"
fi

# Check restart policies
RESTART_POLICIES=$(docker-compose config | grep -c "restart:")
if [ $RESTART_POLICIES -gt 8 ]; then
    success "Politiques de redémarrage configurées ($RESTART_POLICIES services)"
else
    warning "Peu de politiques de redémarrage ($RESTART_POLICIES services)"
fi

echo ""

# ===========================================
# 7. RECOMMANDATIONS
# ===========================================

log "💡 Phase 7: Recommandations et conseils"
echo "--------------------------------------"

info "Configuration système recommandée:"
echo "   • RAM: 16GB (minimum 8GB)"
echo "   • CPU: 8 cores (minimum 4 cores)"
echo "   • Stockage: SSD avec 20GB libres"
echo "   • Réseau: Connexion stable pour téléchargements"
echo ""

info "Avant le premier démarrage:"
echo "   1. Exécuter: make install"
echo "   2. Configurer .env avec vos clés API"
echo "   3. Démarrer avec: make quick-start"
echo "   4. Vérifier avec: make health"
echo ""

info "Monitoring recommandé:"
echo "   • make status - État des conteneurs"
echo "   • make logs - Logs en temps réel"
echo "   • http://localhost:8081 - Kafka UI"
echo "   • http://localhost:8080 - Spark UI"
echo ""

# ===========================================
# 8. RÉSUMÉ FINAL
# ===========================================

echo ""
echo "=================================================================="
log "🎯 RÉSUMÉ DE LA VALIDATION"
echo "=================================================================="

echo -e "${GREEN}✅ Tests réussis:${NC} $PASSED"
echo -e "${YELLOW}⚠️  Avertissements:${NC} $WARNINGS"
echo -e "${RED}❌ Tests échoués:${NC} $FAILED"

echo ""

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}"
        echo "🎉 VALIDATION PARFAITE! 🎉"
        echo "Votre setup CRYPTO VIZ est optimal et prêt à être déployé!"
        echo ""
        echo "Prochaines étapes:"
        echo "  1. make install"
        echo "  2. make quick-start"
        echo "  3. Ouvrir http://localhost:3000"
        echo -e "${NC}"
    else
        echo -e "${YELLOW}"
        echo "✅ VALIDATION RÉUSSIE avec avertissements"
        echo "Votre setup fonctionnera, mais quelques optimisations sont recommandées."
        echo ""
        echo "Prochaines étapes:"
        echo "  1. make install"
        echo "  2. make quick-start"
        echo "  3. Surveiller les logs: make logs"
        echo -e "${NC}"
    fi
elif [ $FAILED -le 2 ]; then
    echo -e "${YELLOW}"
    echo "⚠️ VALIDATION PARTIELLE"
    echo "Quelques problèmes mineurs détectés, mais le démarrage devrait fonctionner."
    echo ""
    echo "Actions recommandées:"
    echo "  1. Corriger les erreurs ci-dessus"
    echo "  2. make install"
    echo "  3. make start (surveiller les logs)"
    echo -e "${NC}"
else
    echo -e "${RED}"
    echo "❌ VALIDATION ÉCHOUÉE"
    echo "Plusieurs problèmes critiques détectés. Correction nécessaire avant démarrage."
    echo ""
    echo "Actions requises:"
    echo "  1. Corriger toutes les erreurs listées"
    echo "  2. Réexécuter ce script"
    echo "  3. Contacter l'équipe si problèmes persistent"
    echo -e "${NC}"
fi

echo ""
echo "=================================================================="
log "Validation terminée à $(date)"
echo "=================================================================="

# Exit with appropriate code
if [ $FAILED -eq 0 ]; then
    exit 0
elif [ $FAILED -le 2 ]; then
    exit 1  # Warnings
else
    exit 2  # Critical errors
fi