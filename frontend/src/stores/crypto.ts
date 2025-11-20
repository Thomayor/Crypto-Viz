import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/services/api'
import type { CryptoPrice } from '@/types'

export const useCryptoStore = defineStore('crypto', () => {
  const prices = ref<CryptoPrice[]>([])
  const priceHistory = ref<Record<string, CryptoPrice[]>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdate = ref<Date | null>(null)

  // Computed
  const topCoins = computed(() => prices.value.slice(0, 10))

  const gainers = computed(() =>
    [...prices.value]
      .filter(coin => coin.percent_change_24h > 0)
      .sort((a, b) => b.percent_change_24h - a.percent_change_24h)
      .slice(0, 5)
  )

  const losers = computed(() =>
    [...prices.value]
      .filter(coin => coin.percent_change_24h < 0)
      .sort((a, b) => a.percent_change_24h - b.percent_change_24h)
      .slice(0, 5)
  )

  const totalMarketCap = computed(() =>
    prices.value.reduce((sum, coin) => {
      const value = typeof coin.market_cap === 'number' ? coin.market_cap : parseFloat(coin.market_cap || '0')
      return sum + (isNaN(value) ? 0 : value)
    }, 0)
  )

  const totalVolume24h = computed(() =>
    prices.value.reduce((sum, coin) => {
      const value = typeof coin.volume_24h === 'number' ? coin.volume_24h : parseFloat(coin.volume_24h || '0')
      return sum + (isNaN(value) ? 0 : value)
    }, 0)
  )

  // Actions
  // Helper function to get crypto logo URL
  function getCryptoLogoUrl(symbol: string): string {
    const symbolUpper = symbol.toUpperCase()

    // CoinMarketCap logo URLs - mapping symbol to CMC ID
    const cmcIds: Record<string, number> = {
      'BTC': 1,
      'ETH': 1027,
      'USDT': 825,
      'BNB': 1839,
      'SOL': 5426,
      'USDC': 3408,
      'XRP': 52,
      'ADA': 2010,
      'AVAX': 5805,
      'DOGE': 74,
      'DOT': 6636,
      'MATIC': 3890,
      'LINK': 1975,
      'UNI': 7083,
      'ATOM': 3794,
      'LTC': 2,
      'ETC': 1321,
      'BCH': 1831,
      'XLM': 512,
      'ALGO': 4030,
      'VET': 3077,
      'FIL': 2280,
      'TRX': 1958,
      'ICP': 8916,
      'HBAR': 4642,
      'APT': 21794,
      'NEAR': 6535,
      'ARB': 11841,
      'OP': 11840,
    }

    const cmcId = cmcIds[symbolUpper]

    // Use CoinMarketCap CDN for logos
    if (cmcId) {
      return `https://s2.coinmarketcap.com/static/img/coins/64x64/${cmcId}.png`
    }

    // Fallback - return empty to show gradient placeholder
    return ''
  }

  async function fetchLatestPrices(limit: number = 50) {
    loading.value = true
    error.value = null

    try {
      const data = await api.getLatestPrices(limit)
      // Map API data to include aliases for backward compatibility
      prices.value = data.map(coin => ({
        ...coin,
        current_price: coin.price,
        total_volume: coin.volume_24h,
        price_change_percentage_24h: coin.percent_change_24h,
        market_cap_rank: coin.rank,
        image: getCryptoLogoUrl(coin.symbol),
        // Additional fields for detail page
        high_24h: coin.price * 1.05, // Mock data
        low_24h: coin.price * 0.95,
        ath: coin.price * 1.5,
        atl: coin.price * 0.1,
        circulating_supply: coin.market_cap / coin.price,
        total_supply: coin.market_cap / coin.price * 1.2,
        max_supply: coin.market_cap / coin.price * 1.5,
        price_change_percentage_1h_in_currency: coin.percent_change_1h,
        price_change_percentage_7d_in_currency: coin.percent_change_7d,
        price_change_percentage_30d_in_currency: coin.percent_change_24h * 3, // Mock
        price_change_percentage_1y_in_currency: coin.percent_change_24h * 30, // Mock
      }))
      lastUpdate.value = new Date()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch prices'
      console.error('Failed to fetch latest prices:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchPriceHistory(symbol: string, hours: number = 24) {
    try {
      const response = await api.getPriceHistory(symbol, hours)
      priceHistory.value[symbol] = response.prices
    } catch (e) {
      console.error(`Failed to fetch price history for ${symbol}:`, e)
    }
  }

  function getCoinBySymbol(symbol: string) {
    return prices.value.find(coin => coin.symbol === symbol)
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    prices,
    priceHistory,
    loading,
    error,
    lastUpdate,

    // Computed
    topCoins,
    gainers,
    losers,
    totalMarketCap,
    totalVolume24h,

    // Actions
    fetchLatestPrices,
    fetchPriceHistory,
    getCoinBySymbol,
    clearError,
  }
})
