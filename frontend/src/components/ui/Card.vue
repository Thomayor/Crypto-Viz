<template>
  <div :class="cardClasses">
    <div v-if="title || $slots.header" class="border-b border-gray-200 pb-4 mb-4">
      <slot name="header">
        <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
      </slot>
    </div>

    <div :class="{ 'p-0': noPadding }">
      <slot></slot>
    </div>

    <div v-if="$slots.footer" class="border-t border-gray-200 pt-4 mt-4">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title?: string
  noPadding?: boolean
  variant?: 'default' | 'bordered' | 'elevated'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  noPadding: false,
})

const cardClasses = computed(() => {
  const base = 'bg-white rounded-lg'
  const padding = props.noPadding ? '' : 'p-6'

  const variants = {
    default: 'shadow-md',
    bordered: 'border-2 border-gray-200',
    elevated: 'shadow-xl',
  }

  return `${base} ${padding} ${variants[props.variant]}`
})
</script>
