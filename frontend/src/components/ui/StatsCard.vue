<template>
  <div class="stats-card group">
    <div class="flex items-center justify-between">
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-1">
          <component
            v-if="icon"
            :is="icon"
            :class="['icon', iconColorClass]"
          />
          <span class="text-sm font-medium text-gray-400">{{ label }}</span>
        </div>

        <div class="flex items-baseline gap-2">
          <h3 class="text-2xl font-bold text-white">{{ formattedValue }}</h3>
          <div v-if="change !== undefined" :class="changeClass">
            <component :is="changeIcon" class="h-4 w-4" />
            <span class="text-sm font-semibold">{{ Math.abs(change).toFixed(2) }}%</span>
          </div>
        </div>

        <p v-if="subtitle" class="text-xs text-gray-500 mt-1">{{ subtitle }}</p>
      </div>

      <div v-if="trend" class="trend-sparkline ml-4">
        <svg :width="sparklineWidth" :height="sparklineHeight" class="text-current">
          <path
            :d="sparklinePath"
            fill="none"
            :stroke="trendColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </div>
    </div>

    <div v-if="$slots.footer" class="mt-4 pt-4 border-t border-gray-700/50">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/vue/24/outline'

interface Props {
  label: string
  value: number | string
  change?: number
  subtitle?: string
  icon?: Component
  iconColor?: 'cyan' | 'green' | 'red' | 'yellow' | 'purple' | 'pink'
  trend?: number[]
  variant?: 'default' | 'gradient'
}

const props = withDefaults(defineProps<Props>(), {
  iconColor: 'cyan',
  variant: 'default'
})

const formattedValue = computed(() => {
  // Handle undefined, null, or NaN values
  if (props.value === undefined || props.value === null) return 'N/A'
  if (typeof props.value === 'number' && isNaN(props.value)) return 'N/A'
  if (typeof props.value === 'string') return props.value

  if (props.value >= 1000000000000) {
    return '$' + (props.value / 1000000000000).toFixed(2) + 'T'
  } else if (props.value >= 1000000000) {
    return '$' + (props.value / 1000000000).toFixed(2) + 'B'
  } else if (props.value >= 1000000) {
    return '$' + (props.value / 1000000).toFixed(2) + 'M'
  } else if (props.value >= 1000) {
    return '$' + (props.value / 1000).toFixed(2) + 'K'
  }
  return '$' + props.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
})

const iconColorClass = computed(() => {
  const colors = {
    cyan: 'text-cyan-400',
    green: 'text-green-400',
    red: 'text-red-400',
    yellow: 'text-yellow-400',
    purple: 'text-purple-400',
    pink: 'text-pink-400'
  }
  return colors[props.iconColor]
})

const changeIcon = computed(() => {
  return (props.change ?? 0) >= 0 ? ArrowTrendingUpIcon : ArrowTrendingDownIcon
})

const changeClass = computed(() => {
  const isPositive = (props.change ?? 0) >= 0
  return [
    'flex items-center gap-1',
    isPositive ? 'text-green-400' : 'text-red-400'
  ]
})

const trendColor = computed(() => {
  if (!props.trend || props.trend.length === 0) return '#06B6D4'
  const firstValue = props.trend[0]
  const lastValue = props.trend[props.trend.length - 1]
  return lastValue >= firstValue ? '#10B981' : '#EF4444'
})

// Sparkline SVG path generation
const sparklineWidth = 80
const sparklineHeight = 40

const sparklinePath = computed(() => {
  if (!props.trend || props.trend.length < 2) return ''

  const data = props.trend
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1

  const xStep = sparklineWidth / (data.length - 1)
  const yScale = sparklineHeight / range

  const points = data.map((value, index) => {
    const x = index * xStep
    const y = sparklineHeight - ((value - min) * yScale)
    return `${x},${y}`
  })

  return `M ${points.join(' L ')}`
})
</script>

<style scoped>
.stats-card {
  @apply bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50
         transition-all duration-300 hover:border-cyan-500/50 hover:shadow-xl
         hover:shadow-cyan-500/10;
}

.icon {
  @apply h-5 w-5 transition-transform duration-300 group-hover:scale-110;
}

.trend-sparkline {
  @apply opacity-70 group-hover:opacity-100 transition-opacity duration-300;
}
</style>
