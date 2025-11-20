import { onMounted, onUnmounted } from 'vue'
import { useWebSocket } from './useWebSocket'
import { useCryptoStore } from '@/stores/crypto'
import { useAnalyticsStore } from '@/stores/analytics'
import { useNewsStore } from '@/stores/news'
import { useRealtimeStore } from '@/stores/realtime'

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

// Throttle function to limit update frequency
function throttle<T extends (...args: any[]) => void>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let lastCall = 0
  let timeout: number | null = null

  return (...args: Parameters<T>) => {
    const now = Date.now()

    if (now - lastCall >= delay) {
      lastCall = now
      func(...args)
    } else {
      if (timeout) clearTimeout(timeout)
      timeout = window.setTimeout(() => {
        lastCall = Date.now()
        func(...args)
      }, delay - (now - lastCall))
    }
  }
}

export function useRealTimeData() {
  const cryptoStore = useCryptoStore()
  const analyticsStore = useAnalyticsStore()
  const newsStore = useNewsStore()
  const realtimeStore = useRealtimeStore()

  const ws = useWebSocket()

  // Throttled update handlers to prevent UI overload
  const handlePriceUpdate = throttle((data: PriceUpdate | PriceUpdate[]) => {
    const updates = Array.isArray(data) ? data : [data]

    updates.forEach(update => {
      realtimeStore.updatePrice(update)

      // Update crypto store
      const index = cryptoStore.prices.findIndex(p => p.id === update.coin_id)
      if (index !== -1) {
        cryptoStore.prices[index] = {
          ...cryptoStore.prices[index],
          current_price: update.current_price,
          price_change_percentage_24h: update.price_change_percentage_24h,
          market_cap: update.market_cap,
          total_volume: update.total_volume
        }
      }
    })

    console.log(`Price updates applied: ${updates.length} coins`)
  }, 500) // Update at most every 500ms

  const handleSentimentUpdate = throttle((data: SentimentUpdate | SentimentUpdate[]) => {
    const updates = Array.isArray(data) ? data : [data]

    updates.forEach(update => {
      realtimeStore.updateSentiment(update)
    })

    console.log(`Sentiment updates applied: ${updates.length} items`)
  }, 1000) // Update at most every second

  const handleNewsUpdate = throttle((data: NewsUpdate | NewsUpdate[]) => {
    const updates = Array.isArray(data) ? data : [data]

    updates.forEach(update => {
      realtimeStore.addNews(update)

      // Add to news store if not already present
      if (!newsStore.news.find(n => n.id === update.id)) {
        newsStore.news.unshift(update as any)
      }
    })

    console.log(`News updates applied: ${updates.length} articles`)
  }, 2000) // Update at most every 2 seconds

  const handleAnomalyUpdate = throttle((data: AnomalyUpdate | AnomalyUpdate[]) => {
    const updates = Array.isArray(data) ? data : [data]

    updates.forEach(update => {
      realtimeStore.addAnomaly(update)

      // Add to analytics store
      if (!analyticsStore.anomalies.find(a => a.id === update.id)) {
        analyticsStore.anomalies.unshift(update as any)
      }
    })

    console.log(`Anomaly updates applied: ${updates.length} anomalies`)
  }, 1000) // Update at most every second

  const handleConnectionStatus = (data: { status: string; message?: string }) => {
    console.log('WebSocket status:', data)
    realtimeStore.setConnectionMessage(data.message || '')
  }

  // Subscribe to WebSocket events
  const setupSubscriptions = () => {
    const unsubscribers = [
      ws.subscribe('price_update', handlePriceUpdate),
      ws.subscribe('prices_batch', handlePriceUpdate),
      ws.subscribe('sentiment_update', handleSentimentUpdate),
      ws.subscribe('news_update', handleNewsUpdate),
      ws.subscribe('news_batch', handleNewsUpdate),
      ws.subscribe('anomaly_update', handleAnomalyUpdate),
      ws.subscribe('connection_status', handleConnectionStatus)
    ]

    return () => {
      unsubscribers.forEach(unsub => unsub())
    }
  }

  // Setup and cleanup
  let cleanup: (() => void) | null = null

  onMounted(() => {
    cleanup = setupSubscriptions()
    console.log('Real-time data subscriptions active')
  })

  onUnmounted(() => {
    if (cleanup) {
      cleanup()
    }
    console.log('Real-time data subscriptions cleaned up')
  })

  return {
    isConnected: ws.isConnected,
    isConnecting: ws.isConnecting,
    connectionStatus: ws.connectionStatus,
    reconnectAttempts: ws.reconnectAttempts,
    sendMessage: ws.sendMessage
  }
}
