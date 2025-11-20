<template>
  <div class="fear-greed-chart">
    <apexchart
      v-if="series.length > 0"
      :options="chartOptions"
      :series="series"
      type="area"
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

interface DataPoint {
  timestamp: Date | string
  value: number // sentiment score from -1 to 1
}

interface Props {
  data: DataPoint[]
  height?: number | string
}

const props = withDefaults(defineProps<Props>(), {
  height: 350
})

// Convert sentiment score (-1 to 1) to Fear & Greed index (0 to 100)
const convertToFearGreed = (sentiment: number): number => {
  // sentiment: -1 (extreme fear) to 1 (extreme greed)
  // Convert to 0-100 scale
  return ((sentiment + 1) / 2) * 100
}

const series = computed(() => {
  if (!props.data || props.data.length === 0) return []

  return [{
    name: 'Fear & Greed Index',
    data: props.data.map(item => ({
      x: new Date(item.timestamp).getTime(),
      y: convertToFearGreed(item.value)
    }))
  }]
})

const getFearGreedLabel = (value: number): string => {
  if (value <= 25) return 'Extreme Fear'
  if (value <= 45) return 'Fear'
  if (value <= 55) return 'Neutral'
  if (value <= 75) return 'Greed'
  return 'Extreme Greed'
}

const getFearGreedColor = (value: number): string => {
  if (value <= 25) return '#EF4444' // red
  if (value <= 45) return '#F59E0B' // orange
  if (value <= 55) return '#EAB308' // yellow
  if (value <= 75) return '#10B981' // green
  return '#059669' // dark green
}

const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    fontFamily: 'Inter, sans-serif',
    zoom: {
      enabled: true,
      type: 'x',
      autoScaleYaxis: true
    },
    toolbar: {
      show: true
    },
    background: 'transparent',
    animations: {
      enabled: true,
      easing: 'easeinout',
      speed: 800
    }
  },
  colors: ['#10B981'],
  dataLabels: {
    enabled: false
  },
  stroke: {
    curve: 'smooth',
    width: 3
  },
  fill: {
    type: 'gradient',
    gradient: {
      shade: 'dark',
      type: 'vertical',
      shadeIntensity: 0.4,
      gradientToColors: ['#059669'],
      inverseColors: false,
      opacityFrom: 0.6,
      opacityTo: 0.1,
      stops: [0, 90, 100]
    }
  },
  grid: {
    borderColor: '#374151',
    strokeDashArray: 4,
    xaxis: {
      lines: {
        show: true
      }
    },
    yaxis: {
      lines: {
        show: true
      }
    },
    padding: {
      top: 0,
      right: 0,
      bottom: 0,
      left: 10
    }
  },
  xaxis: {
    type: 'datetime',
    labels: {
      style: {
        colors: '#9CA3AF',
        fontSize: '12px'
      },
      datetimeUTC: false
    },
    axisBorder: {
      show: false
    },
    axisTicks: {
      show: false
    }
  },
  yaxis: {
    min: 0,
    max: 100,
    tickAmount: 5,
    labels: {
      style: {
        colors: '#9CA3AF',
        fontSize: '12px'
      },
      formatter: (value: number) => {
        return value.toFixed(0)
      }
    }
  },
  tooltip: {
    theme: 'dark',
    x: {
      format: 'dd MMM yyyy HH:mm'
    },
    y: {
      formatter: (value: number) => {
        const label = getFearGreedLabel(value)
        return `${value.toFixed(1)} - ${label}`
      }
    },
    marker: {
      show: true
    }
  },
  annotations: {
    yaxis: [
      {
        y: 0,
        y2: 25,
        fillColor: '#EF4444',
        opacity: 0.1,
        label: {
          text: 'Extreme Fear',
          style: {
            color: '#EF4444',
            background: 'transparent',
            fontSize: '10px'
          },
          position: 'left',
          offsetX: 5
        }
      },
      {
        y: 25,
        y2: 45,
        fillColor: '#F59E0B',
        opacity: 0.1,
        label: {
          text: 'Fear',
          style: {
            color: '#F59E0B',
            background: 'transparent',
            fontSize: '10px'
          },
          position: 'left',
          offsetX: 5
        }
      },
      {
        y: 45,
        y2: 55,
        fillColor: '#EAB308',
        opacity: 0.1,
        label: {
          text: 'Neutral',
          style: {
            color: '#EAB308',
            background: 'transparent',
            fontSize: '10px'
          },
          position: 'left',
          offsetX: 5
        }
      },
      {
        y: 55,
        y2: 75,
        fillColor: '#10B981',
        opacity: 0.1,
        label: {
          text: 'Greed',
          style: {
            color: '#10B981',
            background: 'transparent',
            fontSize: '10px'
          },
          position: 'left',
          offsetX: 5
        }
      },
      {
        y: 75,
        y2: 100,
        fillColor: '#059669',
        opacity: 0.1,
        label: {
          text: 'Extreme Greed',
          style: {
            color: '#059669',
            background: 'transparent',
            fontSize: '10px'
          },
          position: 'left',
          offsetX: 5
        }
      }
    ]
  },
  legend: {
    show: false
  }
}))
</script>

<style scoped>
.fear-greed-chart {
  @apply w-full h-full;
}

:deep(.apexcharts-canvas) {
  @apply w-full;
}

:deep(.apexcharts-tooltip) {
  @apply !bg-gray-800 !border-gray-700;
}

:deep(.apexcharts-tooltip-title) {
  @apply !bg-gray-700 !border-gray-600;
}

:deep(.apexcharts-yaxis-annotation-label) {
  @apply !text-xs;
}
</style>
