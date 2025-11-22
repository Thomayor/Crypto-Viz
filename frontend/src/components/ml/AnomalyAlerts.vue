<template>
  <div class="anomaly-alerts">
    <div class="flex justify-between items-center mb-4">
      <div>
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
          Anomaly Alerts
        </h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Real-time detection of unusual price movements
        </p>
      </div>
      <div class="flex gap-2">
        <select
          v-model="severityFilter"
          @change="loadAnomalies"
          class="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-sm"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <button
          @click="loadAnomalies"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          :disabled="loading"
        >
          <span v-if="loading">Loading...</span>
          <span v-else>Refresh</span>
        </button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-lg">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-red-600 dark:text-red-400">Critical</div>
            <div class="text-2xl font-bold text-red-700 dark:text-red-300">
              {{ criticalCount }}
            </div>
          </div>
          <div class="text-red-600 dark:text-red-400">
            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
      </div>

      <div class="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 p-4 rounded-lg">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-orange-600 dark:text-orange-400">High</div>
            <div class="text-2xl font-bold text-orange-700 dark:text-orange-300">
              {{ highCount }}
            </div>
          </div>
          <div class="text-orange-600 dark:text-orange-400">
            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
      </div>

      <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-4 rounded-lg">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-yellow-600 dark:text-yellow-400">Medium</div>
            <div class="text-2xl font-bold text-yellow-700 dark:text-yellow-300">
              {{ mediumCount }}
            </div>
          </div>
          <div class="text-yellow-600 dark:text-yellow-400">
            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
      </div>

      <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4 rounded-lg">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-blue-600 dark:text-blue-400">Low</div>
            <div class="text-2xl font-bold text-blue-700 dark:text-blue-300">
              {{ lowCount }}
            </div>
          </div>
          <div class="text-blue-600 dark:text-blue-400">
            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Anomaly Cards -->
    <div class="space-y-4">
      <div v-if="loading" class="text-center py-8 text-gray-500">
        Loading anomalies...
      </div>

      <div v-else-if="anomalies.length === 0" class="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
        <svg class="w-16 h-16 mx-auto text-green-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-gray-700 dark:text-gray-300 mb-2">No active anomalies detected</p>
        <p class="text-sm text-gray-500">The system is monitoring for unusual price movements</p>
      </div>

      <div
        v-else
        v-for="anomaly in anomalies"
        :key="anomaly.id"
        class="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden border-l-4"
        :class="getSeverityBorderClass(anomaly.severity)"
      >
        <div class="p-6">
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xl font-bold text-gray-900 dark:text-white">
                  {{ anomaly.symbol }}
                </span>
                <span
                  class="px-2 py-1 text-xs font-semibold rounded-full"
                  :class="getSeverityBadgeClass(anomaly.severity)"
                >
                  {{ anomaly.severity.toUpperCase() }}
                </span>
                <span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                  {{ formatAnomalyType(anomaly.anomaly_type) }}
                </span>
              </div>
              <p class="text-gray-700 dark:text-gray-300 mb-2">
                {{ anomaly.description }}
              </p>
              <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                <span>Score: {{ anomaly.anomaly_score.toFixed(2) }}</span>
                <span>•</span>
                <span>{{ formatDate(anomaly.detected_at) }}</span>
              </div>
            </div>
            <button
              @click="resolveAnomaly(anomaly.id)"
              class="ml-4 px-3 py-1 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded text-sm font-medium transition-colors"
            >
              Resolve
            </button>
          </div>

          <!-- Anomaly Details Bar -->
          <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
            <div class="grid grid-cols-3 gap-4 text-sm">
              <div v-if="anomaly.expected_value">
                <div class="text-gray-500 dark:text-gray-400">Expected</div>
                <div class="font-semibold text-gray-900 dark:text-white">
                  ${{ anomaly.expected_value.toFixed(2) }}
                </div>
              </div>
              <div v-if="anomaly.actual_value">
                <div class="text-gray-500 dark:text-gray-400">Actual</div>
                <div class="font-semibold" :class="getValueChangeClass(anomaly.expected_value, anomaly.actual_value)">
                  ${{ anomaly.actual_value.toFixed(2) }}
                </div>
              </div>
              <div v-if="anomaly.deviation">
                <div class="text-gray-500 dark:text-gray-400">Deviation</div>
                <div class="font-semibold text-red-600 dark:text-red-400">
                  {{ anomaly.deviation.toFixed(2) }}σ
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMLStore } from '@/stores/ml'

const mlStore = useMLStore()

const loading = ref(false)
const severityFilter = ref('')

const anomalies = computed(() => mlStore.anomalies)

const criticalCount = computed(() =>
  anomalies.value.filter(a => a.severity === 'critical').length
)

const highCount = computed(() =>
  anomalies.value.filter(a => a.severity === 'high').length
)

const mediumCount = computed(() =>
  anomalies.value.filter(a => a.severity === 'medium').length
)

const lowCount = computed(() =>
  anomalies.value.filter(a => a.severity === 'low').length
)

async function loadAnomalies() {
  loading.value = true
  try {
    await mlStore.fetchAnomalies(severityFilter.value || undefined)
  } catch (error) {
    console.error('Error loading anomalies:', error)
  } finally {
    loading.value = false
  }
}

async function resolveAnomaly(anomalyId: string) {
  if (confirm('Mark this anomaly as resolved?')) {
    try {
      await mlStore.resolveAnomaly(anomalyId)
    } catch (error) {
      alert('Failed to resolve anomaly')
    }
  }
}

function getSeverityBorderClass(severity: string): string {
  switch (severity) {
    case 'critical': return 'border-red-500'
    case 'high': return 'border-orange-500'
    case 'medium': return 'border-yellow-500'
    case 'low': return 'border-blue-500'
    default: return 'border-gray-500'
  }
}

function getSeverityBadgeClass(severity: string): string {
  switch (severity) {
    case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
    case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    case 'low': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
  }
}

function getValueChangeClass(expected: number | null, actual: number | null): string {
  if (!expected || !actual) return 'text-gray-900 dark:text-white'
  return actual > expected ? 'text-green-600' : 'text-red-600'
}

function formatAnomalyType(type: string): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`
  if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`
  if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
  return 'Just now'
}

onMounted(() => {
  loadAnomalies()
})
</script>

<style scoped>
.anomaly-alerts {
  @apply space-y-4;
}
</style>
