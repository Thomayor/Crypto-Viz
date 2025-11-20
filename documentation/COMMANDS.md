# 📖 Référence Complète des Commandes - Crypto Viz

Guide de référence rapide de toutes les commandes disponibles pour gérer l'application Crypto Viz.

---

## 🚀 Installation & Démarrage

### Installation Initiale

```bash
make install
```
**Description** : Configuration initiale du projet
- Crée le fichier `.env` depuis `.env.example`
- Configure les répertoires nécessaires
- Rend les scripts exécutables
- **À exécuter une seule fois** lors de la première installation

---

### Démarrage Rapide

```bash
make quick-start
```
**Description** : Démarrage complet en une commande
- Exécute `make install`
- Build toutes les images Docker
- Démarre tous les services
- **Commande idéale pour un déploiement complet**

---

### Démarrage Standard

```bash
make start
```
**Description** : Démarre tous les services avec séquençage intelligent
- Démarre les services dans le bon ordre (Zookeeper → Kafka → Ollama → Spark → Apps)
- Attend que chaque service soit prêt avant de démarrer le suivant
- **Commande à utiliser pour démarrer l'application quotidiennement**

---

### Build des Images

```bash
make build
```
**Description** : Construit toutes les images Docker
- Rebuild backend, frontend, scraper, analytics
- Nécessaire après modification des Dockerfiles ou requirements.txt
- **À exécuter avant de redémarrer après des changements de dépendances**

---

## 🛑 Arrêt & Redémarrage

### Arrêt des Services

```bash
make stop
```
**Description** : Arrête tous les services proprement
- Arrête tous les conteneurs Docker
- Préserve les données et volumes
- **Commande pour arrêter l'application en fin de journée**

---

### Redémarrage Simple

```bash
make restart
```
**Description** : Redémarre tous les services
- Équivalent à `make stop` + `make start`
- Préserve les données
- **Commande pour appliquer des changements de configuration**

---

### Redémarrage avec Nettoyage

```bash
make restart-clean
```
**Description** : Redémarre avec nettoyage des volumes
- Supprime les volumes de données
- Redémarre de zéro
- **⚠️ ATTENTION : Perte des données temporaires**
- **Utile pour résoudre des problèmes de données corrompues**

---

### Redémarrage Complet

```bash
make restart-full
```
**Description** : Rebuild complet et redémarrage
- Rebuild toutes les images
- Nettoie les volumes
- Redémarre tous les services
- **⚠️ ATTENTION : Perte de données**
- **Commande pour changements majeurs de code**

---

## 💻 Développement

### Mode Développement (Tous Services)

```bash
make dev
```
**Description** : Démarre l'environnement de développement
- Hot-reload activé sur tous les services
- Logs en temps réel
- **Mode principal pour le développement**

---

### Mode Développement Backend

```bash
make dev-backend
```
**Description** : Backend FastAPI avec hot-reload
- Redémarrage automatique à chaque modification de code Python
- Logs backend en direct
- Port 8000
- **Utile pour développer l'API**

---

### Mode Développement Frontend

```bash
make dev-frontend
```
**Description** : Frontend Vue.js avec hot-reload
- Rechargement automatique du navigateur
- Logs Vite en direct
- Port 3000
- **Utile pour développer l'interface**

---

### Mode Développement Analytics

```bash
make dev-analytics
```
**Description** : Service analytics avec hot-reload
- Redémarrage automatique à chaque modification
- Logs analytics en direct
- **Utile pour développer les pipelines de données**

---

### Mode Développement Scraper

```bash
make dev-scraper
```
**Description** : Service scraper avec hot-reload
- Redémarrage automatique à chaque modification
- Logs scraper en direct
- **Utile pour développer la collecte de données**

---

### Shell de Développement

```bash
make dev-shell
```
**Description** : Shell interactif dans un conteneur
- Accès direct aux conteneurs
- Debugging interactif
- **Utile pour inspecter l'environnement**

---

## 📊 Monitoring & Logs

### Health Check Complet

```bash
make health
```
**Description** : Vérifie l'état de tous les services
- Status des conteneurs
- Santé des endpoints
- Topics Kafka
- Modèles Ollama
- Cluster Spark
- Volumes de données
- **Commande de diagnostic principale**

---

### Status des Conteneurs

```bash
make status
```
**Description** : Affiche l'état et l'utilisation des ressources
- Liste des conteneurs actifs
- CPU et Memory usage
- **Vue d'ensemble rapide du système**

---

### Logs de Tous les Services

```bash
make logs
```
**Description** : Affiche les logs de tous les services
- Logs combinés en temps réel
- Suit les nouveaux logs (tail -f)
- **Ctrl+C pour quitter**

---

### Logs Backend

```bash
make logs-backend
```
**Description** : Logs du service backend uniquement
- FastAPI logs
- Requêtes HTTP
- Erreurs backend

---

### Logs Frontend

```bash
make logs-frontend
```
**Description** : Logs du service frontend
- Nginx logs
- Erreurs de build
- Requêtes HTTP

---

### Logs Kafka

```bash
make logs-kafka
```
**Description** : Logs du broker Kafka
- État des topics
- Erreurs de connexion
- Réplication

---

### Logs Zookeeper

```bash
make logs-zookeeper
```
**Description** : Logs de Zookeeper
- Coordination Kafka
- État du cluster

---

### Logs Ollama

```bash
make logs-ollama
```
**Description** : Logs du service Ollama AI
- Téléchargement du modèle
- Inférences
- Erreurs IA

---

### Logs Spark

```bash
make logs-spark
```
**Description** : Logs du cluster Spark
- Spark Master
- Workers
- Jobs ML

---

### Logs Analytics

```bash
make logs-analytics
```
**Description** : Logs du service analytics
- Pipeline de traitement
- Bootstrap stack (pandas, DuckDB, Spark)
- Erreurs de traitement

---

### Logs Scraper

```bash
make logs-scraper
```
**Description** : Logs du service scraper
- Collecte de données
- Appels API
- Rate limiting

---

## 🗄️ Base de Données & Stockage

### Accès DuckDB

```bash
make duckdb
```
**Description** : Ouvre le CLI DuckDB
- Connexion à la base de données analytique
- Requêtes SQL interactives
- **Exemple** : `SELECT * FROM prices LIMIT 10;`
- `.quit` pour sortir

---

### Liste des Volumes

```bash
docker volume ls
```
**Description** : Liste tous les volumes Docker
- `shared_data` - Données partagées
- `duckdb_data` - Base DuckDB
- `kafka_data` - Topics Kafka
- `ollama_data` - Modèles IA
- `spark_data` - Données Spark

---

## 📡 Kafka

### Liste des Topics Kafka

```bash
make kafka-topics
```
**Description** : Affiche tous les topics Kafka
- Liste des topics
- Partitions
- Réplication
- Configuration

---

### Créer les Topics Kafka

```bash
./scripts/kafka-topics-setup.sh
```
**Description** : Crée tous les topics nécessaires
- crypto-news (3 partitions, 7j)
- crypto-prices (6 partitions, 30j)
- analytics-data (3 partitions, 14j)
- alerts (2 partitions, 3j)
- DLQ topics
- **Exécution automatique au premier démarrage**

---

### Kafka UI

```bash
make kafka-ui
```
**Description** : Ouvre l'interface Kafka UI dans le navigateur
- URL : http://localhost:8085
- Monitoring des topics
- Inspection des messages
- Gestion des consumer groups

---

## ⚡ Spark

### Spark UI

```bash
make spark-ui
```
**Description** : Ouvre l'interface Spark Master dans le navigateur
- URL : http://localhost:8082
- État du cluster
- Jobs en cours
- Workers connectés

---

### Spark Worker 1 UI

```bash
make spark-worker-1
```
**Description** : Interface Spark Worker 1
- URL : http://localhost:8083

---

### Spark Worker 2 UI

```bash
make spark-worker-2
```
**Description** : Interface Spark Worker 2
- URL : http://localhost:8084

---

## 🧪 Tests

### Tests Complets

```bash
make test
```
**Description** : Exécute tous les tests
- Tests backend
- Tests analytics
- Tests scraper
- **À exécuter avant chaque commit**

---

### Tests Backend

```bash
make test-backend
```
**Description** : Tests du backend uniquement
- Tests unitaires FastAPI
- Tests d'intégration API
- Tests endpoints

---

### Tests Analytics

```bash
make test-analytics
```
**Description** : Tests du service analytics
- Tests pipeline pandas
- Tests requêtes DuckDB
- Tests modèles Spark

---

### Tests Scraper

```bash
make test-scraper
```
**Description** : Tests du scraper
- Tests collecte données
- Tests rate limiting
- Tests validation

---

## 🔧 Utilitaires

### Afficher Toutes les URLs

```bash
make urls
```
**Description** : Affiche toutes les URLs d'accès aux services
- Dashboard principal
- Backend API
- Kafka UI
- Spark UI
- Ollama
- Monitoring

---

### Ouvrir le Dashboard

```bash
make open
```
**Description** : Ouvre le dashboard dans le navigateur
- URL : http://localhost:3000
- Interface principale de l'application

---

### Version & Info

```bash
make version
```
**Description** : Affiche les informations de version
- Version Docker
- Version Docker Compose
- Version des images

---

### Validation de la Configuration

```bash
make config
```
**Description** : Valide la configuration Docker Compose
- Vérifie la syntaxe YAML
- Affiche la configuration résolue

---

### Vérification de l'Environnement

```bash
make env-check
```
**Description** : Vérifie les variables d'environnement
- Présence du fichier .env
- Variables requises
- Configuration valide

---

## 🧹 Nettoyage

### Nettoyage Standard

```bash
make clean
```
**Description** : Nettoyage des conteneurs et images inutilisées
- Arrête les conteneurs
- Supprime les conteneurs arrêtés
- Nettoie les images dangling
- **Préserve les volumes de données**

---

### Nettoyage Complet

```bash
make clean-all
```
**Description** : Nettoyage complet du système
- Supprime tous les conteneurs
- Supprime tous les volumes
- Supprime toutes les images
- Supprime le réseau
- **⚠️ ATTENTION : Perte totale des données**
- **Utile pour réinitialiser complètement le projet**

---

### Nettoyage des Volumes

```bash
make clean-volumes
```
**Description** : Supprime uniquement les volumes
- Préserve les images et conteneurs
- **⚠️ ATTENTION : Perte des données**
- **Utile pour réinitialiser les données seulement**

---

## 🔍 Monitoring Stack (Optionnel)

### Démarrer le Monitoring

```bash
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```
**Description** : Démarre la stack de monitoring
- Prometheus (métriques)
- Grafana (dashboards)
- Alertmanager (alertes)
- cAdvisor (conteneurs)
- Node Exporter (système)
- Kafka Exporter

**Ou utiliser le script :**
```bash
./scripts/start-monitoring.sh
```

---

### Arrêter le Monitoring

```bash
docker-compose -f monitoring/docker-compose.monitoring.yml down
```
**Description** : Arrête la stack de monitoring

---

### Valider la Configuration Monitoring

```bash
python scripts/validate-monitoring.py
```
**Description** : Vérifie que la configuration monitoring est complète
- Fichiers de configuration
- Scripts
- Directories

---

### Dashboard Monitoring CLI

```bash
./scripts/monitoring-dashboard.sh
```
**Description** : Dashboard de monitoring dans le terminal
- Status en temps réel
- Métriques Kafka
- Usage ressources
- **Rafraîchissement automatique toutes les 5s**
- **Ctrl+C pour quitter**

---

## 🌐 Accès Direct aux Services

### Dashboard Principal
```bash
open http://localhost:3000
# ou
start http://localhost:3000  # Windows
```

### Backend API
```bash
open http://localhost:8000
```

### Documentation API (Swagger)
```bash
open http://localhost:8000/docs
```

### Kafka UI
```bash
open http://localhost:8085
```

### Spark Master UI
```bash
open http://localhost:8082
```

### Grafana (si monitoring activé)
```bash
open http://localhost:3001
# Login: admin / admin
```

### Prometheus (si monitoring activé)
```bash
open http://localhost:9090
```

---

## 📋 Commandes Docker Directes

### Liste des Conteneurs

```bash
docker ps
```
**Description** : Liste tous les conteneurs actifs

```bash
docker ps -a
```
**Description** : Liste tous les conteneurs (actifs et arrêtés)

```bash
docker ps --filter "name=crypto-viz"
```
**Description** : Liste uniquement les conteneurs Crypto Viz

---

### Logs d'un Conteneur Spécifique

```bash
docker logs crypto-viz-backend
docker logs crypto-viz-kafka
docker logs crypto-viz-ollama
docker logs -f crypto-viz-backend  # Suit les logs en temps réel
docker logs --tail 50 crypto-viz-backend  # Dernières 50 lignes
```

---

### Redémarrer un Conteneur Spécifique

```bash
docker restart crypto-viz-backend
docker restart crypto-viz-kafka
```

---

### Shell dans un Conteneur

```bash
docker exec -it crypto-viz-backend bash
docker exec -it crypto-viz-kafka bash
```

---

### Inspecter un Conteneur

```bash
docker inspect crypto-viz-backend
```

---

## 🔑 Variables d'Environnement Importantes

À configurer dans le fichier `.env` :

```bash
# APIs (optionnel - demo mode par défaut)
NEWS_API_KEY=votre_clé_newsapi
COINGECKO_API_KEY=votre_clé_coingecko
REDDIT_CLIENT_ID=votre_client_id
REDDIT_CLIENT_SECRET=votre_client_secret

# Intervals de scraping (en secondes)
SCRAPER_INTERVAL=30
ANALYTICS_INTERVAL=60

# Ollama
OLLAMA_MODEL=llama3.1:8b

# Backend
CORS_ORIGINS=http://localhost:3000

# Logs
LOG_LEVEL=INFO
```

---

## 🆘 Commandes de Diagnostic

### Problème : Services ne démarrent pas

```bash
# 1. Vérifier l'état
make health

# 2. Voir les logs
make logs

# 3. Vérifier les ports
netstat -an | grep "8000\|3000\|9092"  # Linux/Mac
netstat -an | findstr "8000 3000 9092"  # Windows

# 4. Redémarrage propre
make restart-clean
```

---

### Problème : Kafka ne fonctionne pas

```bash
# 1. Vérifier Zookeeper
docker logs crypto-viz-zookeeper

# 2. Vérifier Kafka
docker logs crypto-viz-kafka

# 3. Vérifier les topics
make kafka-topics

# 4. Redémarrer l'infrastructure
docker restart crypto-viz-zookeeper
sleep 10
docker restart crypto-viz-kafka
```

---

### Problème : Ollama ne répond pas

```bash
# 1. Vérifier le téléchargement du modèle
docker logs crypto-viz-ollama

# 2. Télécharger manuellement le modèle
docker exec crypto-viz-ollama ollama pull llama3.1:8b

# 3. Tester Ollama
curl http://localhost:11434/api/tags
```

---

### Problème : Analytics ne traite pas

```bash
# 1. Vérifier les logs
make logs-analytics

# 2. Vérifier DuckDB
make duckdb

# 3. Vérifier Kafka
make kafka-topics

# 4. Vérifier le scraper
make logs-scraper
```

---

### Problème : Manque d'espace disque

```bash
# 1. Vérifier l'espace utilisé
docker system df

# 2. Nettoyer
docker system prune -a

# 3. Supprimer les volumes inutilisés
docker volume prune
```

---

## 📚 Ordre Recommandé des Commandes

### Première Installation
```bash
1. make install
2. # Éditer .env avec vos clés API (optionnel)
3. make quick-start
4. make health
5. open http://localhost:3000
```

### Développement Quotidien
```bash
1. make start
2. make dev-backend  # ou dev-frontend selon besoin
3. make logs-backend  # monitoring
4. make test
5. make stop
```

### Après Modifications Code
```bash
1. make test
2. make restart-full
3. make health
```

### Debugging
```bash
1. make health
2. make logs-[service]
3. make dev-shell
4. docker logs -f crypto-viz-[service]
```

### Nettoyage Complet
```bash
1. make stop
2. make clean-all
3. make install
4. make quick-start
```

---

## 💡 Astuces

### Alias Utiles (à ajouter dans ~/.bashrc ou ~/.zshrc)

```bash
alias cv='cd /path/to/T-DAT-901-NCE_10'
alias cvstart='cv && make start'
alias cvstop='cv && make stop'
alias cvlogs='cv && make logs'
alias cvhealth='cv && make health'
alias cvdev='cv && make dev'
```

### Watch Mode pour Logs

```bash
watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}"'
```

### Monitoring Ressources en Temps Réel

```bash
docker stats
```

---

**📖 Pour plus d'informations, consultez :**
- `README.md` - Documentation principale
- `CLAUDE.md` - Guide pour développeurs
- `MONITORING_SETUP.md` - Configuration monitoring
- `monitoring/README.md` - Documentation monitoring détaillée
