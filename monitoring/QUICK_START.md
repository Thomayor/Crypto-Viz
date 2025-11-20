# 🚀 Monitoring - Quick Start Guide

## 🎯 En 3 commandes

```bash
# 1. Valider la configuration
./scripts/validate-monitoring.sh

# 2. Démarrer le monitoring
./scripts/start-monitoring.sh

# 3. Accéder à Grafana
open http://localhost:3001
# Login: admin / admin
```

## 📊 Interfaces Disponibles

| Interface | URL | Description |
|-----------|-----|-------------|
| 🎨 **Grafana** | http://localhost:3001 | Dashboards & visualisation |
| 📈 **Prometheus** | http://localhost:9090 | Métriques brutes |
| 🔔 **Alertmanager** | http://localhost:9093 | Gestion alertes |
| 🚀 **Kafka UI** | http://localhost:8085 | Interface Kafka |
| 📦 **cAdvisor** | http://localhost:8086 | Stats conteneurs |

## 💻 Monitoring CLI

Pour un dashboard en temps réel dans votre terminal :

```bash
./scripts/monitoring-dashboard.sh
```

Affiche :
- ✅ Status de tous les services
- 📊 Métriques Kafka
- 💾 Usage ressources
- 🔗 Points d'accès

## 🏥 Health Check

```bash
./scripts/health-check.sh
```

Vérifie :
- Conteneurs Docker
- Endpoints HTTP
- Topics Kafka
- Spark cluster
- Volumes de données

## 📝 Logs

### Voir tous les logs du monitoring

```bash
docker-compose -f monitoring/docker-compose.monitoring.yml logs -f
```

### Logs d'un service spécifique

```bash
docker-compose -f monitoring/docker-compose.monitoring.yml logs -f prometheus
docker-compose -f monitoring/docker-compose.monitoring.yml logs -f grafana
docker-compose -f monitoring/docker-compose.monitoring.yml logs -f loki
```

## 🔍 Requêtes Utiles

### Dans Prometheus (http://localhost:9090)

```promql
# CPU usage par conteneur
rate(container_cpu_usage_seconds_total{name=~"crypto-viz.*"}[5m]) * 100

# Memory usage
container_memory_usage_bytes{name=~"crypto-viz.*"} / 1024 / 1024

# Kafka consumer lag
kafka_consumergroup_lag
```

### Dans Grafana - Logs (Explore)

```logql
# Tous les logs
{project="t-dat-901-nce_10"}

# Logs avec erreurs
{project="t-dat-901-nce_10"} |= "ERROR"

# Logs d'un service
{service="backend"}
```

## 🛠️ Commandes Courantes

```bash
# Démarrer
./scripts/start-monitoring.sh

# Arrêter
docker-compose -f monitoring/docker-compose.monitoring.yml down

# Redémarrer un service
docker-compose -f monitoring/docker-compose.monitoring.yml restart prometheus

# Supprimer tout (y compris données)
docker-compose -f monitoring/docker-compose.monitoring.yml down -v

# Voir l'état
docker-compose -f monitoring/docker-compose.monitoring.yml ps
```

## 🎨 Premier Dashboard Grafana

1. Ouvrir http://localhost:3001
2. Login : `admin` / `admin`
3. Aller dans **Dashboards** (icône 4 carrés)
4. Sélectionner **Crypto Visualization** → **System Overview**

Vous verrez :
- 📊 Status services
- 💻 CPU/Memory
- 🌐 Network I/O
- 💾 Disk usage
- 📨 Kafka metrics
- 📝 Live logs

## 🔔 Alertes

Les alertes sont automatiquement configurées pour :
- Conteneurs arrêtés
- CPU/Memory élevé
- Espace disque faible
- Kafka consumer lag
- API latency

Voir dans : **Alerting** → **Alert rules** dans Grafana

## 📚 Documentation Complète

- `monitoring/README.md` - Guide complet
- `MONITORING_SETUP.md` - Résumé configuration

## 💡 Tips

- Grafana se souvient de vos dashboards favoris
- Utilisez l'auto-refresh (en haut à droite)
- Les logs sont cherchables avec regex
- Créez vos propres dashboards et exportez-les

## ⚡ Troubleshooting

**Grafana ne démarre pas ?**
```bash
docker logs crypto-viz-grafana
```

**Prometheus ne collecte pas de métriques ?**
```bash
curl http://localhost:9090/api/v1/targets
```

**Pas de logs dans Loki ?**
```bash
docker logs crypto-viz-promtail
```

---

**Happy Monitoring! 📊🚀**
