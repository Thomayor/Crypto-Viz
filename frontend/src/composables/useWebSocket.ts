import { ref, onUnmounted, computed } from 'vue'

type MessageHandler = (data: any) => void
type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface WebSocketMessage {
  type: string
  data: any
  timestamp?: string
}

export function useWebSocket(url?: string) {
  // Default URL: use same host as frontend with WebSocket protocol
  const defaultUrl = (() => {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${protocol}//${window.location.host}/ws`
    }
    return 'ws://localhost:3000/ws'
  })()

  const wsUrl = url || defaultUrl
  const ws = ref<WebSocket | null>(null)
  const connectionStatus = ref<ConnectionStatus>('disconnected')
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = ref(1000) // Start with 1 second
  const subscribers = new Map<string, Set<MessageHandler>>()
  const reconnectTimeout = ref<number | null>(null)

  const isConnected = computed(() => connectionStatus.value === 'connected')
  const isConnecting = computed(() => connectionStatus.value === 'connecting')

  // Connect to WebSocket
  const connect = () => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return
    }

    connectionStatus.value = 'connecting'
    console.log(`Connecting to WebSocket: ${wsUrl}`)

    try {
      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        console.log('WebSocket connected')
        connectionStatus.value = 'connected'
        reconnectAttempts.value = 0
        reconnectDelay.value = 1000
      }

      ws.value.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          console.log('WebSocket message received:', message.type)

          // Notify all subscribers for this message type
          const handlers = subscribers.get(message.type)
          if (handlers) {
            handlers.forEach(handler => {
              try {
                handler(message.data)
              } catch (error) {
                console.error(`Error in WebSocket handler for ${message.type}:`, error)
              }
            })
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.value.onerror = (error) => {
        console.error('WebSocket error:', error)
        connectionStatus.value = 'error'
      }

      ws.value.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        connectionStatus.value = 'disconnected'

        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts.value < maxReconnectAttempts) {
          reconnectAttempts.value++
          const delay = Math.min(reconnectDelay.value * 2, 30000) // Max 30 seconds
          reconnectDelay.value = delay

          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.value}/${maxReconnectAttempts})`)

          reconnectTimeout.value = window.setTimeout(() => {
            connect()
          }, delay)
        } else {
          console.error('Max reconnection attempts reached')
        }
      }
    } catch (error) {
      console.error('Error creating WebSocket:', error)
      connectionStatus.value = 'error'
    }
  }

  // Disconnect from WebSocket
  const disconnect = () => {
    if (reconnectTimeout.value) {
      clearTimeout(reconnectTimeout.value)
      reconnectTimeout.value = null
    }

    if (ws.value) {
      ws.value.close()
      ws.value = null
    }

    connectionStatus.value = 'disconnected'
    reconnectAttempts.value = 0
  }

  // Subscribe to a message type
  const subscribe = (messageType: string, handler: MessageHandler) => {
    if (!subscribers.has(messageType)) {
      subscribers.set(messageType, new Set())
    }

    subscribers.get(messageType)!.add(handler)

    // Return unsubscribe function
    return () => unsubscribe(messageType, handler)
  }

  // Unsubscribe from a message type
  const unsubscribe = (messageType: string, handler: MessageHandler) => {
    const handlers = subscribers.get(messageType)
    if (handlers) {
      handlers.delete(handler)
      if (handlers.size === 0) {
        subscribers.delete(messageType)
      }
    }
  }

  // Send a message to the WebSocket
  const sendMessage = (type: string, data: any) => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type,
        data,
        timestamp: new Date().toISOString()
      }
      ws.value.send(JSON.stringify(message))
      return true
    } else {
      console.warn('WebSocket is not connected. Message not sent:', type)
      return false
    }
  }

  // Clean up on component unmount
  onUnmounted(() => {
    disconnect()
    subscribers.clear()
  })

  // Auto-connect on creation
  connect()

  return {
    isConnected,
    isConnecting,
    connectionStatus,
    reconnectAttempts,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    sendMessage
  }
}
