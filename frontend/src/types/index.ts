export interface CryptoPrice {
  id: string  // UUID from PostgreSQL
  symbol: string
  name: string
  price: number
  market_cap: number
  volume_24h: number
  percent_change_1h: number
  percent_change_24h: number
  percent_change_7d: number
  rank: number
  timestamp: string
  // Aliases for backward compatibility with CoinGecko format
  current_price?: number  // Alias for price
  total_volume?: number   // Alias for volume_24h
  price_change_percentage_24h?: number  // Alias for percent_change_24h
  image?: string  // Optional image URL
}

export interface News {
  id: string  // UUID from PostgreSQL
  source: string
  author: string | null
  title: string
  description: string | null
  url: string
  url_to_image?: string | null
  sentiment_score: number
  sentiment_label: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL' | 'positive' | 'negative' | 'neutral'
  analysis_method?: 'ollama' | 'lexicon' | 'fallback'  // Sentiment analysis method
  confidence_score?: number  // Sentiment confidence (0-1)
  keywords: string[]
  mentioned_coins: string[]
  published_at: string
}

export interface SocialPost {
  id: number
  platform: 'reddit' | 'twitter'
  post_id: string
  author: string
  content: string
  sentiment_score: number
  sentiment_label: 'positive' | 'negative' | 'neutral'
  score: number
  num_comments: number
  mentioned_coins: string[]
  created_at: string
  timestamp: string
}

export interface AnalyticsResult {
  id: number
  symbol: string
  metric_type: string
  value: number
  confidence: number
  timestamp: string
}

export interface SentimentResult {
  symbol: string
  time_window: '24h' | '7d' | '30d'
  positive_count: number
  negative_count: number
  neutral_count: number
  average_sentiment: number
  dominant_sentiment: 'positive' | 'negative' | 'neutral'
  timestamp: string
  total_count?: number
  ollama_analyzed?: number
  avg_confidence?: number
}

export interface MLPrediction {
  id: number
  symbol: string
  prediction_type: string
  model_type: 'LinearRegression' | 'KMeans' | 'IsolationForest'
  predicted_value: string
  confidence: number
  lower_bound: string | null
  upper_bound: string | null
  features: Record<string, any>
  created_at: string
  valid_until: string
}

export interface Anomaly {
  id: number
  symbol: string
  anomaly_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  detected_value: number
  expected_range: string
  confidence: number
  timestamp: string
  resolved: boolean
}

export interface HealthStatus {
  status: string
  timestamp: string
  database: {
    connected: boolean
    total_records: number
  }
}

export interface ApiResponse<T> {
  data?: T
  error?: string
}
