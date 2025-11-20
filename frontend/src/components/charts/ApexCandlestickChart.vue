<template>
  <div class="apex-chart-wrapper">
    <apexchart
      v-if="series.length > 0"
      :options="chartOptions"
      :series="series"
      type="candlestick"
      :height="height"
    />
    <div v-else class="flex items-center justify-center h-full text-gray-400">
      No data available
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts

interface CandlestickData {
  timestamp: Date | string
  open: number
  high: number
  low: number
  close: number
}

interface Props {
  data: CandlestickData[]
  title?: string
  height?: number | string
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Price Chart',
  height: 400
})

const series = computed(() => {
  if (!props.data || props.data.length === 0) return []

  return [{
    name: 'Price',
    data: props.data.map(item => ({
      x: new Date(item.timestamp).getTime(),
      y: [item.open, item.high, item.low, item.close]
    }))
  }]
})

const chartOptions = computed(() => ({
  chart: {
    type: 'candlestick',
    fontFamily: 'Inter, sans-serif',
    zoom: {
      enabled: true,
      type: 'x',
      autoScaleYaxis: true
    },
    toolbar: {
      show: true,
      autoSelected: 'zoom'
    },
    background: 'transparent'
  },
  plotOptions: {
    candlestick: {
      colors: {
        upward: '#10B981',
        downward: '#EF4444'
      },
      wick: {
        useFillColor: true
      }
    }
  },
  grid: {
    borderColor: '#374151',
    strokeDashArray: 4
  },
  xaxis: {
    type: 'datetime',
    labels: {
      style: {
        colors: '#9CA3AF',
        fontSize: '12px'
      }
    },
    axisBorder: {
      show: false
    },
    axisTicks: {
      show: false
    }
  },
  yaxis: {
    tooltip: {
      enabled: true
    },
    labels: {
      style: {
        colors: '#9CA3AF',
        fontSize: '12px'
      },
      formatter: (value: number) => {
        return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      }
    }
  },
  tooltip: {
    theme: 'dark',
    custom: function({ seriesIndex, dataPointIndex, w }: any) {
      const data = w.globals.seriesCandleO[seriesIndex][dataPointIndex]
      const o = w.globals.seriesCandleO[seriesIndex][dataPointIndex]
      const h = w.globals.seriesCandleH[seriesIndex][dataPointIndex]
      const l = w.globals.seriesCandleL[seriesIndex][dataPointIndex]
      const c = w.globals.seriesCandleC[seriesIndex][dataPointIndex]

      return `
        <div class="apexcharts-tooltip-candlestick p-2">
          <div class="font-semibold mb-1 text-white">Price Details</div>
          <div class="flex justify-between gap-4 text-sm">
            <div>
              <div class="text-gray-400">Open:</div>
              <div class="text-white font-medium">$${o?.toFixed(2) || 0}</div>
            </div>
            <div>
              <div class="text-gray-400">High:</div>
              <div class="text-green-400 font-medium">$${h?.toFixed(2) || 0}</div>
            </div>
          </div>
          <div class="flex justify-between gap-4 text-sm mt-1">
            <div>
              <div class="text-gray-400">Low:</div>
              <div class="text-red-400 font-medium">$${l?.toFixed(2) || 0}</div>
            </div>
            <div>
              <div class="text-gray-400">Close:</div>
              <div class="text-white font-medium">$${c?.toFixed(2) || 0}</div>
            </div>
          </div>
        </div>
      `
    }
  }
}))
</script>

<style scoped>
.apex-chart-wrapper {
  @apply w-full h-full;
}

:deep(.apexcharts-canvas) {
  @apply w-full;
}

:deep(.apexcharts-tooltip) {
  @apply !bg-gray-800 !border-gray-700;
}
</style>
