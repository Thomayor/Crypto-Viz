<template>
  <div class="prediction-chart">
    <div class="flex justify-between items-center mb-4">
      <div>
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
          Price Predictions
        </h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          ML-powered price forecasting with confidence intervals
        </p>
      </div>
      <div class="flex gap-2">
        <select
          v-model="selectedSymbol"
          @change="loadPredictions"
          class="px-3 py-2 bg-white text-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg"
        >
          <option value="BTC">Bitcoin (BTC)</option>
          <option value="ETH">Ethereum (ETH)</option>
          <option value="BNB">BNB</option>
          <option value="SOL">Solana (SOL)</option>
          <option value="XRP">XRP</option>
        </select>
        <button
          @click="loadPredictions"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          :disabled="loading"
        >
          Refresh
        </button>
      </div>
    </div>

    <!-- Model Performance Metrics -->
    <div v-if="latestPrediction" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600 dark:text-gray-400">Predicted Price</div>
        <div class="text-2xl font-bold text-blue-600">
          ${{ (latestPrediction.predicted_value || 0).toFixed(2) }}
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600 dark:text-gray-400">Confidence</div>
        <div class="text-2xl font-bold text-green-600">
          {{ ((latestPrediction.confidence || 0) * 100).toFixed(1) }}%
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600 dark:text-gray-400">RMSE</div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ latestPrediction.rmse ? latestPrediction.rmse.toFixed(2) : 'N/A' }}
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600 dark:text-gray-400">R² Score</div>
        <div class="text-2xl font-bold text-purple-600">
          {{ latestPrediction.r2_score ? latestPrediction.r2_score.toFixed(3) : 'N/A' }}
        </div>
      </div>
    </div>

    <!-- Predictions Table -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Predicted At
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Predicted Value
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Confidence
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Valid Until
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Model
              </th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-if="loading">
              <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                Loading predictions...
              </td>
            </tr>
            <tr v-else-if="predictions.length === 0">
              <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                No predictions available. ML models may need to be enabled.
              </td>
            </tr>
            <tr
              v-else
              v-for="prediction in predictions.slice(0, 10)"
              :key="prediction.id"
              class="hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                {{ formatDate(prediction.predicted_at) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900 dark:text-white">
                ${{ (prediction.predicted_value || 0).toFixed(2) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-2">
                    <div
                      class="bg-green-600 h-2 rounded-full"
                      :style="{ width: `${(prediction.confidence || 0) * 100}%` }"
                    ></div>
                  </div>
                  <span class="text-sm text-gray-700 dark:text-gray-300">
                    {{ ((prediction.confidence || 0) * 100).toFixed(0) }}%
                  </span>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                {{ formatDate(prediction.valid_until) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  {{ prediction.model_name }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Prediction Explanation -->
    <div v-if="latestPrediction" class="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
      <div class="flex items-start">
        <svg class="w-5 h-5 text-blue-600 mr-3 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
        </svg>
        <div>
          <h4 class="font-semibold text-blue-900 dark:text-blue-200 mb-1">
            About These Predictions
          </h4>
          <p class="text-sm text-blue-800 dark:text-blue-300">
            Predictions are generated using {{ latestPrediction.model_name }} trained on historical price data.
            The confidence score indicates model certainty ({{ ((latestPrediction.confidence || 0) * 100).toFixed(0) }}%).
            <span v-if="latestPrediction.r2_score">
              R² score of {{ (latestPrediction.r2_score || 0).toFixed(3) }} indicates
              {{ (latestPrediction.r2_score || 0) > 0.8 ? 'high' : (latestPrediction.r2_score || 0) > 0.5 ? 'moderate' : 'low' }} model accuracy.
            </span>
          </p>
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
const selectedSymbol = ref('BTC')

// Filter predictions by selected symbol locally instead of filtering the store
const predictions = computed(() => {
  if (!mlStore.predictions || mlStore.predictions.length === 0) return []
  return mlStore.predictions.filter(p => p.symbol === selectedSymbol.value)
})

const latestPrediction = computed(() =>
  predictions.value.length > 0 ? predictions.value[0] : null
)

async function loadPredictions() {
  loading.value = true
  try {
    // Load all predictions without filtering - filter happens in computed
    await mlStore.fetchPredictions()
  } catch (error) {
    console.error('Error loading predictions:', error)
  } finally {
    loading.value = false
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadPredictions()
})
</script>

<style scoped>
.prediction-chart {
  @apply space-y-4;
}
</style>
