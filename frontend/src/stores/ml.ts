import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'

interface MLPrediction {
  id: string
  symbol: string
  prediction_type: string
  predicted_value: number
  confidence: number
  predicted_at: string
  valid_until: string
  model_name: string
  rmse: number | null
  r2_score: number | null
}

interface Anomaly {
  id: string
  symbol: string
  anomaly_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  anomaly_score: number
  description: string
  detected_at: string
}

interface ClusterAssignment {
  symbol: string
  cluster_id: number
  cluster_label: string
  distance_to_centroid: number | null
  silhouette_score: number | null
  feature_values: Record<string, number>
}

interface CorrelationMatrix {
  symbols: string[]
  matrix: Array<{
    symbol: string
    correlations: Record<string, number | null>
  }>
}

interface MomentumScore {
  symbol: string
  total_momentum_score: number
  momentum_label: string
  recommendation: string
  confidence: number
  rsi_score: number
  macd_score: number
  volume_score: number
  trend_score: number
}

export const useMLStore = defineStore('ml', () => {
  // State
  const predictions = ref<MLPrediction[]>([])
  const anomalies = ref<Anomaly[]>([])
  const clusters = ref<ClusterAssignment[]>([])
  const correlationMatrix = ref<CorrelationMatrix | null>(null)
  const momentumScores = ref<MomentumScore[]>([])
  const clusterStatistics = ref<any>(null)

  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const criticalAnomalies = computed(() =>
    anomalies.value.filter(a => a.severity === 'critical')
  )

  const highAnomalies = computed(() =>
    anomalies.value.filter(a => a.severity === 'high')
  )

  const bullishCoins = computed(() =>
    momentumScores.value.filter(m =>
      m.momentum_label === 'bullish' || m.momentum_label === 'very_bullish'
    )
  )

  const bearishCoins = computed(() =>
    momentumScores.value.filter(m =>
      m.momentum_label === 'bearish' || m.momentum_label === 'very_bearish'
    )
  )

  // Actions
  async function fetchPredictions(symbol?: string) {
    try {
      loading.value = true
      error.value = null

      const params = new URLSearchParams()
      if (symbol) params.append('symbol', symbol)

      const response = await api.get(`/analytics/ml/predictions?${params}`)
      predictions.value = response.data
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch predictions'
      console.error('Error fetching predictions:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchAnomalies(severity?: string, symbol?: string) {
    try {
      loading.value = true
      error.value = null

      const params = new URLSearchParams()
      if (severity) params.append('severity', severity)
      if (symbol) params.append('symbol', symbol)

      const response = await api.get(`/analytics/ml/anomalies?${params}`)
      anomalies.value = response.data
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch anomalies'
      console.error('Error fetching anomalies:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchClusters() {
    try {
      loading.value = true
      error.value = null

      const response = await api.get('/analytics/ml/clusters')
      clusters.value = response.data
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch clusters'
      console.error('Error fetching clusters:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchClusterStatistics() {
    try {
      loading.value = true
      error.value = null

      const response = await api.get('/analytics/ml/clusters/statistics')
      clusterStatistics.value = response.data
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch cluster statistics'
      console.error('Error fetching cluster statistics:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchCorrelationMatrix(symbols?: string[]) {
    try {
      loading.value = true
      error.value = null

      const params = new URLSearchParams()
      if (symbols && symbols.length > 0) {
        params.append('symbols', symbols.join(','))
      }

      const response = await api.get(`/analytics/ml/correlations/matrix?${params}`)
      correlationMatrix.value = response.data
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch correlation matrix'
      console.error('Error fetching correlation matrix:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchMomentumScores() {
    try {
      loading.value = true
      error.value = null

      // Using existing momentum endpoint from analytics
      const response = await api.get('/analytics/momentum')
      momentumScores.value = response.data
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch momentum scores'
      console.error('Error fetching momentum scores:', err)
    } finally {
      loading.value = false
    }
  }

  async function resolveAnomaly(anomalyId: string, notes?: string) {
    try {
      loading.value = true
      error.value = null

      await api.post(`/analytics/ml/anomalies/${anomalyId}/resolve`, {
        resolution_notes: notes
      })

      // Remove from local state
      anomalies.value = anomalies.value.filter(a => a.id !== anomalyId)
    } catch (err: any) {
      error.value = err.message || 'Failed to resolve anomaly'
      console.error('Error resolving anomaly:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    predictions,
    anomalies,
    clusters,
    correlationMatrix,
    momentumScores,
    clusterStatistics,
    loading,
    error,

    // Computed
    criticalAnomalies,
    highAnomalies,
    bullishCoins,
    bearishCoins,

    // Actions
    fetchPredictions,
    fetchAnomalies,
    fetchClusters,
    fetchClusterStatistics,
    fetchCorrelationMatrix,
    fetchMomentumScores,
    resolveAnomaly,
    clearError
  }
})
