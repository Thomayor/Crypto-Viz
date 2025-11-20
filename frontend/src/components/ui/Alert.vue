<template>
  <div v-if="modelValue" :class="alertClasses" role="alert">
    <div class="flex">
      <div class="flex-shrink-0">
        <component :is="icon" class="h-5 w-5" />
      </div>
      <div class="ml-3 flex-1">
        <h3 v-if="title" class="text-sm font-medium">{{ title }}</h3>
        <div class="text-sm">
          <slot></slot>
        </div>
      </div>
      <div v-if="dismissible" class="ml-auto pl-3">
        <button
          @click="emit('update:modelValue', false)"
          class="-mx-1.5 -my-1.5 rounded-lg p-1.5 hover:bg-black/10 transition-colors"
        >
          <span class="sr-only">Dismiss</span>
          <XMarkIcon class="h-5 w-5" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XCircleIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'

interface Props {
  modelValue: boolean
  variant?: 'success' | 'danger' | 'warning' | 'info'
  title?: string
  dismissible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'info',
  dismissible: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const alertClasses = computed(() => {
  const base = 'rounded-lg p-4'

  const variants = {
    success: 'bg-green-50 text-green-800 [&_svg]:text-green-400',
    danger: 'bg-red-50 text-red-800 [&_svg]:text-red-400',
    warning: 'bg-yellow-50 text-yellow-800 [&_svg]:text-yellow-400',
    info: 'bg-blue-50 text-blue-800 [&_svg]:text-blue-400',
  }

  return `${base} ${variants[props.variant]}`
})

const icon = computed(() => {
  const icons = {
    success: CheckCircleIcon,
    danger: XCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon,
  }
  return icons[props.variant]
})
</script>
