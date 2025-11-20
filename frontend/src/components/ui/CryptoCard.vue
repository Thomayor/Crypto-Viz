<template>
  <div
    @click="handleClick"
    class="crypto-card group"
  >
    <!-- Header -->
    <div class="flex items-center gap-3 mb-3">
      <!-- Rank Badge -->
      <div class="rank-badge">
        #{{ crypto.rank || crypto.market_cap_rank || '?' }}
      </div>

      <!-- Logo -->
      <img
        v-if="crypto.image"
        :src="crypto.image"
        :alt="crypto.name"
        class="w-10 h-10 rounded-full flex-shrink-0 bg-white/5 p-1"
        @error="handleImageError"
      />
      <div v-else class="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center flex-shrink-0">
        <span class="text-sm font-bold text-white">{{ crypto.symbol.substring(0, 2).toUpperCase() }}</span>
      </div>

      <!-- Name and Symbol -->
      <div class="min-w-0 flex-1">
        <div class="text-white font-bold truncate">{{ crypto.name }}</div>
        <div class="text-gray-400 text-xs uppercase">{{ crypto.symbol }}</div>
      </div>
    </div>

    <!-- Price and Change -->
    <div class="mb-3">
      <div class="text-2xl font-black text-white mb-1">
        {{ formatPrice(crypto.current_price) }}
      </div>
      <div
        :class="[
          'text-sm font-semibold flex items-center gap-1',
          priceChange >= 0 ? 'text-green-400' : 'text-red-400'
        ]"
      >
        <component
          :is="priceChange >= 0 ? ArrowTrendingUpIcon : ArrowTrendingDownIcon"
          class="h-4 w-4"
        />
        {{ formatPercentage(crypto.price_change_percentage_24h) }}
      </div>
    </div>

    <!-- Mini Sparkline Chart -->
    <div class="h-16 relative">
      <svg
        :viewBox="`0 0 ${sparklineData.length * 4} 100`"
        class="w-full h-full"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient :id="`gradient-${crypto.id}`" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" :style="`stop-color: ${sparklineColor}; stop-opacity: 0.3`" />
            <stop offset="100%" :style="`stop-color: ${sparklineColor}; stop-opacity: 0`" />
          </linearGradient>
        </defs>

        <!-- Area -->
        <path
          :d="sparklineAreaPath"
          :fill="`url(#gradient-${crypto.id})`"
        />

        <!-- Line -->
        <path
          :d="sparklinePath"
          :stroke="sparklineColor"
          stroke-width="1.5"
          fill="none"
          class="transition-all duration-300"
        />
      </svg>
    </div>

    <!-- Footer Stats -->
    <div class="mt-3 pt-3 border-t border-gray-700/50 grid grid-cols-2 gap-2 text-xs">
      <div>
        <div class="text-gray-500">Market Cap</div>
        <div class="text-white font-semibold truncate">{{ formatMarketCap(crypto.market_cap) }}</div>
      </div>
      <div>
        <div class="text-gray-500">Volume 24h</div>
        <div class="text-white font-semibold truncate">{{ formatMarketCap(crypto.total_volume) }}</div>
      </div>
    </div>

    <!-- Hover Overlay -->
    <div class="absolute inset-0 border-2 border-transparent group-hover:border-cyan-500/50 rounded-xl transition-all pointer-events-none"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useFormatting } from '@/composables/useFormatting'
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/vue/24/outline'

interface Props {
  crypto: any
}

const props = defineProps<Props>()
const router = useRouter()
const { formatPrice, formatPercentage, formatMarketCap } = useFormatting()

const priceChange = computed(() => props.crypto.price_change_percentage_24h || 0)

const sparklineColor = computed(() => priceChange.value >= 0 ? '#10b981' : '#ef4444')

// Generate mock sparkline data based on 24h change
const sparklineData = computed(() => {
  const points = 20
  const data: number[] = []
  const price = props.crypto.current_price || 0
  const change = priceChange.value / 100

  for (let i = 0; i < points; i++) {
    const progress = i / (points - 1)
    const trend = price * (1 + change * progress)
    const noise = (Math.random() - 0.5) * price * 0.01
    data.push(Math.max(0, trend + noise))
  }

  return data
})

const sparklinePath = computed(() => {
  if (sparklineData.value.length === 0) return ''

  const min = Math.min(...sparklineData.value)
  const max = Math.max(...sparklineData.value)
  const range = max - min || 1

  const points = sparklineData.value.map((value, index) => {
    const x = index * 4
    const y = 100 - ((value - min) / range) * 100
    return `${x},${y}`
  })

  return `M ${points.join(' L ')}`
})

const sparklineAreaPath = computed(() => {
  if (sparklineData.value.length === 0) return ''

  const min = Math.min(...sparklineData.value)
  const max = Math.max(...sparklineData.value)
  const range = max - min || 1

  const points = sparklineData.value.map((value, index) => {
    const x = index * 4
    const y = 100 - ((value - min) / range) * 100
    return `${x},${y}`
  })

  const width = (sparklineData.value.length - 1) * 4

  return `M 0,100 L ${points.join(' L ')} L ${width},100 Z`
})

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.style.display = 'none'
}

const handleClick = () => {
  router.push(`/crypto/${props.crypto.symbol.toLowerCase()}`)
}
</script>

<style scoped>
.crypto-card {
  @apply relative bg-gradient-to-br from-gray-800/60 to-gray-900/60 backdrop-blur-sm
         rounded-xl p-5 border border-gray-700/50
         hover:border-cyan-500/30 hover:shadow-xl hover:shadow-cyan-500/10
         cursor-pointer transition-all duration-300
         hover:scale-[1.02] hover:-translate-y-1;
}

.rank-badge {
  @apply flex-shrink-0 w-8 h-8 rounded-full
         bg-gradient-to-br from-cyan-500/20 to-blue-500/20
         border border-cyan-500/30
         flex items-center justify-center
         text-xs font-bold text-cyan-400;
}
</style>
