<template>
  <div class="doughnut-container">
    <div v-if="chartData" class="flex flex-col lg:flex-row items-center justify-between gap-6">
      <!-- Chart Section -->
      <div class="chart-wrapper">
        <div class="chart-inner">
          <Doughnut :data="chartData" :options="chartOptions" />
        </div>
        <!-- Center Label -->
        <div class="center-label">
          <div class="market-value">{{ formatMarketShare(totalValue) }}</div>
          <div class="market-label">Total Market</div>
        </div>
      </div>

      <!-- Legend Section -->
      <div class="legend-wrapper">
        <div
          v-for="(item, index) in props.data"
          :key="index"
          class="legend-item"
        >
          <div class="legend-left">
            <div
              class="color-dot"
              :style="{ backgroundColor: item.color }"
            ></div>
            <div class="crypto-info">
              <div class="crypto-name">{{ item.label }}</div>
              <div class="crypto-value">{{ formatValue(item.value) }}</div>
            </div>
          </div>
          <div
            class="percentage-badge"
            :style="{
              backgroundColor: `${item.color}20`,
              color: item.color,
              borderColor: `${item.color}40`
            }"
          >
            {{ calculatePercentage(item.value) }}%
          </div>
        </div>
      </div>
    </div>

    <div v-else class="flex items-center justify-center h-64">
      <LoadingSpinner message="Loading data..." />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, type ChartOptions } from 'chart.js'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

ChartJS.register(ArcElement, Tooltip, Legend)

interface Props {
  data: { label: string; value: number; color: string }[]
  title?: string
}

const props = defineProps<Props>()

const totalValue = computed(() => {
  return props.data.reduce((sum, item) => sum + item.value, 0)
})

const calculatePercentage = (value: number) => {
  if (totalValue.value === 0) return '0.0'
  return ((value / totalValue.value) * 100).toFixed(1)
}

const formatValue = (value: number) => {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`
  if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`
  return `$${value.toFixed(2)}`
}

const formatMarketShare = (value: number) => {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`
  return `$${value.toFixed(0)}`
}

const chartData = computed(() => {
  if (!props.data || props.data.length === 0) return null

  return {
    labels: props.data.map((d) => d.label),
    datasets: [
      {
        data: props.data.map((d) => d.value),
        backgroundColor: props.data.map((d) => d.color),
        borderWidth: 2,
        borderColor: '#1e293b',
        hoverBorderWidth: 3,
        hoverBorderColor: '#fff',
        hoverOffset: 8,
      },
    ],
  }
})

const chartOptions: ChartOptions<'doughnut'> = {
  responsive: true,
  maintainAspectRatio: true,
  cutout: '70%',
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      enabled: true,
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      titleColor: '#fff',
      bodyColor: '#cbd5e1',
      borderColor: 'rgba(6, 182, 212, 0.3)',
      borderWidth: 1,
      padding: 10,
      cornerRadius: 6,
      displayColors: true,
      callbacks: {
        label: (context) => {
          const label = context.label || ''
          const value = context.parsed || 0
          const percentage = calculatePercentage(value)
          return ` ${label}: ${formatValue(value)} (${percentage}%)`
        },
      },
    },
  },
  animation: {
    animateRotate: true,
    animateScale: false,
  },
}
</script>

<style scoped>
.doughnut-container {
  @apply w-full;
}

.chart-wrapper {
  @apply relative w-full lg:w-[45%] flex items-center justify-center;
  height: 320px;
}

.chart-inner {
  @apply relative w-full h-full max-w-[320px];
}

.center-label {
  @apply absolute inset-0 flex flex-col items-center justify-center pointer-events-none;
}

.market-value {
  @apply text-2xl font-bold text-white;
}

.market-label {
  @apply text-xs text-gray-400 mt-1 uppercase;
}

.legend-wrapper {
  @apply w-full lg:w-[55%] space-y-2;
}

.legend-item {
  @apply flex items-center justify-between p-3 rounded-lg
         bg-gray-800/40 hover:bg-gray-700/50
         border border-gray-700/50 hover:border-cyan-500/30
         transition-all duration-200 cursor-pointer;
}

.legend-left {
  @apply flex items-center gap-3 flex-1 min-w-0;
}

.color-dot {
  @apply w-3 h-3 rounded-full flex-shrink-0;
}

.crypto-info {
  @apply flex-1 min-w-0;
}

.crypto-name {
  @apply text-sm font-semibold text-white truncate;
}

.crypto-value {
  @apply text-xs text-gray-400;
}

.percentage-badge {
  @apply px-3 py-1 rounded-md font-bold text-sm border;
}
</style>
