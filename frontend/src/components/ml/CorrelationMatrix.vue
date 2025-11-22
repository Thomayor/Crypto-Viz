<template>
  <div class="correlation-matrix">
    <div class="flex justify-between items-center mb-4">
      <div>
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
          Correlation Matrix
        </h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Correlation relationships between cryptocurrencies
        </p>
      </div>
      <div class="flex gap-2">
        <select
          v-model="timeWindow"
          @change="loadMatrix"
          class="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-sm"
        >
          <option value="1d">1 Day</option>
          <option value="7d">7 Days</option>
          <option value="30d">30 Days</option>
        </select>
        <button
          @click="loadMatrix"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          :disabled="loading"
        >
          Refresh
        </button>
      </div>
    </div>

    <!-- Heatmap -->
    <div v-if="matrix" class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <!-- Matrix container with horizontal centering -->
      <div class="overflow-x-auto flex justify-center">
        <div class="min-w-max">
          <!-- Header row -->
          <div class="flex">
            <div class="w-16"></div>
            <div
              v-for="symbol in matrix.symbols"
              :key="symbol"
              class="w-20 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 pb-2"
            >
              {{ symbol }}
            </div>
          </div>

          <!-- Matrix rows -->
          <div
            v-for="(row, rowIndex) in matrix.matrix"
            :key="row.symbol"
            class="flex"
          >
            <div class="w-16 flex items-center justify-end pr-2 text-xs font-semibold text-gray-700 dark:text-gray-300">
              {{ row.symbol }}
            </div>
            <div
              v-for="(value, symbol) in row.correlations"
              :key="symbol"
              class="w-20 h-16 border border-gray-200 dark:border-gray-700 relative group cursor-pointer"
              :style="{ backgroundColor: getColor(value) }"
              @click="showDetails(row.symbol, symbol, value)"
            >
              <div class="absolute inset-0 flex items-center justify-center text-xs font-semibold"
                   :class="getTextColor(value)">
                {{ value !== null ? value.toFixed(2) : 'N/A' }}
              </div>

              <!-- Tooltip -->
              <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                <div class="bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
                  {{ row.symbol }} ↔ {{ symbol }}: {{ value !== null ? value.toFixed(3) : 'N/A' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div class="mt-6 flex items-center justify-center gap-4">
        <div class="flex items-center gap-2">
          <div class="w-4 h-4 rounded" :style="{ backgroundColor: getColor(-1) }"></div>
          <span class="text-xs text-gray-600 dark:text-gray-400">-1.0 (Negative)</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-4 h-4 rounded" :style="{ backgroundColor: getColor(0) }"></div>
          <span class="text-xs text-gray-600 dark:text-gray-400">0.0 (None)</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-4 h-4 rounded" :style="{ backgroundColor: getColor(1) }"></div>
          <span class="text-xs text-gray-600 dark:text-gray-400">+1.0 (Positive)</span>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else-if="loading" class="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
      <div class="text-gray-500">Loading correlation matrix...</div>
    </div>

    <!-- Empty State -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
      <p class="text-gray-500 mb-2">No correlation data available</p>
      <p class="text-sm text-gray-400">Correlation analysis requires historical price data</p>
    </div>

    <!-- Interpretation Guide -->
    <div class="mt-6 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
      <h4 class="font-semibold text-purple-900 dark:text-purple-200 mb-2">
        Understanding Correlation
      </h4>
      <div class="text-sm text-purple-800 dark:text-purple-300 space-y-2">
        <p>
          <span class="font-semibold">+1.0:</span> Perfect positive correlation - prices move together
        </p>
        <p>
          <span class="font-semibold">0.0:</span> No correlation - prices move independently
        </p>
        <p>
          <span class="font-semibold">-1.0:</span> Perfect negative correlation - prices move in opposite directions (good for hedging)
        </p>
      </div>
    </div>

    <!-- Details Modal -->
    <div
      v-if="selectedPair"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      @click.self="selectedPair = null"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-bold text-gray-900 dark:text-white">
            {{ selectedPair.symbol1 }} ↔ {{ selectedPair.symbol2 }}
          </h3>
          <button
            @click="selectedPair = null"
            class="text-gray-500 hover:text-gray-700"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="space-y-4">
          <div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Correlation Coefficient</div>
            <div class="text-3xl font-bold" :class="getCoefficientClass(selectedPair.value)">
              {{ selectedPair.value?.toFixed(3) || 'N/A' }}
            </div>
          </div>

          <div>
            <div class="text-sm text-gray-600 dark:text-gray-400 mb-2">Strength</div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div
                class="h-3 rounded-full"
                :class="getStrengthBarClass(selectedPair.value)"
                :style="{ width: `${Math.abs(selectedPair.value || 0) * 100}%` }"
              ></div>
            </div>
            <div class="text-sm mt-1 font-semibold">
              {{ getStrengthLabel(selectedPair.value) }}
            </div>
          </div>

          <div class="text-sm text-gray-700 dark:text-gray-300">
            <span v-if="selectedPair.value && selectedPair.value > 0.7">
              These cryptocurrencies tend to move together strongly. When one goes up, the other typically does too.
            </span>
            <span v-else-if="selectedPair.value && selectedPair.value < -0.7">
              These cryptocurrencies move in opposite directions. Good for portfolio diversification and hedging.
            </span>
            <span v-else-if="selectedPair.value && Math.abs(selectedPair.value) < 0.3">
              These cryptocurrencies have weak correlation. Their prices move relatively independently.
            </span>
            <span v-else>
              These cryptocurrencies have moderate correlation. There's some relationship in their price movements.
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMLStore } from '@/stores/ml'

const mlStore = useMLStore()

const loading = ref(false)
const timeWindow = ref('7d')
const selectedPair = ref<{ symbol1: string; symbol2: string; value: number | null } | null>(null)

const matrix = ref<any>(null)

async function loadMatrix() {
  loading.value = true
  try {
    await mlStore.fetchCorrelationMatrix()
    matrix.value = mlStore.correlationMatrix
  } catch (error) {
    console.error('Error loading correlation matrix:', error)
  } finally {
    loading.value = false
  }
}

function getColor(value: number | null): string {
  if (value === null) return '#e5e7eb'

  // Red (-1) to White (0) to Green (+1)
  if (value < 0) {
    const intensity = Math.abs(value) * 255
    return `rgb(${intensity}, ${80}, ${80})`
  } else {
    const intensity = value * 255
    return `rgb(${80}, ${intensity}, ${80})`
  }
}

function getTextColor(value: number | null): string {
  if (value === null) return 'text-gray-600'
  return Math.abs(value) > 0.5 ? 'text-white' : 'text-gray-900'
}

function getCoefficientClass(value: number | null): string {
  if (!value) return 'text-gray-500'
  if (value > 0.7) return 'text-green-600'
  if (value < -0.7) return 'text-red-600'
  return 'text-gray-900 dark:text-white'
}

function getStrengthBarClass(value: number | null): string {
  if (!value) return 'bg-gray-400'
  return value > 0 ? 'bg-green-600' : 'bg-red-600'
}

function getStrengthLabel(value: number | null): string {
  if (!value) return 'No correlation'
  const abs = Math.abs(value)
  if (abs > 0.8) return 'Very Strong'
  if (abs > 0.6) return 'Strong'
  if (abs > 0.4) return 'Moderate'
  if (abs > 0.2) return 'Weak'
  return 'Very Weak'
}

function showDetails(symbol1: string, symbol2: string, value: number | null) {
  selectedPair.value = { symbol1, symbol2, value }
}

onMounted(() => {
  loadMatrix()
})
</script>

<style scoped>
.correlation-matrix {
  @apply space-y-4;
}
</style>
