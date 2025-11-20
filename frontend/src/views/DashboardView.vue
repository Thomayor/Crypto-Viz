<template>
  <div class="dashboard-view">
    <!-- Header -->
    <div class="header-section mb-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-600 mb-2">
            Crypto Market Dashboard
          </h1>
          <p class="text-gray-400 flex items-center gap-2">
            <span class="relative flex h-3 w-3">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            Live market data updating every 30 seconds
          </p>
        </div>
        <div v-if="cryptoStore.lastUpdate" class="text-right">
          <div class="text-sm text-gray-500">Last update</div>
          <div class="text-lg font-semibold text-gray-300">
            {{ formatDate(cryptoStore.lastUpdate) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="cryptoStore.loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" />
    </div>

    <div v-else>
      <!-- Stats Cards with TailAdmin Style -->
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
        <StatsCard
          label="Total Market Cap"
          :value="cryptoStore.totalMarketCap"
          :change="2.5"
          :icon="ChartBarIcon"
          icon-color="cyan"
          :trend="marketCapTrend"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">vs yesterday</span>
              <span class="text-green-400 font-semibold">+$12.5B</span>
            </div>
          </template>
        </StatsCard>

        <StatsCard
          label="24h Volume"
          :value="cryptoStore.totalVolume24h"
          :change="1.8"
          :icon="CurrencyDollarIcon"
          icon-color="green"
          :trend="volumeTrend"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">Active trades</span>
              <span class="text-cyan-400 font-semibold">{{ cryptoStore.prices.length }} coins</span>
            </div>
          </template>
        </StatsCard>

        <StatsCard
          label="Market Sentiment"
          :value="formatSentiment(averageSentimentScore)"
          :change="0.5"
          :icon="FaceSmileIcon"
          :icon-color="averageSentimentScore >= 0.6 ? 'green' : averageSentimentScore >= 0.4 ? 'yellow' : 'red'"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">Confidence</span>
              <span class="text-white font-semibold">{{ (averageSentimentScore * 100).toFixed(0) }}%</span>
            </div>
          </template>
        </StatsCard>

        <StatsCard
          label="Active Alerts"
          :value="(analyticsStore.criticalAnomalies?.length || 0).toString()"
          :change="-15.2"
          :icon="ExclamationTriangleIcon"
          icon-color="red"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">Critical anomalies</span>
              <span class="text-red-400 font-semibold">{{ analyticsStore.anomalies?.filter(a => a.severity === 'critical').length || 0 }}</span>
            </div>
          </template>
        </StatsCard>
      </div>

      <!-- Market Indicators -->
      <div class="glass-card p-6 mb-8">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h3 class="text-2xl font-bold text-white flex items-center gap-2">
              <ChartBarIcon class="h-7 w-7 text-cyan-400" />
              Market Indicators
            </h3>
            <p class="text-sm text-gray-400 mt-1">Key technical indicators and market sentiment</p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- BTC Dominance -->
          <div class="bg-gradient-to-br from-gray-800/60 to-gray-900/60 rounded-xl p-6 border border-gray-700/50 hover:border-purple-500/30 transition-all">
            <div class="flex items-center justify-between mb-4">
              <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Bitcoin Dominance</div>
              <div class="p-2 bg-purple-500/10 rounded-lg">
                <ChartBarIcon class="h-5 w-5 text-purple-400" />
              </div>
            </div>
            <div class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400 mb-3">
              {{ btcDominance }}%
            </div>
            <div class="space-y-2">
              <div class="flex-1 bg-gray-700/50 rounded-full h-2 overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500"
                  :style="{ width: `${btcDominance}%` }"
                ></div>
              </div>
              <div class="text-xs text-gray-500">{{ (100 - btcDominance).toFixed(1) }}% altcoins</div>
            </div>
          </div>

          <!-- Average RSI -->
          <div class="bg-gradient-to-br from-gray-800/60 to-gray-900/60 rounded-xl p-6 border border-gray-700/50 hover:border-orange-500/30 transition-all">
            <div class="flex items-center justify-between mb-4">
              <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Avg. RSI (14)</div>
              <div class="p-2 bg-orange-500/10 rounded-lg">
                <ChartBarIcon class="h-5 w-5 text-orange-400" />
              </div>
            </div>
            <div class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-400 mb-3">
              {{ averageRSI }}
            </div>
            <div class="space-y-2">
              <div class="flex-1 bg-gray-700/50 rounded-full h-2 overflow-hidden">
                <div
                  :class="[
                    'h-full rounded-full transition-all duration-500',
                    averageRSI >= 70 ? 'bg-gradient-to-r from-red-500 to-red-600' :
                    averageRSI >= 50 ? 'bg-gradient-to-r from-orange-500 to-yellow-500' :
                    averageRSI >= 30 ? 'bg-gradient-to-r from-yellow-500 to-green-500' :
                    'bg-gradient-to-r from-green-500 to-green-600'
                  ]"
                  :style="{ width: `${averageRSI}%` }"
                ></div>
              </div>
              <div class="text-xs text-gray-500">
                {{ averageRSI >= 70 ? 'Overbought' : averageRSI >= 50 ? 'Neutral-High' : averageRSI >= 30 ? 'Neutral-Low' : 'Oversold' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Grid with ApexCharts -->
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
        <!-- Price Chart -->
        <div class="glass-card p-6">
          <div class="mb-6 flex items-start justify-between">
            <div class="flex-1">
              <h3 class="text-xl font-bold text-white mb-1">
                {{ selectedChartCoin ? (cryptoStore.prices.find(c => c.symbol === selectedChartCoin)?.name || selectedChartCoin.toUpperCase()) : 'Bitcoin' }} Price Evolution
              </h3>
              <p class="text-sm text-gray-400">Last 24 hours price movement</p>
            </div>
            <select
              v-model="selectedChartCoin"
              @change="handleChartCoinChange"
              class="px-3 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white text-sm
                     hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent
                     transition-all duration-200"
            >
              <option
                v-for="coin in cryptoStore.prices.slice(0, 20)"
                :key="coin.id"
                :value="coin.symbol"
              >
                {{ coin.name }} ({{ coin.symbol.toUpperCase() }})
              </option>
            </select>
          </div>
          <ApexAreaChart
            v-if="priceHistoryData.length > 0"
            :data="priceHistoryData"
            :colors="['#06B6D4', '#3B82F6']"
            :height="300"
            y-axis-label="Price (USD)"
          />
          <div v-else class="flex items-center justify-center h-[300px] text-gray-400">
            Loading price data...
          </div>
        </div>

        <!-- Market Overview -->
        <div class="glass-card p-6">
          <div class="mb-6">
            <h3 class="text-xl font-bold text-white mb-1">Market Distribution</h3>
            <p class="text-sm text-gray-400">Top cryptocurrencies by market cap</p>
          </div>
          <DoughnutChart
            v-if="cryptoStore.prices.length > 0"
            :data="marketDistributionData"
            title="Market Share"
          />
        </div>
      </div>

      <!-- Top Gainers & Losers -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <!-- Top Gainers -->
        <div class="glass-card p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-xl font-bold text-white flex items-center gap-2">
                <ArrowTrendingUpIcon class="h-6 w-6 text-green-400" />
                Top Gainers (24h)
              </h3>
              <p class="text-sm text-gray-400 mt-1">Best performing cryptocurrencies</p>
            </div>
          </div>

          <div class="space-y-3">
            <div
              v-for="(coin, index) in cryptoStore.gainers.slice(0, 5)"
              :key="coin.id"
              class="crypto-item-card"
              :style="{ animationDelay: `${index * 0.05}s` }"
            >
              <div class="flex items-center gap-3 flex-1">
                <div class="rank-badge">{{ index + 1 }}</div>
                <img
                  v-if="coin.image"
                  :src="coin.image"
                  :alt="coin.name"
                  class="w-10 h-10 rounded-full ring-2 ring-green-500/20"
                />
                <div class="flex-1 min-w-0">
                  <div class="font-semibold text-white">{{ coin.name }}</div>
                  <div class="text-xs text-gray-400 uppercase">{{ coin.symbol }}</div>
                </div>
              </div>

              <div class="text-right">
                <div class="text-white font-semibold">{{ formatPrice(coin.current_price) }}</div>
                <div class="flex items-center gap-1 text-green-400 text-sm font-semibold justify-end">
                  <ArrowTrendingUpIcon class="h-4 w-4" />
                  {{ formatPercent(coin.price_change_percentage_24h) }}
                </div>
              </div>
            </div>

            <div v-if="cryptoStore.gainers.length === 0" class="text-center py-8 text-gray-400">
              No gainers data available
            </div>
          </div>
        </div>

        <!-- Top Losers -->
        <div class="glass-card p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-xl font-bold text-white flex items-center gap-2">
                <ArrowTrendingDownIcon class="h-6 w-6 text-red-400" />
                Top Losers (24h)
              </h3>
              <p class="text-sm text-gray-400 mt-1">Worst performing cryptocurrencies</p>
            </div>
          </div>

          <div class="space-y-3">
            <div
              v-for="(coin, index) in cryptoStore.losers.slice(0, 5)"
              :key="coin.id"
              class="crypto-item-card"
              :style="{ animationDelay: `${index * 0.05}s` }"
            >
              <div class="flex items-center gap-3 flex-1">
                <div class="rank-badge bg-red-500/20 text-red-400">{{ index + 1 }}</div>
                <img
                  v-if="coin.image"
                  :src="coin.image"
                  :alt="coin.name"
                  class="w-10 h-10 rounded-full ring-2 ring-red-500/20"
                />
                <div class="flex-1 min-w-0">
                  <div class="font-semibold text-white">{{ coin.name }}</div>
                  <div class="text-xs text-gray-400 uppercase">{{ coin.symbol }}</div>
                </div>
              </div>

              <div class="text-right">
                <div class="text-white font-semibold">{{ formatPrice(coin.current_price) }}</div>
                <div class="flex items-center gap-1 text-red-400 text-sm font-semibold justify-end">
                  <ArrowTrendingDownIcon class="h-4 w-4" />
                  {{ formatPercent(Math.abs(coin.price_change_percentage_24h)) }}
                </div>
              </div>
            </div>

            <div v-if="cryptoStore.losers.length === 0" class="text-center py-8 text-gray-400">
              No losers data available
            </div>
          </div>
        </div>
      </div>

      <!-- Crypto Grid with Clickable Cards -->
      <div class="mb-8">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-2xl font-bold text-white">All Cryptocurrencies</h2>
            <p class="text-sm text-gray-400 mt-1">Click on any card to view detailed information</p>
          </div>
          <div class="text-sm text-gray-400">
            Showing {{ displayedCryptos }} of {{ cryptoStore.prices.length }} coins
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 mb-6">
          <CryptoCard
            v-for="crypto in cryptoStore.prices.slice(0, displayedCryptos)"
            :key="crypto.id"
            :crypto="crypto"
          />
        </div>

        <!-- Load More Button -->
        <div v-if="displayedCryptos < cryptoStore.prices.length" class="flex justify-center">
          <button
            @click="displayedCryptos += 20"
            class="px-8 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold rounded-lg transition-all duration-200 hover:shadow-lg hover:shadow-cyan-500/50"
          >
            Load More Cryptocurrencies
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useCryptoStore } from '@/stores/crypto'
import { useAnalyticsStore } from '@/stores/analytics'
import { useFormatting } from '@/composables/useFormatting'
import { usePolling } from '@/composables/usePolling'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import StatsCard from '@/components/ui/StatsCard.vue'
import CryptoCard from '@/components/ui/CryptoCard.vue'
import ApexAreaChart from '@/components/charts/ApexAreaChart.vue'
import DoughnutChart from '@/components/charts/DoughnutChart.vue'
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  FaceSmileIcon,
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  ArrowUpIcon,
  ArrowDownIcon,
} from '@heroicons/vue/24/outline'

const cryptoStore = useCryptoStore()
const analyticsStore = useAnalyticsStore()

const {
  formatPrice,
  formatNumber,
  formatPercent,
  formatDate
} = useFormatting()

// Number of displayed cryptos (for load more functionality)
const displayedCryptos = ref(20)

// Polling for real-time updates
usePolling(async () => {
  await cryptoStore.fetchLatestPrices(50)
}, 30000)

usePolling(async () => {
  await analyticsStore.fetchAnomalies()
}, 60000)

// Computed properties
const averageSentimentScore = computed(() => {
  if (!analyticsStore.sentiment || analyticsStore.sentiment.length === 0) return 0.5
  const sum = analyticsStore.sentiment.reduce((acc, s) => acc + (s.average_sentiment || 0), 0)
  return sum / analyticsStore.sentiment.length
})

const formatSentiment = (score: number) => {
  if (score >= 0.7) return 'Very Bullish'
  if (score >= 0.6) return 'Bullish'
  if (score >= 0.4) return 'Neutral'
  if (score >= 0.3) return 'Bearish'
  return 'Very Bearish'
}

// BTC Dominance calculation
const btcDominance = computed(() => {
  const bitcoin = cryptoStore.prices.find(c => c.symbol === 'BTC' || c.symbol === 'btc')
  if (!bitcoin || !bitcoin.market_cap) return 0

  const totalMarketCap = cryptoStore.prices.reduce((sum, coin) => sum + (coin.market_cap || 0), 0)
  return totalMarketCap > 0 ? parseFloat(((bitcoin.market_cap / totalMarketCap) * 100).toFixed(1)) : 0
})

// Average RSI calculation (Relative Strength Index)
const averageRSI = computed(() => {
  if (cryptoStore.prices.length === 0) return 50

  // Calculate RSI based on 24h price changes
  const gains: number[] = []
  const losses: number[] = []

  cryptoStore.prices.forEach(coin => {
    const change = coin.price_change_percentage_24h || 0
    if (change > 0) {
      gains.push(change)
    } else if (change < 0) {
      losses.push(Math.abs(change))
    }
  })

  if (gains.length === 0 && losses.length === 0) return 50

  const avgGain = gains.length > 0 ? gains.reduce((a, b) => a + b, 0) / gains.length : 0
  const avgLoss = losses.length > 0 ? losses.reduce((a, b) => a + b, 0) / losses.length : 0

  if (avgLoss === 0) return 100
  const rs = avgGain / avgLoss
  const rsi = 100 - (100 / (1 + rs))

  return parseFloat(rsi.toFixed(1))
})

// Mock trend data for sparklines
const marketCapTrend = ref([1.2, 1.3, 1.25, 1.4, 1.5, 1.45, 1.6, 1.7])
const volumeTrend = ref([100, 110, 95, 120, 130, 125, 140, 150])
const selectedChartCoin = ref('BTC')

// Market distribution data for doughnut chart
const marketDistributionData = computed(() => {
  if (cryptoStore.prices.length === 0) return []

  // Theme colors: cyan -> blue -> purple gradient
  const colors = ['#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6']

  return cryptoStore.prices.slice(0, 5).map((coin, index) => ({
    label: coin.name,
    value: coin.market_cap,
    color: colors[index % colors.length]
  }))
})

// Price history data for chart
const priceHistoryData = computed(() => {
  if (cryptoStore.prices.length === 0) return []

  // Find selected coin by symbol
  const selectedCoin = cryptoStore.prices.find(c => c.symbol === selectedChartCoin.value)
  if (!selectedCoin) return []

  const now = new Date()
  const data = []

  for (let i = 24; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 3600000) // Hourly data
    const price = selectedCoin.current_price || selectedCoin.price || 0
    const randomVariation = (Math.random() - 0.5) * price * 0.02
    data.push({
      timestamp,
      value: price + randomVariation
    })
  }

  return data
})

// Handle chart coin change
const handleChartCoinChange = () => {
  // The computed property will automatically update when selectedChartCoin changes
  // No need to fetch new data since we're using mock data based on current prices
}

// Initial data fetch
onMounted(async () => {
  await Promise.all([
    cryptoStore.fetchLatestPrices(50),
    analyticsStore.fetchSentiment(),
    analyticsStore.fetchAnomalies()
  ])
})
</script>

<style scoped>
.dashboard-view {
  @apply min-h-screen;
}

.header-section {
  @apply animate-fade-in;
}

.glass-card {
  @apply bg-gray-800/50 backdrop-blur-lg rounded-2xl border border-gray-700/50
         shadow-xl hover:shadow-2xl transition-all duration-300 hover:border-cyan-500/30;
}

.crypto-item-card {
  @apply flex items-center justify-between p-4 rounded-xl
         bg-gray-700/30 hover:bg-gray-700/50 transition-all duration-300
         border border-gray-600/20 hover:border-cyan-500/30
         transform hover:scale-[1.02] cursor-pointer
         animate-fade-in;
}

.rank-badge {
  @apply w-8 h-8 flex items-center justify-center rounded-lg
         bg-cyan-500/20 text-cyan-400 font-bold text-sm;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.5s ease-out;
}
</style>
