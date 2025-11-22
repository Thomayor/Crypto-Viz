import type {
  CryptoPrice,
  News,
  SocialPost,
  AnalyticsResult,
  SentimentResult,
  MLPrediction,
  Anomaly,
  HealthStatus,
} from '@/types'

// Use relative URL by default to go through nginx proxy
// In production, nginx will proxy /api/ to backend:8000
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(error.detail || `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error)
      throw error
    }
  }

  // Health & Status
  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/health')
  }

  async getStats(): Promise<{ total_records: number }> {
    return this.request<{ total_records: number }>('/api/stats')
  }

  // Cryptocurrency Prices
  async getLatestPrices(limit: number = 10): Promise<CryptoPrice[]> {
    return this.request<CryptoPrice[]>(`/api/crypto/latest?limit=${limit}`)
  }

  async getPriceHistory(
    symbol: string,
    hours: number = 24
  ): Promise<{ symbol: string; hours: number; prices: CryptoPrice[] }> {
    return this.request<{ symbol: string; hours: number; prices: CryptoPrice[] }>(
      `/api/crypto/${symbol}/history?hours=${hours}`
    )
  }

  // News
  async getLatestNews(
    limit: number = 20,
    hours: number = 24
  ): Promise<{ count: number; hours: number; news: News[] }> {
    return this.request<{ count: number; hours: number; news: News[] }>(
      `/api/news/latest?limit=${limit}&hours=${hours}`
    )
  }

  // Social Media
  async getLatestSocial(
    platform: 'reddit' | 'twitter' | 'all' = 'all',
    limit: number = 20,
    hours: number = 24
  ): Promise<{ count: number; platform: string; hours: number; posts: SocialPost[] }> {
    return this.request<{ count: number; platform: string; hours: number; posts: SocialPost[] }>(
      `/api/social/latest?platform=${platform}&limit=${limit}&hours=${hours}`
    )
  }

  // Analytics
  async getAnalyticsResults(
    symbol?: string,
    metricType?: string,
    hours: number = 24
  ): Promise<{ count: number; hours: number; results: AnalyticsResult[] }> {
    const params = new URLSearchParams({ hours: hours.toString() })
    if (symbol) params.append('symbol', symbol)
    if (metricType) params.append('metric_type', metricType)

    return this.request<{ count: number; hours: number; results: AnalyticsResult[] }>(
      `/api/analytics/results?${params}`
    )
  }

  async getSentiment(
    symbol?: string,
    timeWindow: '24h' | '7d' | '30d' = '24h'
  ): Promise<any> {
    // Always use /api/analytics/all/sentiment, with optional symbol filter
    const params = new URLSearchParams()

    // Convert timeWindow to hours
    const hoursMap = { '24h': 24, '7d': 168, '30d': 720 }
    params.append('hours', hoursMap[timeWindow].toString())

    if (symbol) {
      params.append('symbol', symbol)
    }

    return this.request<any>(`/api/analytics/all/sentiment?${params}`)
  }

  async getDailySentiment(
    symbol?: string,
    days: number = 7
  ): Promise<{ count: number; days: number; sentiment: SentimentResult[] }> {
    const params = new URLSearchParams({ days: days.toString() })
    if (symbol) params.append('symbol', symbol)

    return this.request<{ count: number; days: number; sentiment: SentimentResult[] }>(
      `/api/analytics/sentiment/daily?${params}`
    )
  }

  async getAnomalies(symbol?: string): Promise<Anomaly[]> {
    if (!symbol) {
      // Get anomalies for all coins
      return this.request<Anomaly[]>(`/api/analytics/all/anomalies`)
    }
    return this.request<Anomaly[]>(`/api/analytics/${symbol}/anomalies`)
  }

  // ML Predictions
  async getPredictions(symbol?: string): Promise<Record<string, MLPrediction[]>> {
    // Always fetch all predictions since per-symbol endpoint doesn't exist
    return this.request<Record<string, MLPrediction[]>>(`/api/analytics/all/predictions`)
  }

  // Generic GET method for flexibility
  async get<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint)
  }

  // Generic POST method for flexibility
  async post<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }
}

export const api = new ApiService()
