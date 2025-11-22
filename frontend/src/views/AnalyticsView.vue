<template>
  <div class="analytics-view">
    <!-- Header -->
    <div class="header-section mb-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-500 via-pink-500 to-red-500 mb-2">
            ML Analytics & Predictions
          </h1>
          <p class="text-gray-400 flex items-center gap-2">
            <CpuChipIcon class="h-5 w-5 text-purple-400" />
            Machine learning powered insights and anomaly detection
          </p>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="analyticsStore.loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" />
    </div>

    <div v-else>
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
        <StatsCard
          label="Total Predictions"
          :value="(mlStore.predictions?.length || 0).toString()"
          :change="12.5"
          :icon="ChartBarIcon"
          icon-color="purple"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">Confidence</span>
              <span class="text-purple-400 font-semibold">{{ averageConfidence }}%</span>
            </div>
          </template>
        </StatsCard>

        <StatsCard
          label="Active Anomalies"
          :value="(analyticsStore.anomalies?.length || 0).toString()"
          :change="-8.3"
          :icon="ExclamationTriangleIcon"
          icon-color="red"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">Critical</span>
              <span class="text-red-400 font-semibold">{{ analyticsStore.criticalAnomalies?.length || 0 }}</span>
            </div>
          </template>
        </StatsCard>

        <StatsCard
          label="Sentiment Analysis"
          :value="(fearGreedIndex || 0).toFixed(0)"
          :change="2.1"
          :icon="FaceSmileIcon"
          :icon-color="getFearGreedColor(averageSentiment)"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">{{ getSentimentLabel(averageSentiment) }}</span>
              <SentimentMethodBadge method="ollama" :confidence="0.85" :showTooltip="false" />
            </div>
          </template>
        </StatsCard>

        <StatsCard
          label="ML Accuracy"
          value="92.3%"
          :change="1.5"
          :icon="CpuChipIcon"
          icon-color="cyan"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">Model</span>
              <span class="text-cyan-400 font-semibold">LinearReg</span>
            </div>
          </template>
        </StatsCard>
      </div>

      <!-- Coin Selector -->
      <div class="glass-card p-6 mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-bold text-white mb-1">Select Cryptocurrency</h3>
            <p class="text-sm text-gray-400">Choose a coin to view detailed analytics</p>
          </div>
          <select
            v-model="selectedCoin"
            class="select-input"
            @change="handleCoinChange"
          >
            <option value="">All Cryptocurrencies</option>
            <option
              v-for="coin in cryptoStore.prices.slice(0, 20)"
              :key="coin.id"
              :value="coin.symbol"
            >
              {{ coin.name }} ({{ coin.symbol.toUpperCase() }})
            </option>
          </select>
        </div>
      </div>

      <!-- Charts Grid -->
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
        <!-- Price Prediction Chart -->
        <div class="glass-card p-6">
          <div class="mb-6">
            <h3 class="text-xl font-bold text-white mb-1">Price Prediction</h3>
            <p class="text-sm text-gray-400">ML-powered price forecasting</p>
          </div>
          <ApexLineChart
            v-if="predictionChartData.length > 0"
            :data="predictionChartData"
            color="#A855F7"
            :height="300"
            y-axis-label="Predicted Price"
            :smooth="true"
          />
          <div v-else class="flex flex-col items-center justify-center h-[300px] text-center px-8">
            <ExclamationCircleIcon class="h-16 w-16 text-gray-500 mb-4" />
            <p class="text-lg font-semibold text-gray-300 mb-2">Aucune prédiction disponible</p>
            <p class="text-sm text-gray-400">
              {{ selectedCoin
                ? `Désolé, il n'y a pas de prédictions de prix ML pour ${selectedCoin.toUpperCase()} sur les dernières 24 heures.`
                : 'Désolé, il n\'y a pas de prédictions de prix ML sur les dernières 24 heures.'
              }}
            </p>
          </div>
        </div>

        <!-- Fear & Greed Gauge -->
        <div class="glass-card p-6">
          <div class="mb-6">
            <h3 class="text-xl font-bold text-white mb-1">Fear & Greed Index</h3>
            <p class="text-sm text-gray-400">What emotion is driving the market now?</p>
          </div>
          <FearGreedGauge
            v-if="analyticsStore.sentiment && analyticsStore.sentiment.length > 0"
            :value="fearGreedIndex"
            :data-points="totalArticles"
            :ollama-analyzed="ollamaAnalyzed"
            :avg-confidence="avgConfidence"
          />
          <div v-else class="flex flex-col items-center justify-center h-[300px] text-center px-8">
            <ExclamationCircleIcon class="h-16 w-16 text-gray-500 mb-4" />
            <p class="text-lg font-semibold text-gray-300 mb-2">Aucune donnée disponible</p>
            <p class="text-sm text-gray-400">
              {{ selectedCoin
                ? `Désolé, il n'y a pas de données d'analyse de sentiment pour ${selectedCoin.toUpperCase()} sur les dernières 24 heures.`
                : 'Désolé, il n\'y a pas de données d\'analyse de sentiment sur les dernières 24 heures.'
              }}
            </p>
          </div>
        </div>
      </div>

      <!-- ML Price Predictions Component -->
      <div class="glass-card p-6 mb-8">
        <PredictionChart />
      </div>

      <!-- Correlation Matrix Component -->
      <div class="glass-card p-6 mb-8">
        <CorrelationMatrix />
      </div>

      <!-- ML Anomaly Alerts Component (replaces old anomalies section) -->
      <div class="mb-8">
        <AnomalyAlerts />
      </div>

      <!-- Anomalies Section -->
      <div class="glass-card p-6 mb-8">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h3 class="text-xl font-bold text-white mb-1">Detected Anomalies</h3>
            <p class="text-sm text-gray-400">Unusual market patterns and behaviors</p>
          </div>
          <div class="flex gap-2">
            <button
              v-for="severity in ['all', 'critical', 'high', 'medium', 'low']"
              :key="severity"
              @click="selectedSeverity = severity"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                selectedSeverity === severity
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
              ]"
            >
              {{ severity.charAt(0).toUpperCase() + severity.slice(1) }}
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <div
            v-for="(anomaly, index) in filteredAnomalies.slice(0, 9)"
            :key="anomaly.metadata?.id || index"
            class="anomaly-card"
            :style="{ animationDelay: `${index * 0.05}s` }"
          >
            <div class="flex items-start justify-between mb-3">
              <div :class="['severity-badge', getSeverityClass(anomaly.severity)]">
                <ExclamationTriangleIcon class="h-4 w-4" />
                {{ anomaly.severity }}
              </div>
              <div class="text-xs text-gray-400">
                {{ formatDate(anomaly.detected_at) }}
              </div>
            </div>

            <h4 class="font-semibold text-white mb-2">{{ anomaly.symbol }}</h4>
            <p class="text-sm text-gray-400 mb-3">{{ anomaly.description }}</p>

            <div class="flex items-center justify-between pt-3 border-t border-gray-700/50">
              <div class="text-xs text-gray-500">Anomaly Score</div>
              <div class="text-sm font-bold text-white">{{ (anomaly.metadata?.anomaly_score || 0).toFixed(2) }}</div>
            </div>
          </div>

          <div v-if="filteredAnomalies.length === 0" class="col-span-full text-center py-12 text-gray-400">
            No anomalies detected for the selected severity level
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'
import { useMLStore } from '@/stores/ml'
import { useCryptoStore } from '@/stores/crypto'
import { useFormatting } from '@/composables/useFormatting'
import { usePolling } from '@/composables/usePolling'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import StatsCard from '@/components/ui/StatsCard.vue'
import ApexLineChart from '@/components/charts/ApexLineChart.vue'
import FearGreedGauge from '@/components/charts/FearGreedGauge.vue'
import SentimentMethodBadge from '@/components/SentimentMethodBadge.vue'
import PredictionChart from '@/components/ml/PredictionChart.vue'
import CorrelationMatrix from '@/components/ml/CorrelationMatrix.vue'
import AnomalyAlerts from '@/components/ml/AnomalyAlerts.vue'
import {
  ChartBarIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  FaceSmileIcon,
  CpuChipIcon,
} from '@heroicons/vue/24/outline'

const analyticsStore = useAnalyticsStore()
const mlStore = useMLStore()
const cryptoStore = useCryptoStore()
const { formatDate } = useFormatting()

const selectedCoin = ref('')
const selectedSeverity = ref('all')

// Polling
usePolling(async () => {
  await Promise.all([
    mlStore.fetchPredictions(selectedCoin.value || undefined),
    analyticsStore.fetchAnomalies(selectedCoin.value || undefined),
    analyticsStore.fetchSentiment(selectedCoin.value || undefined)
  ])
}, 60000)

// Computed properties
const averageSentiment = computed(() => {
  if (!analyticsStore.sentiment || analyticsStore.sentiment.length === 0) return 0.5
  const sum = analyticsStore.sentiment.reduce((acc, s) => acc + (s.average_sentiment || 0), 0)
  return sum / analyticsStore.sentiment.length
})

// Convert sentiment to Fear & Greed index (0-100)
const fearGreedIndex = computed(() => {
  return ((averageSentiment.value + 1) / 2) * 100
})

const getSentimentLabel = (score: number) => {
  // Convert to 0-100 scale
  const index = ((score + 1) / 2) * 100

  if (index <= 25) return 'Extreme Fear'
  if (index <= 45) return 'Fear'
  if (index <= 55) return 'Neutral'
  if (index <= 75) return 'Greed'
  return 'Extreme Greed'
}

const getFearGreedColor = (score: number) => {
  const index = ((score + 1) / 2) * 100

  if (index <= 25) return 'red'
  if (index <= 45) return 'orange'
  if (index <= 55) return 'yellow'
  if (index <= 75) return 'green'
  return 'cyan'
}

// Statistics for gauge
const totalArticles = computed(() => {
  if (!analyticsStore.sentiment || analyticsStore.sentiment.length === 0) return 0
  return analyticsStore.sentiment.reduce((sum, s) => sum + (s.total_count || 0), 0)
})

const ollamaAnalyzed = computed(() => {
  if (!analyticsStore.sentiment || analyticsStore.sentiment.length === 0) return 0
  return analyticsStore.sentiment.reduce((sum, s) => sum + (s.ollama_analyzed || 0), 0)
})

const avgConfidence = computed(() => {
  if (!analyticsStore.sentiment || analyticsStore.sentiment.length === 0) return 0
  const withConfidence = analyticsStore.sentiment.filter(s => s.avg_confidence !== null && s.avg_confidence !== undefined)
  if (withConfidence.length === 0) return 0
  const sum = withConfidence.reduce((acc, s) => acc + (s.avg_confidence || 0), 0)
  return sum / withConfidence.length
})

const filteredAnomalies = computed(() => {
  if (!analyticsStore.anomalies) return []
  if (selectedSeverity.value === 'all') {
    return analyticsStore.anomalies
  }
  return analyticsStore.anomalies.filter(a => a.severity === selectedSeverity.value)
})

const getSeverityClass = (severity: string) => {
  const classes = {
    critical: 'severity-critical',
    high: 'severity-high',
    medium: 'severity-medium',
    low: 'severity-low'
  }
  return classes[severity as keyof typeof classes] || 'severity-low'
}

// Chart data
const predictionChartData = computed(() => {
  // Use mlStore instead of analyticsStore
  if (!mlStore.predictions || mlStore.predictions.length === 0) return []

  // Filter predictions by selected coin if any
  let predictions = mlStore.predictions
  if (selectedCoin.value) {
    predictions = predictions.filter((p: any) => p.symbol === selectedCoin.value.toUpperCase())
  }

  if (predictions.length === 0) return []

  // Filter only price predictions and map to chart format
  return predictions
    .filter((p: any) => p.prediction_type === 'price')
    .map((p: any) => ({
      timestamp: p.predicted_at,
      value: p.predicted_value
    }))
})

const sentimentChartData = computed(() => {
  if (!analyticsStore.sentiment || analyticsStore.sentiment.length === 0) return []

  return analyticsStore.sentiment.map(s => ({
    timestamp: s.timestamp,
    value: s.average_sentiment || 0 // Keep as -1 to 1, FearGreedChart will convert
  }))
})

// Average confidence for predictions
const averageConfidence = computed(() => {
  try {
    if (!mlStore.predictions || mlStore.predictions.length === 0) return 0
    const validPredictions = mlStore.predictions.filter((p: any) => p && typeof p.confidence === 'number')
    if (validPredictions.length === 0) return 0
    const sum = validPredictions.reduce((acc: number, p: any) => acc + p.confidence, 0)
    return Math.round((sum / validPredictions.length) * 100)
  } catch (error) {
    console.error('Error calculating average confidence:', error)
    return 0
  }
})

const handleCoinChange = async () => {
  await Promise.all([
    mlStore.fetchPredictions(selectedCoin.value || undefined),
    analyticsStore.fetchAnomalies(selectedCoin.value || undefined),
    analyticsStore.fetchSentiment(selectedCoin.value || undefined)
  ])
}

// Initial fetch
onMounted(async () => {
  await Promise.all([
    cryptoStore.fetchLatestPrices(50),
    mlStore.fetchPredictions(),
    analyticsStore.fetchAnomalies(),
    analyticsStore.fetchSentiment()
  ])
})
</script>

<style scoped>
.analytics-view {
  @apply min-h-screen;
}

.header-section {
  @apply animate-fade-in;
}

.glass-card {
  @apply bg-gray-800/50 backdrop-blur-lg rounded-2xl border border-gray-700/50
         shadow-xl hover:shadow-2xl transition-all duration-300 hover:border-purple-500/30;
}

.select-input {
  @apply bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2.5 text-white
         focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500
         transition-all duration-200 cursor-pointer hover:bg-gray-700;
}

.anomaly-card {
  @apply bg-gray-700/30 backdrop-blur-sm rounded-xl p-4 border border-gray-600/30
         hover:border-purple-500/30 transition-all duration-300
         transform hover:scale-[1.02] cursor-pointer
         animate-fade-in;
}

.severity-badge {
  @apply flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase;
}

.severity-critical {
  @apply bg-red-500/20 text-red-400 border border-red-500/30;
}

.severity-high {
  @apply bg-orange-500/20 text-orange-400 border border-orange-500/30;
}

.severity-medium {
  @apply bg-yellow-500/20 text-yellow-400 border border-yellow-500/30;
}

.severity-low {
  @apply bg-blue-500/20 text-blue-400 border border-blue-500/30;
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
