<template>
  <div class="apex-chart-wrapper">
    <apexchart
      v-if="series.length > 0"
      :options="chartOptions"
      :series="series"
      type="line"
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

interface Props {
  data: Array<{ timestamp: Date | string; value: number }>
  title?: string
  color?: string
  height?: number | string
  yAxisLabel?: string
  smooth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  color: '#3B82F6',
  height: 350,
  yAxisLabel: 'Value',
  smooth: true
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
    type: 'line',
    fontFamily: 'Inter, sans-serif',
    zoom: {
      enabled: true,
      type: 'x',
      autoScaleYaxis: true
    },
    toolbar: {
      show: true,
      tools: {
        download: true,
        selection: true,
        zoom: true,
        zoomin: true,
        zoomout: true,
        pan: true,
        reset: true
      }
    },
    background: 'transparent'
  },
  colors: [props.color],
  dataLabels: {
    enabled: false
  },
  stroke: {
    curve: props.smooth ? 'smooth' : 'straight',
    width: 3
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
  },
  tooltip: {
    theme: 'dark',
    x: {
      format: 'dd MMM yyyy HH:mm'
    },
    y: {
      formatter: (value: number) => {
        return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      }
    }
  },
  legend: {
    show: false
  },
  fill: {
    type: 'gradient',
    gradient: {
      shade: 'dark',
      type: 'vertical',
      shadeIntensity: 0.5,
      gradientToColors: [props.color],
      inverseColors: false,
      opacityFrom: 0.8,
      opacityTo: 0.3,
      stops: [0, 100]
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

:deep(.apexcharts-tooltip-title) {
  @apply !bg-gray-700 !border-gray-600;
}
</style>
