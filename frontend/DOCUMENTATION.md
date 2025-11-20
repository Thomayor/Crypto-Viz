# Documentation Frontend - CRYPTO VIZ

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Technologies utilisées](#technologies-utilisées)
4. [Structure du projet](#structure-du-projet)
5. [Configuration](#configuration)
6. [Composants](#composants)
7. [Vues](#vues)
8. [Services et API](#services-et-api)
9. [Store Pinia](#store-pinia)
10. [Composables](#composables)
11. [Styling et Design](#styling-et-design)
12. [Développement](#développement)
13. [Déploiement](#déploiement)

---

## Vue d'ensemble

**CRYPTO VIZ** est une plateforme d'analyse de données de cryptomonnaies en temps réel. Le frontend est construit avec Vue 3, TypeScript et Tailwind CSS, offrant une interface moderne avec des effets de glassmorphisme et des animations fluides.

### Fonctionnalités principales

- **Tableau de bord en temps réel** : Visualisation des prix des cryptomonnaies avec mise à jour automatique toutes les 30 secondes
- **Analyses ML** : Prédictions de prix, détection d'anomalies et clustering via des modèles d'apprentissage automatique
- **Analyse de sentiment** : Agrégation de news et de posts des réseaux sociaux avec analyse de sentiment IA
- **Visualisations graphiques** : Charts interactifs pour les prix, volumes, et tendances
- **Design responsive** : Interface adaptative pour desktop et mobile

---

## Architecture

### Pattern architectural

Le frontend utilise une **architecture en couches** :

```
┌─────────────────────────────────────────┐
│          Vues (Views)                   │  ← Pages de l'application
├─────────────────────────────────────────┤
│     Composants (Components)             │  ← Composants réutilisables
├─────────────────────────────────────────┤
│  Composables & Store (Business Logic)  │  ← Logique métier
├─────────────────────────────────────────┤
│      Services API (Data Layer)          │  ← Couche d'accès aux données
└─────────────────────────────────────────┘
```

### Flux de données

1. **Polling HTTP** : Mise à jour automatique des données via requêtes HTTP périodiques
2. **Store Pinia** : Gestion centralisée de l'état de l'application
3. **Composables** : Logique réutilisable (polling, formatage)
4. **Réactivité Vue 3** : Mise à jour automatique de l'interface

---

## Technologies utilisées

### Core Framework

- **Vue 3.5.13** : Framework JavaScript progressif avec Composition API
- **TypeScript 5.7.3** : Typage statique pour une meilleure maintenabilité
- **Vite 7.0.6** : Build tool ultra-rapide avec Hot Module Replacement (HMR)

### State Management & Routing

- **Pinia 3.0.3** : Store de gestion d'état moderne pour Vue 3
- **Vue Router 4.5.0** : Routage officiel pour Vue.js

### Styling & UI

- **Tailwind CSS 3.4.17** : Framework CSS utility-first
- **PostCSS** : Transformation CSS avec autoprefixer
- **Heroicons** : Icônes SVG optimisées
- **Headless UI** : Composants UI accessibles sans style

### Data Visualization

- **Chart.js 4.5.1** : Bibliothèque de graphiques flexible
- **vue-chartjs 5.3.3** : Wrapper Vue pour Chart.js

### Utilities

- **date-fns 4.1.0** : Manipulation de dates moderne et légère

---

## Structure du projet

```
frontend/
├── public/                      # Fichiers statiques
├── src/
│   ├── assets/                  # Assets (CSS, images)
│   │   └── main.css            # Styles globaux et Tailwind
│   │
│   ├── components/              # Composants réutilisables
│   │   ├── charts/             # Composants de graphiques
│   │   │   ├── DoughnutChart.vue
│   │   │   ├── PriceChart.vue
│   │   │   ├── SentimentChart.vue
│   │   │   └── VolumeChart.vue
│   │   │
│   │   ├── layout/             # Composants de mise en page
│   │   │   └── AppLayout.vue   # Layout principal avec navigation
│   │   │
│   │   └── ui/                 # Composants UI de base
│   │       ├── Alert.vue
│   │       ├── Badge.vue
│   │       ├── Card.vue
│   │       └── LoadingSpinner.vue
│   │
│   ├── composables/             # Logique réutilisable
│   │   ├── useFormatting.ts    # Formatage de nombres et dates
│   │   └── usePolling.ts       # Système de polling HTTP
│   │
│   ├── router/                  # Configuration du routeur
│   │   └── index.ts
│   │
│   ├── services/                # Services API
│   │   └── api.ts              # Client API REST
│   │
│   ├── stores/                  # Stores Pinia
│   │   ├── analytics.ts        # Store des analyses ML
│   │   ├── crypto.ts           # Store des prix crypto
│   │   └── news.ts             # Store des news et social media
│   │
│   ├── types/                   # Définitions TypeScript
│   │   └── index.ts            # Interfaces et types
│   │
│   ├── views/                   # Pages de l'application
│   │   ├── AnalyticsView.vue   # Page d'analyses ML
│   │   ├── DashboardView.vue   # Tableau de bord principal
│   │   ├── LandingView.vue     # Page d'accueil marketing
│   │   └── NewsView.vue        # Page news et réseaux sociaux
│   │
│   ├── App.vue                  # Composant racine
│   └── main.ts                  # Point d'entrée de l'application
│
├── .env.example                 # Variables d'environnement exemple
├── index.html                   # Point d'entrée HTML
├── package.json                 # Dépendances npm
├── postcss.config.js            # Configuration PostCSS
├── tailwind.config.js           # Configuration Tailwind CSS
├── tsconfig.json                # Configuration TypeScript
├── vite.config.ts               # Configuration Vite
└── DOCUMENTATION.md             # Ce fichier
```

---

## Configuration

### Variables d'environnement

Créer un fichier `.env` à la racine du dossier `frontend/` :

```env
# URL de l'API backend
VITE_API_BASE_URL=http://localhost:8000

# Intervalles de polling (en millisecondes)
VITE_CRYPTO_POLL_INTERVAL=30000      # 30 secondes pour les prix
VITE_NEWS_POLL_INTERVAL=300000       # 5 minutes pour les news
VITE_ANALYTICS_POLL_INTERVAL=60000   # 1 minute pour les analyses
```

### Fichiers de configuration

#### vite.config.ts

Configuration de Vite avec alias de path et plugins Vue :

```typescript
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [
    vue(),
    // vueDevTools() désactivé (problème avec localStorage en Node.js)
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
```

#### tailwind.config.js

Configuration Tailwind avec palette de couleurs personnalisée :

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: { /* palette cyan-blue */ },
        success: '#10b981',
        danger: '#ef4444',
        warning: '#f59e0b',
      },
    },
  },
  plugins: [],
}
```

#### tsconfig.json

Configuration TypeScript avec support de Vue et alias de path :

```json
{
  "extends": "@vue/tsconfig/tsconfig.dom.json",
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"]
}
```

---

## Composants

### Composants UI de base

#### Card.vue

Composant de carte avec effet glassmorphisme :

```vue
<Card>
  <template #header>Titre</template>
  <p>Contenu de la carte</p>
</Card>
```

**Props** :
- `padding` : Padding personnalisé (défaut : "p-6")

**Slots** :
- `header` : En-tête de la carte
- `default` : Contenu principal

#### Badge.vue

Badge coloré pour afficher des statuts ou catégories :

```vue
<Badge variant="success">+2.5%</Badge>
```

**Props** :
- `variant` : "primary" | "success" | "danger" | "warning" | "neutral" (défaut : "primary")

#### LoadingSpinner.vue

Spinner de chargement animé :

```vue
<LoadingSpinner size="lg" />
```

**Props** :
- `size` : "sm" | "md" | "lg" (défaut : "md")

#### Alert.vue

Composant d'alerte avec icône et bouton de fermeture :

```vue
<Alert
  type="warning"
  :dismissible="true"
  @dismiss="handleDismiss"
>
  Message d'alerte
</Alert>
```

**Props** :
- `type` : "info" | "success" | "warning" | "error" (défaut : "info")
- `dismissible` : Affiche le bouton de fermeture (défaut : false)

**Events** :
- `dismiss` : Émis lors du clic sur le bouton de fermeture

### Composants de graphiques

#### PriceChart.vue

Graphique en ligne pour l'évolution des prix :

```vue
<PriceChart
  :data="priceHistory"
  :coin-id="'bitcoin'"
/>
```

**Props** :
- `data` : Tableau d'objets `{ timestamp: Date, price: number }`
- `coinId` : ID de la cryptomonnaie (pour la couleur)

#### VolumeChart.vue

Graphique en barres pour les volumes :

```vue
<VolumeChart :data="volumeData" />
```

**Props** :
- `data` : Tableau d'objets `{ timestamp: Date, volume: number }`

#### SentimentChart.vue

Graphique pour l'évolution du sentiment :

```vue
<SentimentChart :data="sentimentData" />
```

**Props** :
- `data` : Tableau d'objets `{ timestamp: Date, score: number }`

#### DoughnutChart.vue

Graphique en donut pour la répartition :

```vue
<DoughnutChart
  :data="marketCapData"
  title="Market Cap Distribution"
/>
```

**Props** :
- `data` : Objet `{ labels: string[], values: number[] }`
- `title` : Titre du graphique (optionnel)

### Composant de layout

#### AppLayout.vue

Layout principal avec navigation et footer :

**Caractéristiques** :
- Navigation responsive (desktop + mobile)
- Indicateur de statut de connexion
- Menu hamburger pour mobile
- Footer avec liens
- Transition fade entre les pages

**Navigation** :
- Home (/) : Page d'accueil marketing
- Dashboard (/dashboard) : Tableau de bord crypto
- Analytics (/analytics) : Analyses ML
- News & Social (/news) : News et réseaux sociaux

---

## Vues

### LandingView.vue

**Route** : `/`
**Layout** : Aucun (fullscreen)

Page d'accueil marketing avec :
- **Hero section** : Titre animé avec gradient, particules flottantes, boutons CTA
- **Stats** : 4 compteurs (50+ cryptos, 24/7 données, AI sentiment, ML predictions)
- **Features** : 3 cartes de fonctionnalités principales
- **Tech Stack** : Badges des technologies utilisées
- **CTA section** : Section d'appel à l'action finale
- **Footer** : Informations du projet

**Animations** :
- Gradient animé sur le titre
- 50 particules flottantes avec mouvement aléatoire
- Cards avec hover scale et shadow
- Fade-in-up sur le contenu

### DashboardView.vue

**Route** : `/dashboard`
**Layout** : AppLayout

Tableau de bord principal avec visualisation en temps réel :

**Sections** :

1. **En-tête** : Titre avec gradient cyan → blue → purple
2. **Stats Cards** (4 cartes) :
   - Total Market Cap
   - 24h Volume
   - Average Sentiment
   - Active Alerts
3. **Charts** (2 colonnes) :
   - Volume Chart (24h)
   - Sentiment Chart
4. **Top Gainers / Losers** (2 colonnes) :
   - Top 5 gainers avec variation positive
   - Top 5 losers avec variation négative
5. **Full Crypto Table** :
   - Tableau complet avec toutes les cryptos
   - Avatar, nom, prix, variation 24h, market cap, volume

**Mise à jour des données** :
- Polling automatique toutes les 30 secondes
- Affichage du dernier timestamp de mise à jour
- Spinner de chargement lors du fetch initial

**Computed Properties** :
- `totalMarketCap` : Somme de tous les market caps
- `totalVolume24h` : Somme de tous les volumes 24h
- `averageSentiment` : Moyenne des sentiments
- `activeAlerts` : Nombre d'anomalies critiques

**Formatage** :
- Prix : `$1,234.56`
- Market Cap : `$1.2T` / `$345.6B` / `$12.3M`
- Variation : `+2.5%` / `-1.2%` avec couleur
- Dates : Format relatif (il y a X minutes/heures)

### AnalyticsView.vue

**Route** : `/analytics`
**Layout** : AppLayout

Page d'analyses ML avec prédictions et détection d'anomalies :

**Sections** :

1. **En-tête** : Titre avec gradient purple → pink → red
2. **Coin Selector** : Dropdown pour sélectionner une crypto
3. **Anomalies Cards** :
   - Liste des anomalies détectées
   - Badges de sévérité (critical, high, medium, low)
   - Description et timestamp
4. **ML Predictions Cards** :
   - Prédictions de prix avec intervalle de confiance
   - Barre de progression pour la confiance
   - Prix actuel vs prédit
5. **Sentiment Trends Chart** :
   - Évolution du sentiment dans le temps
6. **Analytics Results Table** :
   - Tableau détaillé des résultats d'analyse
   - Timestamp, sentiment, volume, indicateurs techniques

**Mise à jour des données** :
- Polling toutes les 60 secondes
- Fetch automatique lors du changement de coin sélectionnée

**Badges de sévérité** :
- `critical` : Rouge
- `high` : Orange
- `medium` : Jaune
- `low` : Bleu

**Modèles ML disponibles** :
- Linear Regression (prédiction de prix)
- KMeans Clustering (groupement)
- Isolation Forest (détection d'anomalies)

### NewsView.vue

**Route** : `/news`
**Layout** : AppLayout

Page de news et réseaux sociaux avec analyse de sentiment :

**Sections** :

1. **En-tête** : Titre avec gradient blue → cyan → teal
2. **Stats Cards** (4 cartes) :
   - Total articles/posts
   - Sentiment positif
   - Sentiment neutre
   - Sentiment négatif
3. **Filters** :
   - Dropdown pour filtrer par sentiment
   - Badges des coins les plus mentionnés
   - Barre de progression du sentiment moyen
4. **News Articles** :
   - Liste des articles de news
   - Badge de sentiment
   - Source, auteur, date
   - Lien externe vers l'article
5. **Social Media Posts** :
   - Posts Reddit et Twitter
   - Boutons de filtre par plateforme
   - Scores de sentiment et engagement

**Mise à jour des données** :
- Polling toutes les 5 minutes (news)
- Filtre réactif par sentiment

**Sentiment Colors** :
- Positif : Vert
- Neutre : Gris
- Négatif : Rouge

**Calculs** :
- Top mentioned coins (comptage des références)
- Sentiment moyen (moyenne des scores)
- Distribution par sentiment (count)

---

## Services et API

### API Service (api.ts)

Service centralisé pour toutes les communications avec le backend.

**Base URL** : `http://localhost:8000`

#### Configuration

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    // Gestion des requêtes avec fetch
    // Gestion des erreurs HTTP
    // Parsing JSON automatique
  }
}
```

#### Endpoints disponibles

##### Health & Status

```typescript
// Vérifier la santé de l'API
api.getHealth(): Promise<HealthStatus>
```

##### Crypto Prices

```typescript
// Récupérer les derniers prix
api.getLatestPrices(limit?: number): Promise<CryptoPrice[]>

// Récupérer l'historique des prix d'une crypto
api.getPriceHistory(coinId: string, days?: number): Promise<CryptoPrice[]>

// Récupérer les statistiques d'une crypto
api.getCryptoStats(coinId: string): Promise<CryptoStats>
```

##### News & Social

```typescript
// Récupérer les dernières news
api.getLatestNews(limit?: number): Promise<News[]>

// Récupérer les posts des réseaux sociaux
api.getSocialPosts(platform?: string, limit?: number): Promise<SocialPost[]>
```

##### Analytics

```typescript
// Récupérer les résultats d'analyse
api.getAnalyticsResults(coinId?: string, limit?: number): Promise<AnalyticsResult[]>

// Récupérer les analyses de sentiment
api.getSentiment(coinId?: string, limit?: number): Promise<SentimentResult[]>
```

##### ML Predictions

```typescript
// Récupérer les prédictions ML
api.getPredictions(coinId?: string, modelType?: string): Promise<MLPrediction[]>

// Récupérer les anomalies détectées
api.getAnomalies(coinId?: string, severity?: string): Promise<Anomaly[]>

// Récupérer les clusters
api.getClusters(): Promise<ClusterResult[]>
```

#### Gestion des erreurs

Toutes les méthodes peuvent lancer une `Error` avec :
- Message d'erreur du backend (si disponible)
- Status HTTP en cas d'erreur réseau

Exemple d'utilisation :

```typescript
try {
  const prices = await api.getLatestPrices(50)
  // Traiter les prix
} catch (error) {
  console.error('Erreur lors du fetch des prix:', error)
  // Afficher une notification d'erreur à l'utilisateur
}
```

---

## Store Pinia

### crypto.ts - Store des cryptomonnaies

Gestion de l'état des prix de cryptomonnaies.

**State** :

```typescript
{
  prices: CryptoPrice[],        // Liste de tous les prix
  loading: boolean,             // État de chargement
  error: string | null,         // Message d'erreur
  lastUpdate: Date | null       // Timestamp de dernière mise à jour
}
```

**Getters** :

```typescript
// Top 5 des plus fortes hausses (24h)
gainers: CryptoPrice[]

// Top 5 des plus fortes baisses (24h)
losers: CryptoPrice[]

// Total market cap de toutes les cryptos
totalMarketCap: number

// Volume total 24h
totalVolume24h: number

// Récupérer une crypto par ID
getCryptoById(id: string): CryptoPrice | undefined
```

**Actions** :

```typescript
// Récupérer les derniers prix
async fetchLatestPrices(limit?: number): Promise<void>

// Récupérer l'historique d'une crypto
async fetchPriceHistory(coinId: string, days?: number): Promise<CryptoPrice[]>

// Récupérer les stats d'une crypto
async fetchCryptoStats(coinId: string): Promise<CryptoStats>
```

**Exemple d'utilisation** :

```vue
<script setup lang="ts">
import { useCryptoStore } from '@/stores/crypto'

const cryptoStore = useCryptoStore()

// Fetch des prix au montage
onMounted(() => {
  cryptoStore.fetchLatestPrices(50)
})

// Utilisation des getters
const topGainers = cryptoStore.gainers
const totalMarketCap = cryptoStore.totalMarketCap
</script>
```

### analytics.ts - Store des analyses ML

Gestion des prédictions ML et détection d'anomalies.

**State** :

```typescript
{
  analyticsResults: AnalyticsResult[],
  sentimentResults: SentimentResult[],
  predictions: MLPrediction[],
  anomalies: Anomaly[],
  clusters: ClusterResult[],
  loading: boolean,
  error: string | null
}
```

**Getters** :

```typescript
// Anomalies critiques uniquement
criticalAnomalies: Anomaly[]

// Dernière prédiction pour une crypto
getLatestPrediction(coinId: string): MLPrediction | undefined

// Sentiment moyen pour une crypto
getAverageSentiment(coinId: string): number
```

**Actions** :

```typescript
async fetchAnalyticsResults(coinId?: string, limit?: number): Promise<void>
async fetchSentiment(coinId?: string, limit?: number): Promise<void>
async fetchPredictions(coinId?: string, modelType?: string): Promise<void>
async fetchAnomalies(coinId?: string, severity?: string): Promise<void>
async fetchClusters(): Promise<void>
```

### news.ts - Store des news et réseaux sociaux

Gestion des articles de news et posts sociaux.

**State** :

```typescript
{
  news: News[],
  socialPosts: SocialPost[],
  loading: boolean,
  error: string | null
}
```

**Getters** :

```typescript
// News filtrées par sentiment
getNewsBySentiment(sentiment: 'positive' | 'neutral' | 'negative'): News[]

// Posts filtrés par plateforme
getSocialPostsByPlatform(platform: string): SocialPost[]

// Sentiment moyen de toutes les news
averageNewsSentiment: number

// Top 5 des coins les plus mentionnés
topMentionedCoins: { coin: string, count: number }[]
```

**Actions** :

```typescript
async fetchLatestNews(limit?: number): Promise<void>
async fetchSocialPosts(platform?: string, limit?: number): Promise<void>
```

---

## Composables

### usePolling.ts

Composable pour gérer le polling HTTP automatique.

**Signature** :

```typescript
function usePolling(
  callback: () => void | Promise<void>,
  interval: number = 30000
): {
  isPolling: Ref<boolean>
  start: () => void
  stop: () => void
  restart: () => void
}
```

**Paramètres** :
- `callback` : Fonction à exécuter périodiquement
- `interval` : Intervalle en millisecondes (défaut : 30000 = 30s)

**Retour** :
- `isPolling` : État du polling (actif/inactif)
- `start()` : Démarrer le polling
- `stop()` : Arrêter le polling
- `restart()` : Redémarrer le polling

**Caractéristiques** :
- Exécution immédiate au démarrage
- Nettoyage automatique au démontage du composant
- Gestion des erreurs dans le callback

**Exemple d'utilisation** :

```vue
<script setup lang="ts">
import { usePolling } from '@/composables/usePolling'
import { useCryptoStore } from '@/stores/crypto'

const cryptoStore = useCryptoStore()

// Polling toutes les 30 secondes
const { isPolling, start, stop } = usePolling(async () => {
  await cryptoStore.fetchLatestPrices(50)
}, 30000)

// Démarrer au montage
onMounted(() => {
  start()
})

// Le polling s'arrête automatiquement au démontage
</script>
```

### useFormatting.ts

Composable pour le formatage de nombres et dates.

**Fonctions disponibles** :

```typescript
// Formater un prix en devise
formatPrice(value: number): string
// Exemple: 1234.56 → "$1,234.56"

// Formater un nombre large (market cap, volume)
formatNumber(value: number): string
// Exemple: 1234567890 → "$1.23B"

// Formater un pourcentage
formatPercent(value: number): string
// Exemple: 0.0256 → "+2.56%"

// Formater une date en relatif
formatDate(date: Date | string): string
// Exemple: "il y a 5 minutes", "il y a 2 heures"

// Formater une date complète
formatDateTime(date: Date | string): string
// Exemple: "12 janv. 2025 à 14:30"
```

**Exemple d'utilisation** :

```vue
<script setup lang="ts">
import { useFormatting } from '@/composables/useFormatting'

const { formatPrice, formatPercent, formatNumber, formatDate } = useFormatting()

const price = 45678.90
const change = 0.0234
const marketCap = 123456789000
const timestamp = new Date()
</script>

<template>
  <div>
    <p>Prix: {{ formatPrice(price) }}</p>
    <p>Variation: {{ formatPercent(change) }}</p>
    <p>Market Cap: {{ formatNumber(marketCap) }}</p>
    <p>Mis à jour: {{ formatDate(timestamp) }}</p>
  </div>
</template>
```

---

## Styling et Design

### Système de design

Le frontend utilise un système de design moderne avec :

1. **Dark Theme** : Palette de couleurs sombres (gray-900, gray-800)
2. **Glassmorphisme** : Effets de verre avec `backdrop-blur`
3. **Gradients** : Dégradés colorés sur les titres et boutons
4. **Animations** : Transitions fluides et hover effects

### Palette de couleurs

**Couleurs principales** :

```css
/* Primary (Cyan-Blue) */
--primary-500: #06b6d4  /* Cyan */
--primary-600: #2563eb  /* Blue */

/* Success */
--success: #10b981      /* Green */

/* Danger */
--danger: #ef4444       /* Red */

/* Warning */
--warning: #f59e0b      /* Orange */

/* Backgrounds */
--bg-dark: #111827      /* Gray-900 */
--bg-darker: #1f2937    /* Gray-800 */
```

**Gradients prédéfinis** :

```css
/* Dashboard title */
bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500

/* Analytics title */
bg-gradient-to-r from-purple-500 via-pink-500 to-red-500

/* News title */
bg-gradient-to-r from-blue-500 via-cyan-500 to-teal-500

/* Landing hero */
bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900
```

### Classes CSS personnalisées

**Glass Cards** :

```css
.glass-card {
  @apply bg-gray-800/50 backdrop-blur-lg rounded-2xl border border-gray-700/50
         shadow-xl hover:shadow-2xl transition-all duration-300
         hover:border-cyan-500/50;
}
```

**Card Headers** :

```css
.card-header {
  @apply flex items-center justify-between p-4;
}

.card-title {
  @apply text-lg font-bold text-white;
}
```

**Stat Cards** :

```css
.stat-card {
  @apply bg-gradient-to-br from-cyan-500/10 to-blue-500/10
         backdrop-blur-lg rounded-xl p-6 border border-cyan-500/20
         hover:border-cyan-400/40 transition-all duration-300
         hover:scale-105;
}
```

**Crypto Items** :

```css
.crypto-item {
  @apply flex items-center justify-between p-3 rounded-lg
         bg-gray-700/30 hover:bg-gray-700/50 transition-all duration-200
         border border-gray-600/20 hover:border-cyan-500/30;
}
```

### Animations

**Fade transitions** :

```css
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
```

**Gradient animation** :

```css
@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.animate-gradient {
  background-size: 200% 200%;
  animation: gradient-shift 3s ease infinite;
}
```

**Float animation** (landing page) :

```css
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  33% { transform: translateY(-20px) rotate(5deg); }
  66% { transform: translateY(-10px) rotate(-5deg); }
}
```

**Staggered animations** :

```typescript
// Dans le template
<div
  v-for="(item, index) in items"
  :style="{ animationDelay: `${index * 0.1}s` }"
  class="animate-fade-in"
>
```

### Responsive Design

Breakpoints Tailwind CSS utilisés :

- `sm:` : 640px et plus
- `md:` : 768px et plus
- `lg:` : 1024px et plus
- `xl:` : 1280px et plus

Exemple de layout responsive :

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  <!-- 1 colonne sur mobile, 2 sur tablette, 4 sur desktop -->
</div>
```

---

## Développement

### Installation

```bash
# Installer les dépendances
cd frontend
npm install
```

### Scripts disponibles

```bash
# Démarrer le serveur de développement (port 3000)
npm run dev

# Builder pour la production
npm run build

# Preview du build de production
npm run preview

# Type-checking TypeScript
npm run type-check

# Linter avec ESLint
npm run lint
```

### Variables d'environnement de développement

Créer un fichier `.env.development` :

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_CRYPTO_POLL_INTERVAL=30000
VITE_NEWS_POLL_INTERVAL=300000
VITE_ANALYTICS_POLL_INTERVAL=60000
```

### Hot Module Replacement (HMR)

Vite fournit un HMR ultra-rapide :
- Les modifications de composants Vue sont appliquées instantanément
- L'état de l'application est préservé
- Pas de rechargement complet de la page

### Debugging

#### Vue DevTools

**Note** : Le plugin `vite-plugin-vue-devtools` est désactivé dans `vite.config.ts` en raison d'un conflit avec `localStorage` en contexte Node.js.

Pour débugger, utiliser l'extension navigateur **Vue DevTools** :
- Chrome : [Vue.js devtools](https://chrome.google.com/webstore/detail/vuejs-devtools)
- Firefox : [Vue.js devtools](https://addons.mozilla.org/fr/firefox/addon/vue-js-devtools/)

#### Console Logging

Les stores Pinia peuvent être inspectés dans la console :

```typescript
// Dans le composant
import { useCryptoStore } from '@/stores/crypto'

const cryptoStore = useCryptoStore()
console.log('Store state:', cryptoStore.$state)
console.log('Gainers:', cryptoStore.gainers)
```

#### Network Tab

Vérifier les appels API dans l'onglet Network des DevTools :
- Filtrer par "XHR" ou "Fetch"
- Vérifier les status codes (200, 400, 500...)
- Inspecter les réponses JSON

### Bonnes pratiques

#### Composition API

Utiliser `<script setup>` pour une syntaxe concise :

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)

onMounted(() => {
  console.log('Component mounted')
})
</script>
```

#### TypeScript

Typer toutes les props et variables :

```typescript
interface Props {
  title: string
  count?: number  // Optionnel
}

const props = withDefaults(defineProps<Props>(), {
  count: 0  // Valeur par défaut
})
```

#### Composables

Extraire la logique réutilisable dans des composables :

```typescript
// composables/useCounter.ts
export function useCounter() {
  const count = ref(0)
  const increment = () => count.value++
  return { count, increment }
}

// Dans le composant
const { count, increment } = useCounter()
```

#### Async/Await

Toujours gérer les erreurs des requêtes API :

```typescript
try {
  const data = await api.getLatestPrices()
  // Traiter les données
} catch (error) {
  console.error('Erreur:', error)
  // Afficher un message d'erreur à l'utilisateur
}
```

---

## Déploiement

### Build de production

```bash
# Builder l'application
npm run build

# Les fichiers générés sont dans /dist
```

### Structure du build

```
dist/
├── assets/           # JS, CSS, et assets optimisés
│   ├── index-[hash].js
│   ├── index-[hash].css
│   └── ...
├── index.html       # Point d'entrée HTML
└── ...
```

### Déploiement avec Docker

Le projet inclut un `Dockerfile` multi-stage :

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

**Builder l'image** :

```bash
docker build -t crypto-viz-frontend .
```

**Lancer le container** :

```bash
docker run -p 3000:3000 crypto-viz-frontend
```

### Variables d'environnement en production

Les variables `VITE_*` sont injectées au moment du build. Pour un déploiement flexible, utiliser un script de remplacement ou des variables d'environnement du système :

```bash
# Définir la variable avant le build
export VITE_API_BASE_URL=https://api.production.com
npm run build
```

### Optimisations de production

Vite optimise automatiquement :
- **Minification** : CSS et JS minifiés
- **Tree-shaking** : Suppression du code non utilisé
- **Code splitting** : Chargement lazy des routes
- **Asset hashing** : Cache busting automatique
- **Compression** : Gzip/Brotli via Nginx

### Nginx Configuration

Configuration Nginx recommandée (`nginx.conf`) :

```nginx
server {
    listen 3000;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Compression
    gzip on;
    gzip_types text/css application/javascript application/json;

    # Cache des assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Déploiement sur le cloud

#### Vercel / Netlify

1. Connecter le repo GitHub
2. Configurer les variables d'environnement
3. Build command : `npm run build`
4. Output directory : `dist`

#### AWS S3 + CloudFront

1. Builder l'application : `npm run build`
2. Upload les fichiers de `dist/` vers un bucket S3
3. Configurer CloudFront pour servir depuis S3
4. Configurer les règles de redirection pour le SPA

#### Docker Compose

Le projet inclut un `docker-compose.yml` complet avec backend :

```bash
# Démarrer tous les services
docker-compose up -d

# Frontend accessible sur http://localhost:3000
# Backend accessible sur http://localhost:8000
```

---

## Troubleshooting

### Problèmes courants

#### Le dev server ne démarre pas

**Erreur** : `localStorage.getItem is not a function`

**Solution** : Vérifier que `vueDevTools()` est commenté dans `vite.config.ts`

```typescript
export default defineConfig({
  plugins: [
    vue(),
    // vueDevTools(), // Désactivé
  ],
})
```

#### Tailwind CSS ne fonctionne pas

**Erreur** : PostCSS plugin error

**Solution** : Utiliser Tailwind CSS 3.x et `postcss.config.js` en CommonJS :

```javascript
// postcss.config.cjs
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

#### Heroicons import error

**Erreur** : `The requested module does not provide an export named 'TrendingUpIcon'`

**Solution** : Utiliser les noms corrects d'icônes :

```typescript
import {
  ArrowTrendingUpIcon,   // ✅ Correct
  ArrowTrendingDownIcon  // ✅ Correct
} from '@heroicons/vue/24/outline'
```

#### API calls failing

**Erreur** : CORS error ou 404

**Vérifications** :
1. Backend est-il démarré ? (`http://localhost:8000`)
2. `VITE_API_BASE_URL` est-elle correcte dans `.env` ?
3. CORS configuré sur le backend ?

```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Build fails

**Erreur** : TypeScript type errors

**Solution** : Exécuter le type-check :

```bash
npm run type-check
```

Corriger les erreurs TypeScript avant de builder.

### Logs et debugging

#### Vérifier les logs Vite

```bash
npm run dev -- --debug
```

#### Inspecter le bundle

```bash
npm run build -- --debug

# Analyser la taille du bundle
npx vite-bundle-visualizer
```

#### Tester le build de production localement

```bash
npm run build
npm run preview
# Ouvre http://localhost:4173
```

---

## Ressources

### Documentation officielle

- [Vue 3](https://vuejs.org/)
- [Vite](https://vitejs.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [Pinia](https://pinia.vuejs.org/)
- [Vue Router](https://router.vuejs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Chart.js](https://www.chartjs.org/)
- [Heroicons](https://heroicons.com/)

### Outils

- [Vue DevTools](https://devtools.vuejs.org/)
- [Vite Plugin Inspect](https://github.com/antfu/vite-plugin-inspect)
- [ESLint](https://eslint.org/)

### Communauté

- [Vue Discord](https://chat.vuejs.org/)
- [Stack Overflow - Vue.js](https://stackoverflow.com/questions/tagged/vue.js)
- [GitHub Discussions](https://github.com/vuejs/core/discussions)

---

## Support

Pour toute question ou problème :

1. Vérifier cette documentation
2. Consulter le fichier `CLAUDE.md` à la racine du projet
3. Vérifier les issues GitHub du projet
4. Contacter l'équipe de développement

---

**Dernière mise à jour** : Janvier 2025
**Version** : 1.0.0
**Auteurs** : EPITECH MSc Pro - Promo 2026
