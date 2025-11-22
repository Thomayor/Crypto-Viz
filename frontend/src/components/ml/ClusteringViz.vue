<template>
  <div class="clustering-viz">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
        Cryptocurrency Clustering
      </h3>
      <button
        @click="refreshData"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        :disabled="loading"
      >
        <span v-if="loading">Refreshing...</span>
        <span v-else>Refresh</span>
      </button>
    </div>

    <!-- Statistics Cards -->
    <div v-if="statistics" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600 dark:text-gray-400">Total Cryptos</div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ statistics.total_cryptos }}
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600 dark:text-gray-400">Clusters</div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ statistics.num_clusters }}
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600 dark:text-gray-400">Silhouette Score</div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ statistics.overall_silhouette_score.toFixed(3) }}
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600 dark:text-gray-400">Largest Cluster</div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ largestCluster?.crypto_count || 0 }}
        </div>
      </div>
    </div>

    <!-- Cluster Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div
        v-for="cluster in statistics?.clusters"
        :key="cluster.cluster_id"
        class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg"
        :class="selectedCluster === cluster.cluster_id ? 'ring-2 ring-blue-500' : ''"
      >
        <div class="flex justify-between items-center mb-4">
          <div>
            <h4 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ cluster.cluster_label }}
            </h4>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Cluster {{ cluster.cluster_id }}
            </p>
          </div>
          <div class="text-right">
            <div class="text-2xl font-bold text-blue-600">
              {{ cluster.crypto_count }}
            </div>
            <div class="text-xs text-gray-500">cryptos</div>
          </div>
        </div>

        <div class="mb-4">
          <div class="flex justify-between text-sm mb-1">
            <span class="text-gray-600 dark:text-gray-400">Silhouette Score</span>
            <span class="font-semibold">{{ cluster.avg_silhouette_score.toFixed(3) }}</span>
          </div>
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              class="bg-blue-600 h-2 rounded-full"
              :style="{ width: `${(cluster.avg_silhouette_score * 100)}%` }"
            ></div>
          </div>
        </div>

        <button
          @click="viewClusterDetails(cluster.cluster_id)"
          class="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          View Details
        </button>
      </div>
    </div>

    <!-- Cluster Details Modal -->
    <div
      v-if="selectedCluster !== null && clusterDetails"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      @click.self="selectedCluster = null"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-y-auto">
        <div class="p-6 border-b border-gray-200 dark:border-gray-700">
          <div class="flex justify-between items-center">
            <h3 class="text-2xl font-bold text-gray-900 dark:text-white">
              {{ clusterDetails.cluster_label }}
            </h3>
            <button
              @click="selectedCluster = null"
              class="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 mt-2">
            {{ clusterDetails.crypto_count }} cryptocurrencies in this cluster
          </p>
        </div>

        <div class="p-6">
          <!-- Cluster Characteristics -->
          <div v-if="clusterDetails.characteristics" class="mb-6">
            <h4 class="text-lg font-semibold mb-3">Cluster Characteristics</h4>
            <div class="grid grid-cols-2 gap-4">
              <div
                v-for="(char, key) in clusterDetails.characteristics"
                :key="key"
                class="bg-gray-50 dark:bg-gray-700 p-3 rounded"
              >
                <div class="text-sm text-gray-600 dark:text-gray-400 capitalize">
                  {{ key.replace(/_/g, ' ') }}
                </div>
                <div class="text-lg font-semibold">
                  {{ formatNumber(char.avg) }}
                </div>
                <div class="text-xs text-gray-500">
                  Range: {{ formatNumber(char.min) }} - {{ formatNumber(char.max) }}
                </div>
              </div>
            </div>
          </div>

          <!-- Cryptocurrencies List -->
          <div>
            <h4 class="text-lg font-semibold mb-3">Cryptocurrencies</h4>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              <div
                v-for="crypto in clusterDetails.cryptos"
                :key="crypto.symbol"
                class="bg-gray-50 dark:bg-gray-700 px-3 py-2 rounded text-center font-medium"
              >
                {{ crypto.symbol }}
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
import { api } from '@/services/api'

const mlStore = useMLStore()

const loading = ref(false)
const statistics = ref<any>(null)
const selectedCluster = ref<number | null>(null)
const clusterDetails = ref<any>(null)

const largestCluster = computed(() => {
  if (!statistics.value?.clusters) return null
  return statistics.value.clusters.reduce((max: any, cluster: any) =>
    cluster.crypto_count > (max?.crypto_count || 0) ? cluster : max
  , null)
})

async function refreshData() {
  loading.value = true
  try {
    await mlStore.fetchClusterStatistics()
    statistics.value = mlStore.clusterStatistics
  } catch (error) {
    console.error('Error refreshing cluster data:', error)
  } finally {
    loading.value = false
  }
}

async function viewClusterDetails(clusterId: number) {
  selectedCluster.value = clusterId
  try {
    const response = await api.get(`/analytics/ml/clusters/${clusterId}`)
    clusterDetails.value = response.data
  } catch (error) {
    console.error('Error fetching cluster details:', error)
  }
}

function formatNumber(value: number): string {
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`
  return value.toFixed(2)
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.clustering-viz {
  @apply space-y-4;
}
</style>
