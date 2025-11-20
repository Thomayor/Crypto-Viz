<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'

const route = useRoute()

const shouldShowLayout = computed(() => {
  return route.meta.layout !== 'none'
})
</script>

<template>
  <AppLayout v-if="shouldShowLayout" />
  <router-view v-else />
</template>

<style>
/* No scoped styles needed - using global styles from main.css */
</style>
