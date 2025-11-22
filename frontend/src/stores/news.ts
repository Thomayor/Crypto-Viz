import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/services/api'
import type { News, SocialPost } from '@/types'

export const useNewsStore = defineStore('news', () => {
  const news = ref<News[]>([])
  const socialPosts = ref<SocialPost[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdate = ref<Date | null>(null)

  // Computed
  const positiveNews = computed(() =>
    news.value.filter(n => n.sentiment_label?.toUpperCase() === 'POSITIVE')
  )

  const negativeNews = computed(() =>
    news.value.filter(n => n.sentiment_label?.toUpperCase() === 'NEGATIVE')
  )

  const neutralNews = computed(() =>
    news.value.filter(n => n.sentiment_label?.toUpperCase() === 'NEUTRAL')
  )

  const averageSentiment = computed(() => {
    if (news.value.length === 0) return 0
    const total = news.value.reduce((sum, n) => sum + n.sentiment_score, 0)
    return total / news.value.length
  })

  const topMentionedCoins = computed(() => {
    const coinCounts: Record<string, number> = {}

    news.value.forEach(n => {
      n.mentioned_coins.forEach(coin => {
        coinCounts[coin] = (coinCounts[coin] || 0) + 1
      })
    })

    return Object.entries(coinCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([coin, count]) => ({ coin, count }))
  })

  const redditPosts = computed(() =>
    socialPosts.value.filter(p => p.platform === 'reddit')
  )

  const twitterPosts = computed(() =>
    socialPosts.value.filter(p => p.platform === 'twitter')
  )

  // Actions
  async function fetchLatestNews(limit: number = 20, hours: number = 24) {
    loading.value = true
    error.value = null

    try {
      const response = await api.getLatestNews(limit, hours)
      news.value = response.news
      lastUpdate.value = new Date()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch news'
      console.error('Failed to fetch latest news:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchLatestSocial(
    platform: 'reddit' | 'twitter' | 'all' = 'all',
    limit: number = 20,
    hours: number = 24
  ) {
    try {
      const response = await api.getLatestSocial(platform, limit, hours)
      socialPosts.value = response.posts
    } catch (e) {
      console.error('Failed to fetch social posts:', e)
    }
  }

  // Alias for compatibility
  async function fetchSocialPosts(limit: number = 20, hours: number = 24) {
    return fetchLatestSocial('all', limit, hours)
  }

  function getNewsByCoin(symbol: string) {
    return news.value.filter(n => n.mentioned_coins.includes(symbol))
  }

  function getSocialByCoin(symbol: string) {
    return socialPosts.value.filter(p => p.mentioned_coins.includes(symbol))
  }

  function getSocialPostsByPlatform(platform: string) {
    if (platform === 'all') return socialPosts.value
    return socialPosts.value.filter(p => p.platform === platform)
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    news,
    socialPosts,
    loading,
    error,
    lastUpdate,

    // Computed
    positiveNews,
    negativeNews,
    neutralNews,
    averageSentiment,
    topMentionedCoins,
    redditPosts,
    twitterPosts,

    // Actions
    fetchLatestNews,
    fetchLatestSocial,
    fetchSocialPosts,
    getNewsByCoin,
    getSocialByCoin,
    getSocialPostsByPlatform,
    clearError,
  }
})
