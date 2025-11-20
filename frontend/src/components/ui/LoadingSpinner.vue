<template>
  <div :class="containerClasses">
    <div :class="spinnerClasses"></div>
    <p v-if="message" class="mt-4 text-sm text-gray-600">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  size?: 'sm' | 'md' | 'lg'
  message?: string
  centered?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  centered: true,
})

const containerClasses = computed(() => {
  return props.centered ? 'flex flex-col items-center justify-center' : ''
})

const spinnerClasses = computed(() => {
  const base = 'animate-spin rounded-full border-b-2 border-primary-600'

  const sizes = {
    sm: 'h-6 w-6',
    md: 'h-10 w-10',
    lg: 'h-16 w-16',
  }

  return `${base} ${sizes[props.size]}`
})
</script>
