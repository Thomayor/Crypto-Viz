# Crypto Viz - Monitoring & Observability

Ce dossier contient toute la configuration pour le monitoring et l'observabilité de l'infrastructure Crypto Visualization.

## 📊 Stack de Monitoring

- **Prometheus** - Collecte de métriques temps réel
- **Grafana** - Visualisation et dashboards
- **Loki** - Agrégation centralisée des logs
- **Promtail** - Collecteur de logs Docker
- **Alertmanager** - Gestion des alertes
- **Node Exporter** - Métriques système
- **cAdvisor** - Métriques des conteneurs
- **Kafka Exporter** - Métriques Kafka spécifiques

## 🚀 Démarrage Rapide

### 1. Démarrer le monitoring

```bash
# Option 1 : Utiliser le script automatique
./scripts/start-monitoring.sh

# Option 2 : Démarrage manuel
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

### 2. Accéder aux interfaces

| Service | URL | Credentials |
|---------|-----|------------|
| **Grafana** | http://localhost:3001 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Alertmanager** | http://localhost:9093 | - |
| **cAdvisor** | http://localhost:8086 | - |

### 3. Dashboard CLI

Pour un monitoring en temps réel dans le terminal :

```bash
./scripts/monitoring-dashboard.sh
```

## 📁 Structure

```
monitoring/
├── docker-compose.monitoring.yml   # Configuration Docker Compose
├── prometheus/
│   ├── prometheus.yml              # Configuration Prometheus
│   ├── alerts.yml                  # Règles d'alertes
│   └── alertmanager.yml            # Configuration Alertmanager
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/            # Sources de données (Prometheus, Loki)
│   │   └── dashboards/             # Provisioning des dashboards
│   └── dashboards/
│       └── crypto-viz-overview.json # Dashboard principal
├── loki/
│   ├── loki-config.yml             # Configuration Loki
│   └── promtail-config.yml         # Configuration collecteur de logs
└── README.md                       # Ce fichier
```

## 📈 Métriques Collectées

### Métriques Système
- CPU usage par conteneur
- Memory usage et limits
- Disk I/O
- Network I/O
- System load

### Métriques Kafka
- Nombre de topics
- Partitions offline
- Consumer lag
- Messages par seconde
- Réplication status

### Métriques Application
- Backend API latency
- Request rate
- Error rate
- Spark jobs status

## 🔔 Alertes Configurées

Les alertes suivantes sont configurées dans `prometheus/alerts.yml` :

### Critiques 🔴
- **ContainerDown** : Conteneur arrêté depuis >2min
- **KafkaOfflinePartitions** : Partitions Kafka offline
- **CriticalDiskSpace** : <10% espace disque

### Warnings 🟡
- **HighCPUUsage** : CPU >80% pendant 5min
- **HighMemoryUsage** : Memory >85% pendant 5min
- **KafkaConsumerLag** : Lag >1000 messages
- **LowDiskSpace** : <20% espace disque
- **HighAPILatency** : 95th percentile >2s
- **SparkWorkerDisconnected** : <2 workers actifs

## 🔍 Utilisation

### Visualiser les métriques dans Grafana

1. Ouvrir http://localhost:3001
2. Login : `admin` / `admin`
3. Aller dans **Dashboards** → **Crypto Visualization** → **System Overview**

Le dashboard principal affiche :
- État de santé de tous les services
- CPU et Memory usage
- Métriques Kafka (topics, lag)
- Network I/O
- Logs récents

### Requêtes Prometheus utiles

```promql
# CPU usage par conteneur
rate(container_cpu_usage_seconds_total{name=~"crypto-viz.*"}[5m]) * 100

# Memory usage
container_memory_usage_bytes{name=~"crypto-viz.*"} / 1024 / 1024

# Kafka consumer lag
kafka_consumergroup_lag

# Container restarts
increase(container_last_seen{name=~"crypto-viz.*"}[24h])
```

### Recherche de logs dans Loki

Dans Grafana, onglet **Explore** :

```logql
# Tous les logs du projet
{project="t-dat-901-nce_10"}

# Logs d'un service spécifique
{service="backend"}

# Logs avec niveau ERROR
{project="t-dat-901-nce_10"} |= "ERROR"

# Logs Kafka uniquement
{service="kafka"}

# Logs des scrapers/analytics
{service=~"web-scraper|analytics-builder"}
```

## 🛠️ Configuration Avancée

### Modifier la rétention

**Prometheus** (`prometheus/prometheus.yml`) :
```yaml
--storage.tsdb.retention.time=30d  # 30 jours par défaut
```

**Loki** (`loki/loki-config.yml`) :
```yaml
retention_period: 720h  # 30 jours
```

### Ajouter de nouvelles métriques

1. Éditer `prometheus/prometheus.yml`
2. Ajouter un nouveau `scrape_config`
3. Redémarrer Prometheus :
```bash
docker-compose -f monitoring/docker-compose.monitoring.yml restart prometheus
```

### Créer de nouvelles alertes

1. Éditer `prometheus/alerts.yml`
2. Ajouter votre règle d'alerte
3. Recharger la config :
```bash
curl -X POST http://localhost:9090/-/reload
```

## 📊 Dashboards

### Dashboard Principal : System Overview

Affiche :
- ✅ Status de tous les services
- 📊 CPU/Memory usage
- 🔄 Network I/O
- 💾 Disk usage
- 📨 Kafka metrics
- 🔄 Container restarts
- 📝 Recent logs

### Créer un nouveau dashboard

1. Dans Grafana, créer un nouveau dashboard
2. Ajouter des panels avec requêtes Prometheus/Loki
3. Exporter le JSON
4. Sauvegarder dans `monitoring/grafana/dashboards/`

## 🚨 Troubleshooting

### Prometheus ne collecte pas les métriques

```bash
# Vérifier les targets
curl http://localhost:9090/api/v1/targets

# Vérifier les logs
docker logs crypto-viz-prometheus
```

### Grafana ne se connecte pas aux datasources

```bash
# Vérifier la configuration
docker exec crypto-viz-grafana cat /etc/grafana/provisioning/datasources/datasources.yml

# Tester la connexion Prometheus
curl http://prometheus:9090/api/v1/status/config
```

### Loki ne reçoit pas de logs

```bash
# Vérifier Promtail
docker logs crypto-viz-promtail

# Vérifier Loki
curl http://localhost:3100/ready
```

### Les alertes ne fonctionnent pas

```bash
# Vérifier Alertmanager
docker logs crypto-viz-alertmanager

# Vérifier les règles dans Prometheus
curl http://localhost:9090/api/v1/rules
```

## 📝 Commandes Utiles

```bash
# Démarrer le monitoring
./scripts/start-monitoring.sh

# Voir les logs en temps réel
docker-compose -f monitoring/docker-compose.monitoring.yml logs -f

# Redémarrer un service
docker-compose -f monitoring/docker-compose.monitoring.yml restart [service]

# Arrêter le monitoring
docker-compose -f monitoring/docker-compose.monitoring.yml down

# Supprimer les données (reset)
docker-compose -f monitoring/docker-compose.monitoring.yml down -v

# Dashboard CLI
./scripts/monitoring-dashboard.sh

# Health check complet
./scripts/health-check.sh
```

## 🔗 Intégration avec Backend

Les alertes peuvent être envoyées au backend via webhook :

```yaml
# alertmanager.yml
receivers:
  - name: 'backend-webhook'
    webhook_configs:
      - url: 'http://backend:8000/api/alerts/webhook'
```

Le backend peut ensuite :
- Stocker les alertes dans la DB
- Envoyer des notifications
- Créer des tickets
- Déclencher des actions automatiques

## 📚 Ressources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [LogQL Guide](https://grafana.com/docs/loki/latest/logql/)

## 🎯 Bonnes Pratiques

1. **Métriques** : Garder les métriques focalisées et utiles
2. **Alertes** : Éviter le bruit, alerter uniquement sur l'important
3. **Rétention** : Ajuster selon les besoins et l'espace disque
4. **Dashboards** : Créer des vues par rôle (dev, ops, business)
5. **Logs** : Utiliser des niveaux appropriés (DEBUG, INFO, WARNING, ERROR)
6. **Labels** : Utiliser des labels cohérents pour le filtrage

---

**Monitoring configuré avec ❤️ pour Crypto Viz**
