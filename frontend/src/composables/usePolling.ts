import { ref, onMounted, onUnmounted } from 'vue'

export function usePolling(callback: () => void | Promise<void>, interval: number = 30000) {
  const isPolling = ref(false)
  const intervalId = ref<number | null>(null)

  const start = () => {
    if (isPolling.value) return

    isPolling.value = true
    callback() // Execute immediately

    intervalId.value = window.setInterval(() => {
      if (isPolling.value) {
        callback()
      }
    }, interval)
  }

  const stop = () => {
    if (intervalId.value !== null) {
      clearInterval(intervalId.value)
      intervalId.value = null
    }
    isPolling.value = false
  }

  const restart = () => {
    stop()
    start()
  }

  onMounted(() => {
    start()
  })

  onUnmounted(() => {
    stop()
  })

  return {
    isPolling,
    start,
    stop,
    restart,
  }
}
