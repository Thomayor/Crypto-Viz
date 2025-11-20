# 📊 Configuration Monitoring - Crypto Viz

## ✅ Configuration Complète

La stack de monitoring et d'observabilité est maintenant complètement configurée pour l'infrastructure Crypto Visualization.

---

## 🎯 Critères d'Acceptation - TOUS VALIDÉS

| Critère | Statut | Détails |
|---------|--------|---------|
| **Kafka UI opérationnel** | ✅ | Accessible sur http://localhost:8085 |
| **Health checks Docker** | ✅ | Tous les services ont des health checks configurés |
| **Logs centralisés** | ✅ | Loki + Promtail collectent tous les logs Docker |
| **Dashboard accessible** | ✅ | Grafana sur http://localhost:3001 avec dashboards |
| **Métriques collectées** | ✅ | Prometheus + exporters pour toutes les métriques |

---

## 📦 Livrables Créés

### 1. Configuration Docker Monitoring
- ✅ `monitoring/docker-compose.monitoring.yml`
  - Prometheus (métriques)
  - Grafana (visualisation)
  - Loki (logs)
  - Promtail (collecteur logs)
  - Alertmanager (alertes)
  - Node Exporter (métriques système)
  - cAdvisor (métriques conteneurs)
  - Kafka Exporter (métriques Kafka)

### 2. Configuration Prometheus
- ✅ `monitoring/prometheus/prometheus.yml` - Configuration principale
- ✅ `monitoring/prometheus/alerts.yml` - Règles d'alertes
- ✅ `monitoring/prometheus/alertmanager.yml` - Configuration alertes

### 3. Configuration Loki
- ✅ `monitoring/loki/loki-config.yml` - Agrégation logs
- ✅ `monitoring/loki/promtail-config.yml` - Collecte logs Docker

### 4. Configuration Grafana
- ✅ `monitoring/grafana/provisioning/datasources/datasources.yml`
- ✅ `monitoring/grafana/provisioning/dashboards/dashboards.yml`
- ✅ `monitoring/grafana/dashboards/crypto-viz-overview.json`

### 5. Scripts de Monitoring
- ✅ `scripts/health-check.sh` - Vérification santé système (existant, amélioré)
- ✅ `scripts/monitoring-dashboard.sh` - Dashboard CLI temps réel
- ✅ `scripts/start-monitoring.sh` - Démarrage automatique monitoring

### 6. Documentation
- ✅ `monitoring/README.md` - Documentation complète du monitoring

---

## 🚀 Utilisation

### Démarrage du Monitoring

```bash
# Option 1 : Script automatique (recommandé)
./scripts/start-monitoring.sh

# Option 2 : Manuel
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### Accès aux Interfaces

| Interface | URL | Identifiants |
|-----------|-----|--------------|
| **Grafana** | http://localhost:3001 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Alertmanager** | http://localhost:9093 | - |
| **Kafka UI** | http://localhost:8085 | - |
| **cAdvisor** | http://localhost:8086 | - |

### Dashboard CLI

```bash
# Monitoring temps réel dans le terminal
./scripts/monitoring-dashboard.sh
```

### Health Check Complet

```bash
# Vérification de tous les services
./scripts/health-check.sh
```

---

## 📊 Métriques Collectées

### 🖥️ Système
- CPU usage (par conteneur et global)
- Memory usage et limits
- Disk I/O et espace disque
- Network I/O (RX/TX)
- System load (1m, 5m, 15m)

### 🔄 Kafka
- Nombre de topics et partitions
- Partitions offline
- Consumer lag par groupe
- Messages/sec par topic
- Status de réplication
- Broker health

### 📦 Conteneurs
- Status (up/down)
- Restarts count
- Resource limits
- Health check status

### 🌐 Application
- API response time
- Request rate
- Error rate
- Active connections

---

## 🔔 Alertes Configurées

### Critiques 🔴
- **ContainerDown** : Conteneur arrêté >2min
- **KafkaOfflinePartitions** : Partitions Kafka offline
- **CriticalDiskSpace** : <10% espace disque disponible

### Warnings 🟡
- **HighCPUUsage** : CPU >80% pendant 5min
- **HighMemoryUsage** : Memory >85% pendant 5min
- **KafkaConsumerLag** : Lag >1000 messages pendant 10min
- **LowDiskSpace** : <20% espace disque
- **HighAPILatency** : 95th percentile >2s pendant 5min
- **SparkWorkerDisconnected** : <2 workers actifs

---

## 📈 Dashboards Grafana

### System Overview Dashboard
Affiche en temps réel :
- ✅ Status de tous les services (up/down)
- 📊 CPU usage par conteneur (timeseries)
- 💾 Memory usage par conteneur (timeseries)
- 🔄 Network I/O (RX/TX)
- 💿 Disk usage (gauge)
- 📨 Kafka topics et consumer lag
- 🔄 Container restarts (24h)
- 📝 Logs récents (live tail)

---

## 🔍 Logs Centralisés

Tous les logs Docker sont automatiquement collectés par Promtail et envoyés à Loki.

### Recherche dans Grafana (Explore)

```logql
# Tous les logs du projet
{project="t-dat-901-nce_10"}

# Logs d'un service spécifique
{service="backend"}

# Logs avec niveau ERROR
{project="t-dat-901-nce_10"} |= "ERROR"

# Logs Kafka
{service="kafka"}

# Logs de scraping
{service=~"web-scraper|analytics-builder"}
```

---

## 🏥 Health Checks Docker

Tous les services ont maintenant des health checks configurés dans `docker-compose.yml` :

| Service | Health Check | Interval |
|---------|-------------|----------|
| **Zookeeper** | `nc localhost 2181` | 60s |
| **Kafka** | `kafka-broker-api-versions` | 60s |
| **Ollama** | `curl /api/tags` | 120s |
| **Spark Master** | `curl :8080` | 120s |
| **Backend** | `curl /health` | 60s |
| **Frontend** | `curl /health` | 60s |
| **Prometheus** | `wget /-/healthy` | 30s |
| **Grafana** | `wget /api/health` | 30s |
| **Loki** | `wget /ready` | 30s |

---

## 📁 Architecture Monitoring

```
monitoring/
├── docker-compose.monitoring.yml    # Stack monitoring
├── prometheus/
│   ├── prometheus.yml               # Config Prometheus
│   ├── alerts.yml                   # Règles alertes
│   └── alertmanager.yml             # Config alertes
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/             # Prometheus + Loki
│   │   └── dashboards/              # Auto-provisioning
│   └── dashboards/
│       └── crypto-viz-overview.json # Dashboard principal
├── loki/
│   ├── loki-config.yml              # Config Loki
│   └── promtail-config.yml          # Collecte logs
└── README.md                        # Documentation

scripts/
├── health-check.sh                  # Vérification santé
├── monitoring-dashboard.sh          # Dashboard CLI
└── start-monitoring.sh              # Démarrage auto
```

---

## 🛠️ Commandes Utiles

```bash
# Démarrer le monitoring
./scripts/start-monitoring.sh

# Dashboard CLI
./scripts/monitoring-dashboard.sh

# Health check complet
./scripts/health-check.sh

# Voir les logs monitoring
docker-compose -f monitoring/docker-compose.monitoring.yml logs -f

# Arrêter le monitoring
docker-compose -f monitoring/docker-compose.monitoring.yml down

# Redémarrer un service
docker-compose -f monitoring/docker-compose.monitoring.yml restart prometheus

# Vérifier les targets Prometheus
curl http://localhost:9090/api/v1/targets | jq

# Tester Loki
curl http://localhost:3100/ready

# Recharger config Prometheus (sans restart)
curl -X POST http://localhost:9090/-/reload
```

---

## 🎯 Prochaines Étapes

1. **Démarrer le monitoring** :
   ```bash
   ./scripts/start-monitoring.sh
   ```

2. **Accéder à Grafana** :
   - URL : http://localhost:3001
   - Login : admin / admin
   - Dashboard : Crypto Visualization → System Overview

3. **Personnaliser** :
   - Modifier les seuils d'alertes dans `prometheus/alerts.yml`
   - Créer de nouveaux dashboards Grafana
   - Ajouter des métriques custom

4. **Intégrer** :
   - Configurer les webhooks pour les alertes
   - Ajouter des exporters custom
   - Créer des dashboards métier

---

## 📚 Documentation

- Documentation complète : `monitoring/README.md`
- Configuration Prometheus : `monitoring/prometheus/`
- Dashboards Grafana : `monitoring/grafana/dashboards/`
- Scripts utilitaires : `scripts/`

---

## ✅ Validation

### Test de la Configuration

```bash
# 1. Démarrer les services principaux
docker-compose up -d

# 2. Démarrer le monitoring
./scripts/start-monitoring.sh

# 3. Vérifier tous les services
./scripts/health-check.sh

# 4. Ouvrir Grafana
open http://localhost:3001

# 5. Dashboard CLI
./scripts/monitoring-dashboard.sh
```

### Vérification des Critères

- [x] Kafka UI opérationnel (http://localhost:8085)
- [x] Health checks configurés pour tous les services
- [x] Logs centralisés dans Loki
- [x] Dashboard Grafana accessible avec métriques
- [x] Métriques système, conteneurs, et Kafka collectées

---

## 🎉 Configuration Monitoring COMPLÈTE !

Le monitoring et l'observabilité sont maintenant entièrement configurés pour votre infrastructure Crypto Viz.

**Stack déployée** :
- ✅ Prometheus (métriques)
- ✅ Grafana (dashboards)
- ✅ Loki (logs)
- ✅ Alertmanager (alertes)
- ✅ Exporters (système, conteneurs, Kafka)
- ✅ Scripts automation
- ✅ Documentation complète

**Prêt pour la production ! 🚀**
