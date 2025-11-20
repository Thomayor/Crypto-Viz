<template>
  <div class="apex-chart-wrapper">
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
  value: number
}

interface Props {
  data: DataPoint[]
  title?: string
  colors?: string[]
  height?: number | string
  yAxisLabel?: string
  fillOpacity?: number
  formatType?: 'currency' | 'percentage' | 'number'
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  colors: () => ['#06B6D4', '#3B82F6'],
  height: 350,
  yAxisLabel: 'Value',
  fillOpacity: 0.5,
  formatType: 'currency'
})

const series = computed(() => {
  if (!props.data || props.data.length === 0) return []

  return [{
    name: props.yAxisLabel,
    data: props.data.map(item => ({
      x: new Date(item.timestamp).getTime(),
      y: item.value
    }))
  }]
})

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
  colors: props.colors,
  dataLabels: {
    enabled: false
  },
  stroke: {
    curve: 'smooth',
    width: 2
  },
  fill: {
    type: 'gradient',
    gradient: {
      shade: 'dark',
      type: 'vertical',
      shadeIntensity: 0.5,
      gradientToColors: props.colors,
      inverseColors: false,
      opacityFrom: props.fillOpacity,
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
    labels: {
      style: {
        colors: '#9CA3AF',
        fontSize: '12px'
      },
      formatter: (value: number) => {
        if (props.formatType === 'percentage') {
          return value.toFixed(1) + '%'
        } else if (props.formatType === 'number') {
          return value.toFixed(2)
        } else {
          // currency format
          if (value >= 1000000000) {
            return '$' + (value / 1000000000).toFixed(2) + 'B'
          } else if (value >= 1000000) {
            return '$' + (value / 1000000).toFixed(2) + 'M'
          } else if (value >= 1000) {
            return '$' + (value / 1000).toFixed(2) + 'K'
          }
          return '$' + value.toFixed(2)
        }
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
        if (props.formatType === 'percentage') {
          return value.toFixed(1) + '%'
        } else if (props.formatType === 'number') {
          return value.toFixed(2)
        } else {
          return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        }
      }
    }
  },
  legend: {
    show: false
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

:deep(.apexcharts-tooltip-title) {
  @apply !bg-gray-700 !border-gray-600;
}
</style>
