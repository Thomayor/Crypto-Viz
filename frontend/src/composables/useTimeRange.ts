import { ref, computed } from 'vue'

export type TimeRangeValue = '1h' | '4h' | '12h' | '24h' | '7d' | '30d' | '90d'

interface TimeRangeConfig {
  label: string
  value: TimeRangeValue
  hours: number
  dataPoints: number
  dateFormat: string
}

const timeRangeConfigs: TimeRangeConfig[] = [
  { label: '1 Hour', value: '1h', hours: 1, dataPoints: 60, dateFormat: 'HH:mm' },
  { label: '4 Hours', value: '4h', hours: 4, dataPoints: 48, dateFormat: 'HH:mm' },
  { label: '12 Hours', value: '12h', hours: 12, dataPoints: 72, dateFormat: 'HH:mm' },
  { label: '24 Hours', value: '24h', hours: 24, dataPoints: 96, dateFormat: 'MMM dd HH:mm' },
  { label: '7 Days', value: '7d', hours: 168, dataPoints: 168, dateFormat: 'MMM dd' },
  { label: '30 Days', value: '30d', hours: 720, dataPoints: 180, dateFormat: 'MMM dd' },
  { label: '90 Days', value: '90d', hours: 2160, dataPoints: 180, dateFormat: 'MMM dd' }
]

export function useTimeRange(initialValue: TimeRangeValue = '24h') {
  const selectedRange = ref<TimeRangeValue>(initialValue)

  const currentConfig = computed(() => {
    return timeRangeConfigs.find(c => c.value === selectedRange.value) || timeRangeConfigs[3]
  })

  const hours = computed(() => currentConfig.value.hours)
  const dataPoints = computed(() => currentConfig.value.dataPoints)
  const dateFormat = computed(() => currentConfig.value.dateFormat)
  const label = computed(() => currentConfig.value.label)

  const setTimeRange = (value: TimeRangeValue) => {
    selectedRange.value = value
  }

  const timeRangeToHours = (range: TimeRangeValue): number => {
    const config = timeRangeConfigs.find(c => c.value === range)
    return config?.hours || 24
  }

  const getTimeRangeLabel = (range: TimeRangeValue): string => {
    const config = timeRangeConfigs.find(c => c.value === range)
    return config?.label || '24 Hours'
  }

  return {
    selectedRange,
    hours,
    dataPoints,
    dateFormat,
    label,
    setTimeRange,
    timeRangeToHours,
    getTimeRangeLabel,
    configs: timeRangeConfigs
  }
}
