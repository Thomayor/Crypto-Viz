<template>
  <div class="relative">
    <Bar v-if="chartData" :data="chartData" :options="chartOptions" />
    <div v-else class="flex items-center justify-center h-64">
      <LoadingSpinner message="Loading volume data..." />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  type ChartOptions,
} from 'chart.js'
import type { CryptoPrice } from '@/types'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import { useFormatting } from '@/composables/useFormatting'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

interface Props {
  prices: CryptoPrice[]
}

const props = defineProps<Props>()
const { formatVolume } = useFormatting()

const chartData = computed(() => {
  if (!props.prices || props.prices.length === 0) return null

  const topPrices = [...props.prices]
    .sort((a, b) => parseFloat(b.volume_24h) - parseFloat(a.volume_24h))
    .slice(0, 10)

  return {
    labels: topPrices.map((p) => p.symbol),
    datasets: [
      {
        label: '24h Volume',
        data: topPrices.map((p) => parseFloat(p.volume_24h)),
        backgroundColor: topPrices.map((p) =>
          p.percent_change_24h >= 0 ? 'rgba(16, 185, 129, 0.8)' : 'rgba(239, 68, 68, 0.8)'
        ),
      },
    ],
  }
})

const chartOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          return `Volume: ${formatVolume(context.parsed.y)}`
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
      beginAtZero: true,
      ticks: {
        callback: (value) => formatVolume(value as number),
      },
    },
  },
}
</script>
