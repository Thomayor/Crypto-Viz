<template>
  <div class="connection-status">
    <div
      :class="[
        'flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all duration-300',
        statusClass
      ]"
    >
      <!-- Status Indicator -->
      <div class="relative flex h-3 w-3">
        <span
          v-if="isConnected"
          class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
          :class="pulseClass"
        ></span>
        <span
          class="relative inline-flex rounded-full h-3 w-3"
          :class="dotClass"
        ></span>
      </div>

      <!-- Status Text -->
      <span class="text-xs font-medium whitespace-nowrap" :class="textClass">
        {{ statusText }}
      </span>

      <!-- Reconnect Attempts -->
      <span
        v-if="reconnectAttempts > 0 && !isConnected"
        class="text-xs text-gray-400"
      >
        ({{ reconnectAttempts }}/5)
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  isConnected: boolean
  isConnecting: boolean
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error'
  reconnectAttempts?: number
}

const props = withDefaults(defineProps<Props>(), {
  reconnectAttempts: 0
})

const statusText = computed(() => {
  switch (props.connectionStatus) {
    case 'connected':
      return 'Live'
    case 'connecting':
      return 'Connecting...'
    case 'disconnected':
      return 'Offline'
    case 'error':
      return 'Error'
    default:
      return 'Unknown'
  }
})

const statusClass = computed(() => {
  switch (props.connectionStatus) {
    case 'connected':
      return 'bg-green-500/10 border border-green-500/30'
    case 'connecting':
      return 'bg-yellow-500/10 border border-yellow-500/30'
    case 'disconnected':
      return 'bg-gray-500/10 border border-gray-500/30'
    case 'error':
      return 'bg-red-500/10 border border-red-500/30'
    default:
      return 'bg-gray-500/10 border border-gray-500/30'
  }
})

const dotClass = computed(() => {
  switch (props.connectionStatus) {
    case 'connected':
      return 'bg-green-500'
    case 'connecting':
      return 'bg-yellow-500'
    case 'disconnected':
      return 'bg-gray-500'
    case 'error':
      return 'bg-red-500'
    default:
      return 'bg-gray-500'
  }
})

const pulseClass = computed(() => {
  switch (props.connectionStatus) {
    case 'connected':
      return 'bg-green-400'
    case 'connecting':
      return 'bg-yellow-400'
    default:
      return ''
  }
})

const textClass = computed(() => {
  switch (props.connectionStatus) {
    case 'connected':
      return 'text-green-400'
    case 'connecting':
      return 'text-yellow-400'
    case 'disconnected':
      return 'text-gray-400'
    case 'error':
      return 'text-red-400'
    default:
      return 'text-gray-400'
  }
})
</script>

<style scoped>
.connection-status {
  @apply flex items-center;
}
</style>
