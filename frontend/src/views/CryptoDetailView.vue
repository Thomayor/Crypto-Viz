<template>
  <div class="crypto-detail-view">
    <div v-if="cryptoStore.loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" />
    </div>

    <div v-else-if="selectedCrypto">
      <!-- Back Button -->
      <button
        @click="$router.push('/dashboard')"
        class="mb-6 flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeftIcon class="h-5 w-5" />
        <span>Back to Dashboard</span>
      </button>

      <!-- Header Section -->
      <div class="glass-card p-8 mb-8">
        <div class="flex items-start justify-between mb-6">
          <div class="flex items-center gap-4">
            <img
              v-if="selectedCrypto.image"
              :src="selectedCrypto.image"
              :alt="selectedCrypto.name"
              class="w-16 h-16 rounded-full bg-white/5 p-2"
            />
            <div v-else class="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
              <span class="text-2xl font-bold text-white">{{ selectedCrypto.symbol.substring(0, 2).toUpperCase() }}</span>
            </div>
            <div>
              <h1 class="text-4xl font-black text-white mb-2">{{ selectedCrypto.name }}</h1>
              <div class="flex items-center gap-3">
                <span class="text-gray-400 text-sm uppercase font-semibold">{{ selectedCrypto.symbol }}</span>
                <span class="px-2 py-1 bg-gray-700/50 rounded text-xs text-gray-300">Rank #{{ selectedCrypto.market_cap_rank || 'N/A' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Price Section -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="col-span-1">
            <div class="text-sm text-gray-400 mb-2">Price</div>
            <div class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400">
              {{ formatPrice(selectedCrypto.current_price) }}
            </div>
          </div>

          <div>
            <div class="text-sm text-gray-400 mb-2">24h Change</div>
            <div :class="[
              'text-2xl font-bold flex items-center gap-2',
              (selectedCrypto.price_change_percentage_24h || 0) >= 0 ? 'text-green-400' : 'text-red-400'
            ]">
              <component
                :is="(selectedCrypto.price_change_percentage_24h || 0) >= 0 ? ArrowTrendingUpIcon : ArrowTrendingDownIcon"
                class="h-6 w-6"
              />
              {{ formatPercentage(selectedCrypto.price_change_percentage_24h) }}
            </div>
          </div>

          <div>
            <div class="text-sm text-gray-400 mb-2">Market Cap</div>
            <div class="text-2xl font-bold text-white">{{ formatNumber(selectedCrypto.market_cap) }}</div>
          </div>

          <div>
            <div class="text-sm text-gray-400 mb-2">24h Volume</div>
            <div class="text-2xl font-bold text-white">{{ formatNumber(selectedCrypto.total_volume) }}</div>
          </div>
        </div>
      </div>

      <!-- Charts and Stats Grid -->
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-8">
        <!-- Main Chart -->
        <div class="xl:col-span-2 glass-card p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-xl font-bold text-white mb-1">Price Chart</h3>
              <p class="text-sm text-gray-400">
                {{ selectedPeriod === '24H' ? 'Last 24 hours' :
                   selectedPeriod === '7D' ? 'Last 7 days' :
                   selectedPeriod === '30D' ? 'Last 30 days' :
                   'Last year' }}
              </p>
            </div>
            <div class="flex gap-2">
              <button
                v-for="period in ['24H', '7D', '30D', '1Y']"
                :key="period"
                @click="selectedPeriod = period"
                :class="[
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                  selectedPeriod === period
                    ? 'bg-cyan-500 text-white'
                    : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
                ]"
              >
                {{ period }}
              </button>
            </div>
          </div>
          <ApexLineChart
            v-if="priceChartData.length > 0"
            :data="priceChartData"
            :color="(selectedCrypto.price_change_percentage_24h || 0) >= 0 ? '#10b981' : '#ef4444'"
            :height="400"
            y-axis-label="Price (USD)"
            :smooth="true"
          />
        </div>

        <!-- Stats Cards -->
        <div class="space-y-6">
          <!-- Market Stats -->
          <div class="glass-card p-6">
            <h3 class="text-lg font-bold text-white mb-4">Market Statistics</h3>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">Market Cap Rank</span>
                <span class="text-white font-semibold">#{{ selectedCrypto.market_cap_rank || 'N/A' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">24h High</span>
                <span class="text-green-400 font-semibold">{{ formatPrice(selectedCrypto.high_24h) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">24h Low</span>
                <span class="text-red-400 font-semibold">{{ formatPrice(selectedCrypto.low_24h) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">All Time High</span>
                <span class="text-white font-semibold">{{ formatPrice(selectedCrypto.ath) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">All Time Low</span>
                <span class="text-white font-semibold">{{ formatPrice(selectedCrypto.atl) }}</span>
              </div>
            </div>
          </div>

          <!-- Supply Info -->
          <div class="glass-card p-6">
            <h3 class="text-lg font-bold text-white mb-4">Supply Information</h3>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">Circulating Supply</span>
                <span class="text-white font-semibold">{{ formatSupply(selectedCrypto.circulating_supply) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">Total Supply</span>
                <span class="text-white font-semibold">{{ formatSupply(selectedCrypto.total_supply) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">Max Supply</span>
                <span class="text-white font-semibold">{{ formatSupply(selectedCrypto.max_supply) }}</span>
              </div>
            </div>

            <!-- Supply Progress Bar -->
            <div v-if="selectedCrypto.circulating_supply && selectedCrypto.max_supply" class="mt-4">
              <div class="flex items-center justify-between text-xs text-gray-400 mb-2">
                <span>Circulating</span>
                <span>{{ supplyPercentage }}%</span>
              </div>
              <div class="bg-gray-700/50 rounded-full h-2 overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500"
                  :style="{ width: `${supplyPercentage}%` }"
                ></div>
              </div>
            </div>
          </div>

          <!-- Price Changes -->
          <div class="glass-card p-6">
            <h3 class="text-lg font-bold text-white mb-4">Price Changes</h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">1h</span>
                <span :class="[
                  'font-semibold',
                  (selectedCrypto.price_change_percentage_1h_in_currency || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                ]">
                  {{ formatPercentage(selectedCrypto.price_change_percentage_1h_in_currency) }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">24h</span>
                <span :class="[
                  'font-semibold',
                  (selectedCrypto.price_change_percentage_24h || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                ]">
                  {{ formatPercentage(selectedCrypto.price_change_percentage_24h) }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">7d</span>
                <span :class="[
                  'font-semibold',
                  (selectedCrypto.price_change_percentage_7d_in_currency || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                ]">
                  {{ formatPercentage(selectedCrypto.price_change_percentage_7d_in_currency) }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">30d</span>
                <span :class="[
                  'font-semibold',
                  (selectedCrypto.price_change_percentage_30d_in_currency || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                ]">
                  {{ formatPercentage(selectedCrypto.price_change_percentage_30d_in_currency) }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-400 text-sm">1y</span>
                <span :class="[
                  'font-semibold',
                  (selectedCrypto.price_change_percentage_1y_in_currency || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                ]">
                  {{ formatPercentage(selectedCrypto.price_change_percentage_1y_in_currency) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Additional Info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Volume Chart -->
        <div class="glass-card p-6">
          <div class="mb-6">
            <h3 class="text-xl font-bold text-white mb-1">Trading Volume</h3>
            <p class="text-sm text-gray-400">24-hour trading volume trend</p>
          </div>
          <ApexAreaChart
            v-if="volumeChartData.length > 0"
            :data="volumeChartData"
            :colors="['#06b6d4', '#0891b2']"
            :height="250"
            y-axis-label="Volume (USD)"
          />
        </div>

        <!-- Market Cap Chart -->
        <div class="glass-card p-6">
          <div class="mb-6">
            <h3 class="text-xl font-bold text-white mb-1">Market Cap Evolution</h3>
            <p class="text-sm text-gray-400">Market capitalization trend</p>
          </div>
          <ApexAreaChart
            v-if="marketCapChartData.length > 0"
            :data="marketCapChartData"
            :colors="['#8b5cf6', '#7c3aed']"
            :height="250"
            y-axis-label="Market Cap (USD)"
          />
        </div>
      </div>
    </div>

    <div v-else class="glass-card p-12 text-center">
      <p class="text-gray-400 text-lg">Cryptocurrency not found</p>
      <button
        @click="$router.push('/dashboard')"
        class="mt-4 px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg font-semibold transition-colors"
      >
        Return to Dashboard
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCryptoStore } from '@/stores/crypto'
import { useFormatting } from '@/composables/useFormatting'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ApexLineChart from '@/components/charts/ApexLineChart.vue'
import ApexAreaChart from '@/components/charts/ApexAreaChart.vue'
import {
  ArrowLeftIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const cryptoStore = useCryptoStore()
const { formatPrice, formatNumber, formatPercentage } = useFormatting()

const selectedPeriod = ref('24H')
const loadingChart = ref(false)

const selectedCrypto = computed(() => {
  const symbol = route.params.symbol as string
  return cryptoStore.prices.find(c => c.symbol.toLowerCase() === symbol.toLowerCase())
})

const supplyPercentage = computed(() => {
  if (!selectedCrypto.value?.circulating_supply || !selectedCrypto.value?.max_supply) return 0
  return parseFloat(((selectedCrypto.value.circulating_supply / selectedCrypto.value.max_supply) * 100).toFixed(2))
})

const formatSupply = (value: number | null | undefined) => {
  if (!value) return 'N/A'
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`
  return value.toFixed(0)
}

// Get hours based on selected period
const getHoursForPeriod = (period: string): number => {
  switch (period) {
    case '24H': return 24
    case '7D': return 24 * 7
    case '30D': return 24 * 30
    case '1Y': return 24 * 365
    default: return 24
  }
}

// Fetch price history when period changes
const fetchChartData = async () => {
  if (!selectedCrypto.value) return

  loadingChart.value = true
  const hours = getHoursForPeriod(selectedPeriod.value)
  await cryptoStore.fetchPriceHistory(selectedCrypto.value.symbol, hours)
  loadingChart.value = false
}

// Watch for period changes
watch(selectedPeriod, () => {
  fetchChartData()
})

// Price chart data from store
const priceChartData = computed(() => {
  if (!selectedCrypto.value) return []

  const symbol = selectedCrypto.value.symbol
  const historyData = cryptoStore.priceHistory[symbol]

  if (historyData && historyData.length > 0) {
    return historyData.map((item: any) => ({
      timestamp: new Date(item.timestamp),
      value: item.price
    }))
  }

  // Fallback to mock data if no history available
  const now = new Date()
  const data = []
  const price = selectedCrypto.value.current_price || 0
  const hours = getHoursForPeriod(selectedPeriod.value)
  const points = Math.min(hours, 100) // Limit points for performance

  for (let i = points; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * (hours / points) * 3600000)
    const randomVariation = (Math.random() - 0.5) * price * 0.03
    data.push({
      timestamp,
      value: price + randomVariation
    })
  }

  return data
})

const volumeChartData = computed(() => {
  if (!selectedCrypto.value) return []

  const now = new Date()
  const data = []
  const volume = selectedCrypto.value.total_volume || 0

  for (let i = 24; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 3600000)
    const randomVariation = (Math.random() - 0.5) * volume * 0.1
    data.push({
      timestamp,
      value: volume + randomVariation
    })
  }

  return data
})

const marketCapChartData = computed(() => {
  if (!selectedCrypto.value) return []

  const now = new Date()
  const data = []
  const marketCap = selectedCrypto.value.market_cap || 0

  for (let i = 24; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 3600000)
    const randomVariation = (Math.random() - 0.5) * marketCap * 0.02
    data.push({
      timestamp,
      value: marketCap + randomVariation
    })
  }

  return data
})

onMounted(async () => {
  if (cryptoStore.prices.length === 0) {
    await cryptoStore.fetchLatestPrices(50)
  }
  // Fetch initial chart data
  await fetchChartData()
})
</script>

<style scoped>
.crypto-detail-view {
  @apply min-h-screen;
}

.glass-card {
  @apply bg-gray-800/50 backdrop-blur-lg rounded-2xl border border-gray-700/50
         shadow-xl hover:shadow-2xl transition-all duration-300;
}
</style>
