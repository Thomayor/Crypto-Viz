<template>
  <div class="time-range-selector">
    <div class="flex items-center gap-1 p-1 bg-gray-800/50 rounded-lg border border-gray-700/50">
      <button
        v-for="option in timeOptions"
        :key="option.value"
        @click="selectTimeRange(option.value)"
        :class="[
          'px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200',
          modelValue === option.value
            ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/25'
            : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
        ]"
      >
        {{ option.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export type TimeRangeValue = '1h' | '4h' | '12h' | '24h' | '7d' | '30d' | '90d'

interface TimeOption {
  label: string
  value: TimeRangeValue
  hours: number
}

interface Props {
  modelValue: TimeRangeValue
  options?: TimeRangeValue[]
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '24h',
  options: () => ['1h', '4h', '12h', '24h', '7d', '30d'],
  compact: false
})

const emit = defineEmits<{
  'update:modelValue': [value: TimeRangeValue]
  'change': [value: TimeRangeValue, hours: number]
}>()

const allTimeOptions: TimeOption[] = [
  { label: '1H', value: '1h', hours: 1 },
  { label: '4H', value: '4h', hours: 4 },
  { label: '12H', value: '12h', hours: 12 },
  { label: '24H', value: '24h', hours: 24 },
  { label: '7D', value: '7d', hours: 168 },
  { label: '30D', value: '30d', hours: 720 },
  { label: '90D', value: '90d', hours: 2160 }
]

const timeOptions = computed(() => {
  return allTimeOptions.filter(opt => props.options.includes(opt.value))
})

const selectTimeRange = (value: TimeRangeValue) => {
  emit('update:modelValue', value)
  const option = allTimeOptions.find(o => o.value === value)
  if (option) {
    emit('change', value, option.hours)
  }
}

// Utility function to convert TimeRangeValue to hours
export const timeRangeToHours = (range: TimeRangeValue): number => {
  const option = allTimeOptions.find(o => o.value === range)
  return option?.hours || 24
}
</script>

<style scoped>
.time-range-selector {
  @apply inline-flex;
}
</style>
