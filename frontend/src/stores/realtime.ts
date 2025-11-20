import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

interface PriceUpdate {
  coin_id: string
  current_price: number
  price_change_percentage_24h: number
  market_cap: number
  total_volume: number
  timestamp: string
}

interface SentimentUpdate {
  coin_id: string
  sentiment_score: number
  sentiment: 'positive' | 'neutral' | 'negative'
  timestamp: string
}

interface NewsUpdate {
  id: string
  title: string
  description: string
  url: string
  source: string
  sentiment: 'positive' | 'neutral' | 'negative'
  published_at: string
}

interface AnomalyUpdate {
  id: string
  coin_id: string
  anomaly_score: number
  severity: 'critical' | 'high' | 'medium' | 'low'
  description: string
  timestamp: string
}

export const useRealtimeStore = defineStore('realtime', () => {
  // State
  const latestPrices = ref<Map<string, PriceUpdate>>(new Map())
  const latestSentiments = ref<Map<string, SentimentUpdate>>(new Map())
  const latestNews = ref<NewsUpdate[]>([])
  const latestAnomalies = ref<AnomalyUpdate[]>([])
  const connectionMessage = ref('')
  const lastUpdateTime = ref<Date | null>(null)
  const updateCount = ref(0)

  // Computed
  const totalUpdates = computed(() => updateCount.value)

  const recentNews = computed(() => {
    return latestNews.value.slice(0, 10) // Keep only last 10
  })

  const criticalAnomalies = computed(() => {
    return latestAnomalies.value.filter(a => a.severity === 'critical')
  })

  const getPriceForCoin = (coinId: string) => {
    return latestPrices.value.get(coinId)
  }

  const getSentimentForCoin = (coinId: string) => {
    return latestSentiments.value.get(coinId)
  }

  // Actions
  const updatePrice = (data: PriceUpdate) => {
    latestPrices.value.set(data.coin_id, data)
    lastUpdateTime.value = new Date()
    updateCount.value++
  }

  const updateSentiment = (data: SentimentUpdate) => {
    latestSentiments.value.set(data.coin_id, data)
    lastUpdateTime.value = new Date()
    updateCount.value++
  }

  const addNews = (data: NewsUpdate) => {
    // Add to beginning and keep only last 50
    latestNews.value.unshift(data)
    if (latestNews.value.length > 50) {
      latestNews.value = latestNews.value.slice(0, 50)
    }
    lastUpdateTime.value = new Date()
    updateCount.value++
  }

  const addAnomaly = (data: AnomalyUpdate) => {
    // Check if anomaly already exists
    if (!latestAnomalies.value.find(a => a.id === data.id)) {
      latestAnomalies.value.unshift(data)
      // Keep only last 100 anomalies
      if (latestAnomalies.value.length > 100) {
        latestAnomalies.value = latestAnomalies.value.slice(0, 100)
      }
      lastUpdateTime.value = new Date()
      updateCount.value++
    }
  }

  const setConnectionMessage = (message: string) => {
    connectionMessage.value = message
  }

  const clearAll = () => {
    latestPrices.value.clear()
    latestSentiments.value.clear()
    latestNews.value = []
    latestAnomalies.value = []
    connectionMessage.value = ''
    lastUpdateTime.value = null
    updateCount.value = 0
  }

  return {
    // State
    latestPrices,
    latestSentiments,
    latestNews,
    latestAnomalies,
    connectionMessage,
    lastUpdateTime,
    updateCount,

    // Computed
    totalUpdates,
    recentNews,
    criticalAnomalies,
    getPriceForCoin,
    getSentimentForCoin,

    // Actions
    updatePrice,
    updateSentiment,
    addNews,
    addAnomaly,
    setConnectionMessage,
    clearAll
  }
})
