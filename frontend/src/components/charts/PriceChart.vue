<template>
  <div class="relative">
    <Line v-if="chartData" :data="chartData" :options="chartOptions" />
    <div v-else class="flex items-center justify-center h-64">
      <LoadingSpinner message="Loading chart data..." />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ChartOptions,
} from 'chart.js'
import type { CryptoPrice } from '@/types'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import { useFormatting } from '@/composables/useFormatting'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

interface Props {
  prices: CryptoPrice[]
  symbol: string
}

const props = defineProps<Props>()
const { formatPrice, formatDate } = useFormatting()

const chartData = computed(() => {
  if (!props.prices || props.prices.length === 0) return null

  const sortedPrices = [...props.prices].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )

  return {
    labels: sortedPrices.map((p) => formatDate(p.timestamp, 'MMM dd HH:mm')),
    datasets: [
      {
        label: props.symbol,
        data: sortedPrices.map((p) => parseFloat(p.price)),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 2,
        pointHoverRadius: 6,
      },
    ],
  }
})

const chartOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index',
  },
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          return `Price: ${formatPrice(context.parsed.y)}`
        },
      },
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
    },
    y: {
      ticks: {
        callback: (value) => formatPrice(value as number),
      },
    },
  },
}
</script>
