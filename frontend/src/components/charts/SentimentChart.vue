<template>
  <div class="relative">
    <Bar v-if="chartData" :data="chartData" :options="chartOptions" />
    <div v-else class="flex items-center justify-center h-64">
      <LoadingSpinner message="Loading sentiment data..." />
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
import type { SentimentResult } from '@/types'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import { useFormatting } from '@/composables/useFormatting'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

interface Props {
  sentiment: SentimentResult[]
}

const props = defineProps<Props>()
const { formatDate } = useFormatting()

const chartData = computed(() => {
  if (!props.sentiment || props.sentiment.length === 0) return null

  const sortedSentiment = [...props.sentiment].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )

  return {
    labels: sortedSentiment.map((s) => s.symbol || formatDate(s.timestamp, 'MMM dd')),
    datasets: [
      {
        label: 'Positive',
        data: sortedSentiment.map((s) => s.positive_count),
        backgroundColor: 'rgba(16, 185, 129, 0.8)',
      },
      {
        label: 'Neutral',
        data: sortedSentiment.map((s) => s.neutral_count),
        backgroundColor: 'rgba(107, 114, 128, 0.8)',
      },
      {
        label: 'Negative',
        data: sortedSentiment.map((s) => s.negative_count),
        backgroundColor: 'rgba(239, 68, 68, 0.8)',
      },
    ],
  }
})

const chartOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
    },
    tooltip: {
      mode: 'index',
      intersect: false,
    },
  },
  scales: {
    x: {
      stacked: true,
      grid: {
        display: false,
      },
    },
    y: {
      stacked: true,
      beginAtZero: true,
    },
  },
}
</script>
