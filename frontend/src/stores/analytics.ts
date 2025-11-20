import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/services/api'
import type { SentimentResult, MLPrediction, Anomaly, AnalyticsResult } from '@/types'

export const useAnalyticsStore = defineStore('analytics', () => {
  const sentiment = ref<SentimentResult[]>([])
  const dailySentiment = ref<SentimentResult[]>([])
  const predictions = ref<Record<string, MLPrediction[]>>({})
  const anomalies = ref<Anomaly[]>([])
  const analyticsResults = ref<AnalyticsResult[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const criticalAnomalies = computed(() =>
    anomalies.value.filter(a => a.severity === 'critical' && !a.resolved)
  )

  const highAnomalies = computed(() =>
    anomalies.value.filter(a => a.severity === 'high' && !a.resolved)
  )

  const activeSentiment = computed(() =>
    sentiment.value.filter(s => s.average_sentiment !== null)
  )

  const overallSentiment = computed(() => {
    if (sentiment.value.length === 0) return null

    const total = sentiment.value.reduce((sum, s) => sum + s.average_sentiment, 0)
    const avg = total / sentiment.value.length

    if (avg >= 0.66) return 'positive'
    if (avg <= 0.33) return 'negative'
    return 'neutral'
  })

  // Actions
  async function fetchSentiment(symbol?: string, timeWindow: '24h' | '7d' | '30d' = '24h') {
    loading.value = true
    error.value = null

    try {
      const response = await api.getSentiment(symbol, timeWindow)
      if (Array.isArray(response)) {
        sentiment.value = response
      } else if (response.sentiment) {
        sentiment.value = response.sentiment
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch sentiment'
      console.error('Failed to fetch sentiment:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchDailySentiment(symbol?: string, days: number = 7) {
    try {
      const response = await api.getDailySentiment(symbol, days)
      dailySentiment.value = response.sentiment
    } catch (e) {
      console.error('Failed to fetch daily sentiment:', e)
    }
  }

  async function fetchPredictions(symbol?: string, predictionType?: string) {
    try {
      const response = await api.getPredictions(symbol)
      predictions.value = response
    } catch (e) {
      console.error(`Failed to fetch predictions:`, e)
    }
  }

  async function fetchAnomalies(symbol?: string) {
    try {
      const response = await api.getAnomalies(symbol)
      anomalies.value = Array.isArray(response) ? response : []
    } catch (e) {
      console.error('Failed to fetch anomalies:', e)
    }
  }

  async function fetchAnalyticsResults(symbol?: string, metricType?: string, hours: number = 24) {
    try {
      const response = await api.getAnalyticsResults(symbol, metricType, hours)
      analyticsResults.value = response.results
    } catch (e) {
      console.error('Failed to fetch analytics results:', e)
    }
  }

  function getPredictionsForSymbol(symbol: string) {
    return predictions.value[symbol] || []
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    sentiment,
    dailySentiment,
    predictions,
    anomalies,
    analyticsResults,
    loading,
    error,

    // Computed
    criticalAnomalies,
    highAnomalies,
    activeSentiment,
    overallSentiment,

    // Actions
    fetchSentiment,
    fetchDailySentiment,
    fetchPredictions,
    fetchAnomalies,
    fetchAnalyticsResults,
    getPredictionsForSymbol,
    clearError,
  }
})
