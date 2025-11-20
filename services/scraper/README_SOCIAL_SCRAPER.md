# Reddit Social Sentiment Scraper - Guide d'Utilisation

## 📋 Vue d'ensemble

Le Social Sentiment Scraper collecte des mentions de cryptomonnaies sur Reddit pour l'analyse de sentiment. Il surveille 10 subreddits crypto et publie les données dans Kafka.

## 🚀 Démarrage Rapide

### 1. Configuration des Credentials Reddit

Créez une application Reddit sur https://www.reddit.com/prefs/apps :
- **Type** : script
- **Name** : CryptoViz Social Scraper
- **Redirect URI** : http://localhost:8080

Récupérez vos credentials et mettez à jour le fichier `.env` :

```bash
REDDIT_CLIENT_ID=votre_client_id
REDDIT_CLIENT_SECRET=votre_client_secret
REDDIT_USER_AGENT=CryptoViz/1.0
SOCIAL_SCRAPER_INTERVAL=600
```

### 2. Test de la Connexion Reddit

Avant de lancer le scraper complet, testez la connexion :

```bash
cd services/scraper
python3 test_reddit_scraper.py
```

Ce script va :
- ✅ Tester la connexion à l'API Reddit
- ✅ Vérifier le preprocessing de texte
- ✅ Scraper quelques posts de test
- ✅ Afficher les cryptomonnaies mentionnées

### 3. Lancer le Scraper

**Option A : Mode Standalone**
```bash
cd services/scraper
python3 social_sentiment_scraper.py
```

**Option B : Avec Docker**
```bash
# À ajouter au docker-compose.yml
docker-compose up -d social-scraper
```

## 📊 Fonctionnement

### Cycle de Scraping

**Intervalle** : 10 minutes (600 secondes)

**Pour chaque cycle :**
1. Parcourt 10 subreddits crypto
2. Récupère les 10 posts "hot" de chaque subreddit
3. Filtre les posts mentionnant des cryptomonnaies
4. Nettoie et preprocess le texte
5. Extrait les coins mentionnés
6. Publie vers Kafka topic `social-posts`

### Subreddits Surveillés (10)

| Subreddit | Focus | Subscribers |
|-----------|-------|-------------|
| r/CryptoCurrency | Général crypto | ~7M |
| r/Bitcoin | Bitcoin | ~5M |
| r/ethereum | Ethereum | ~2M |
| r/cardano | Cardano | ~700K |
| r/solana | Solana | ~300K |
| r/polkadot | Polkadot | ~100K |
| r/CryptoMarkets | Trading | ~800K |
| r/altcoin | Altcoins | ~400K |
| r/defi | DeFi | ~200K |
| r/NFT | NFTs | ~600K |

### Cryptomonnaies Détectées (14)

Le scraper peut identifier ces cryptomonnaies dans les posts :

```
BTC (Bitcoin), ETH (Ethereum), ADA (Cardano), SOL (Solana),
DOT (Polkadot), XRP (Ripple), DOGE (Dogecoin), SHIB (Shiba),
MATIC (Polygon), AVAX (Avalanche), LINK (Chainlink), ATOM (Cosmos),
LTC (Litecoin), BNB (Binance)
```

## 📝 Format des Données

Chaque post publié dans Kafka contient :

```json
{
  "platform": "reddit",
  "post_id": "abc123",
  "author": "username",
  "title": "Bitcoin breaks $50k!",
  "text": "Cleaned and preprocessed text content...",
  "score": 1234,
  "num_comments": 567,
  "created_utc": "2025-01-04T12:00:00",
  "subreddit": "CryptoCurrency",
  "url": "https://reddit.com/r/CryptoCurrency/...",
  "coins_mentioned": ["BTC"],
  "timestamp": "2025-01-04T12:05:00"
}
```

## 🔧 Configuration Avancée

### Modifier l'Intervalle de Scraping

Dans `.env` :
```bash
SOCIAL_SCRAPER_INTERVAL=300  # 5 minutes
SOCIAL_SCRAPER_INTERVAL=900  # 15 minutes
```

### Ajouter des Subreddits

Éditez `social_sentiment_scraper.py` ligne ~37 :

```python
CRYPTO_SUBREDDITS = [
    'CryptoCurrency',
    'Bitcoin',
    'ethereum',
    # Ajoutez vos subreddits ici
    'moonshots',
    'cryptocurrencymemes',
]
```

### Ajuster les Posts par Subreddit

Dans `SocialSentimentScraper.__init__()`, modifiez la méthode `scrape_all_subreddits()` :

```python
posts = await self.reddit_scraper.scrape_all_subreddits(
    self.subreddits,
    limit_per_subreddit=20  # Au lieu de 10
)
```

## 📈 Performance Attendue

### Avec Configuration par Défaut

- **Cycle** : 10 minutes
- **Subreddits** : 10
- **Posts/subreddit** : 10
- **Posts filtrés** : ~50-70% (avec mentions crypto)
- **Total/heure** : ~300-400 posts
- **Total/jour** : ~5,000-7,000 posts

### Rate Limiting

- **Reddit API** : 60 requêtes/minute
- **Scraper** : ~10 requêtes/cycle (1 par subreddit)
- **Sécurité** : Large marge, pas de risque de ban

## 🐛 Dépannage

### Erreur : "Invalid credentials"

```bash
✗ Error: received 401 HTTP response
```

**Solution** :
- Vérifiez que `REDDIT_CLIENT_ID` et `REDDIT_CLIENT_SECRET` sont corrects
- Assurez-vous que l'app Reddit est de type "script"
- Régénérez les credentials si nécessaire

### Erreur : "No module named 'praw'"

```bash
ModuleNotFoundError: No module named 'praw'
```

**Solution** :
```bash
pip install praw kafka-python backoff
```

### Aucun Post Trouvé

```
WARNING: No relevant posts found
```

**Causes possibles** :
- Les posts récents ne mentionnent pas de cryptomonnaies
- Rate limit atteint (attendez 1 minute)
- Subreddit temporairement inaccessible

**Solution** : Attendez le prochain cycle (10 min)

### Kafka Connection Error

```
✗ Failed to create Kafka producer
```

**Solution** :
- Vérifiez que Kafka est démarré : `docker ps | grep kafka`
- Vérifiez la connexion : `KAFKA_BOOTSTRAP_SERVERS=kafka:29092`

## 📊 Monitoring

### Voir les Logs du Scraper

```bash
# Logs en temps réel
docker logs -f crypto-viz-social-scraper

# Dernières 100 lignes
docker logs --tail 100 crypto-viz-social-scraper
```

### Vérifier les Messages Kafka

```bash
# Compter les messages
docker exec crypto-viz-kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 --topic social-posts

# Voir les derniers messages
docker exec crypto-viz-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic social-posts \
  --from-beginning \
  --max-messages 5
```

### Statistiques du Scraper

Les logs affichent des stats à chaque cycle :

```
Scrape cycle completed in 12.34s
Scraped: 67, Published: 67, Errors: 0
Total stats - Scraped: 4023, Published: 4023, Errors: 2
```

## 🔒 Sécurité & Respect des APIs

### Bonnes Pratiques

✅ **Respecter les Rate Limits** : 60 req/min max
✅ **User Agent Descriptif** : CryptoViz/1.0
✅ **Credentials Sécurisés** : Jamais dans le code
✅ **Données Publiques** : Lecture seule
✅ **Error Handling** : Retry avec backoff

### Terms of Service

Ce scraper est conforme aux :
- ✅ Reddit API Terms of Service
- ✅ Reddit Data API Terms
- ✅ PRAW Best Practices

**Limitation** : Lecture seule, aucune écriture/modification

## 📚 Documentation Supplémentaire

- **SUBREDDITS.md** : Liste complète des subreddits
- **Reddit API Docs** : https://www.reddit.com/dev/api
- **PRAW Documentation** : https://praw.readthedocs.io/

## 🆘 Support

En cas de problème :
1. Vérifiez les logs : `docker logs crypto-viz-social-scraper`
2. Testez la connexion : `python3 test_reddit_scraper.py`
3. Vérifiez les credentials Reddit
4. Consultez la documentation PRAW
