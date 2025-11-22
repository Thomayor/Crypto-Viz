<template>
  <div class="news-view">
    <!-- Header -->
    <div class="header-section mb-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-cyan-500 to-teal-500 mb-2">
            News & Social Media
          </h1>
          <p class="text-gray-400 flex items-center gap-2">
            <NewspaperIcon class="h-5 w-5 text-cyan-400" />
            AI-powered sentiment analysis from news and social platforms
          </p>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="newsStore.loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" />
    </div>

    <div v-else>
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
        <StatsCard
          label="Total Articles"
          :value="(newsStore.news?.length || 0).toString()"
          :change="15.2"
          :icon="NewspaperIcon"
          icon-color="cyan"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">Last 24h</span>
              <span class="text-cyan-400 font-semibold">{{ newsStore.news?.filter(n => isRecent(n.published_at)).length || 0 }} new</span>
            </div>
          </template>
        </StatsCard>

        <StatsCard
          label="Positive Sentiment"
          :value="positiveCount.toString()"
          :change="8.5"
          :icon="FaceSmileIcon"
          icon-color="green"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">Percentage</span>
              <span class="text-green-400 font-semibold">{{ newsStore.news?.length ? ((positiveCount / newsStore.news.length) * 100).toFixed(0) : 0 }}%</span>
            </div>
          </template>
        </StatsCard>

        <StatsCard
          label="Neutral Sentiment"
          :value="neutralCount.toString()"
          :change="-2.3"
          :icon="MinusCircleIcon"
          icon-color="yellow"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">Percentage</span>
              <span class="text-yellow-400 font-semibold">{{ newsStore.news?.length ? ((neutralCount / newsStore.news.length) * 100).toFixed(0) : 0 }}%</span>
            </div>
          </template>
        </StatsCard>

        <StatsCard
          label="Negative Sentiment"
          :value="negativeCount.toString()"
          :change="-12.8"
          :icon="FaceFrownIcon"
          icon-color="red"
        >
          <template #footer>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">Percentage</span>
              <span class="text-red-400 font-semibold">{{ newsStore.news?.length ? ((negativeCount / newsStore.news.length) * 100).toFixed(0) : 0 }}%</span>
            </div>
          </template>
        </StatsCard>
      </div>

      <!-- Filters and Overview -->
      <div class="glass-card p-6 mb-8">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Sentiment Filter -->
          <div>
            <h3 class="text-sm font-semibold text-gray-400 uppercase mb-3">Filter by Sentiment</h3>
            <select
              v-model="selectedSentiment"
              class="select-input w-full"
            >
              <option value="all">All Sentiments</option>
              <option value="positive">Positive</option>
              <option value="neutral">Neutral</option>
              <option value="negative">Negative</option>
            </select>
          </div>

          <!-- Top Mentioned Coins -->
          <div>
            <h3 class="text-sm font-semibold text-gray-400 uppercase mb-3">Top Mentioned</h3>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="coin in topMentionedCoins.slice(0, 5)"
                :key="coin.coin"
                class="px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-full text-xs font-semibold border border-cyan-500/30"
              >
                {{ coin.coin }} ({{ coin.count }})
              </span>
            </div>
          </div>

          <!-- Average Sentiment -->
          <div>
            <h3 class="text-sm font-semibold text-gray-400 uppercase mb-3">Average Sentiment</h3>
            <div class="flex items-center gap-3">
              <div class="flex-1 bg-gray-700 rounded-full h-3 overflow-hidden">
                <div
                  :class="getSentimentBarClass(averageSentiment)"
                  :style="{ width: `${averageSentiment * 100}%` }"
                  class="h-full transition-all duration-500"
                ></div>
              </div>
              <span class="text-lg font-bold text-white min-w-[4rem]">
                {{ (averageSentiment * 100).toFixed(0) }}%
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- News Articles Grid -->
      <div class="mb-8">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold text-white">Latest News Articles</h2>
          <div class="text-sm text-gray-400">
            Showing {{ filteredNews.length }} of {{ newsStore.news?.length || 0 }} articles
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          <div
            v-for="(article, index) in filteredNews.slice(0, 12)"
            :key="article.id"
            class="news-card"
            :style="{ animationDelay: `${index * 0.05}s` }"
          >
            <div class="flex items-start justify-between mb-3">
              <div :class="['sentiment-badge', getSentimentBadgeClass(article.sentiment_label)]">
                {{ article.sentiment_label }}
              </div>
              <div class="text-xs text-gray-500">
                {{ formatDate(article.published_at) }}
              </div>
            </div>

            <h3 class="text-lg font-bold text-white mb-2 line-clamp-2 hover:text-cyan-400 transition-colors">
              {{ article.title }}
            </h3>

            <p class="text-sm text-gray-400 mb-4 line-clamp-3">
              {{ article.description || 'No description available' }}
            </p>

            <div class="flex items-center justify-between pt-4 border-t border-gray-700/50">
              <div class="flex items-center gap-2">
                <div class="w-6 h-6 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
                  <span class="text-white text-xs font-bold">{{ article.source?.substring(0, 1).toUpperCase() }}</span>
                </div>
                <span class="text-xs text-gray-500">{{ article.source }}</span>
              </div>

              <a
                v-if="article.url"
                :href="article.url"
                target="_blank"
                rel="noopener noreferrer"
                class="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
              >
                Read more
                <ArrowTopRightOnSquareIcon class="h-3 w-3" />
              </a>
            </div>
          </div>

          <div v-if="filteredNews.length === 0" class="col-span-full text-center py-12 text-gray-400">
            No news articles found for the selected sentiment
          </div>
        </div>
      </div>

      <!-- Social Media Posts -->
      <div class="glass-card p-6">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-2xl font-bold text-white mb-1">Social Media Posts</h2>
            <p class="text-sm text-gray-400">Trending discussions from Reddit and Twitter</p>
          </div>

          <div class="flex gap-2">
            <button
              @click="selectedPlatform = 'all'"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                selectedPlatform === 'all'
                  ? 'bg-cyan-500 text-white'
                  : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
              ]"
            >
              All
            </button>
            <button
              @click="selectedPlatform = 'reddit'"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2',
                selectedPlatform === 'reddit'
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
              ]"
            >
              <ChatBubbleLeftIcon class="h-4 w-4" />
              Reddit
            </button>
            <button
              @click="selectedPlatform = 'twitter'"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2',
                selectedPlatform === 'twitter'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
              ]"
            >
              <AtSymbolIcon class="h-4 w-4" />
              Twitter
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div
            v-for="(post, index) in filteredSocialPosts.slice(0, 10)"
            :key="post.id"
            class="social-post-card"
            :style="{ animationDelay: `${index * 0.05}s` }"
          >
            <div class="flex items-start gap-3">
              <div :class="['platform-badge', post.platform === 'reddit' ? 'platform-reddit' : 'platform-twitter']">
                <component :is="post.platform === 'reddit' ? ChatBubbleLeftIcon : AtSymbolIcon" class="h-4 w-4" />
              </div>

              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-2">
                  <span class="font-semibold text-white">{{ post.author }}</span>
                  <div :class="['sentiment-dot', getSentimentDotClass(post.sentiment)]"></div>
                </div>

                <p class="text-sm text-gray-300 mb-3 line-clamp-3">{{ post.content }}</p>

                <div class="flex items-center gap-4 text-xs text-gray-500">
                  <div class="flex items-center gap-1">
                    <HeartIcon class="h-4 w-4" />
                    {{ post.engagement_score || 0 }}
                  </div>
                  <div>{{ formatDate(post.created_at) }}</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="filteredSocialPosts.length === 0" class="col-span-full text-center py-12 text-gray-400">
            No social media posts found for the selected platform
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useNewsStore } from '@/stores/news'
import { useFormatting } from '@/composables/useFormatting'
import { usePolling } from '@/composables/usePolling'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import StatsCard from '@/components/ui/StatsCard.vue'
import {
  NewspaperIcon,
  FaceSmileIcon,
  FaceFrownIcon,
  MinusCircleIcon,
  ArrowTopRightOnSquareIcon,
  ChatBubbleLeftIcon,
  AtSymbolIcon,
  HeartIcon,
} from '@heroicons/vue/24/outline'

const newsStore = useNewsStore()
const { formatDate } = useFormatting()

const selectedSentiment = ref('all')
const selectedPlatform = ref('all')

// Polling
usePolling(async () => {
  await Promise.all([
    newsStore.fetchLatestNews(100),
    newsStore.fetchSocialPosts()
  ])
}, 300000) // 5 minutes

// Computed properties
const positiveCount = computed(() =>
  newsStore.news?.filter(n => n.sentiment_label?.toUpperCase() === 'POSITIVE').length || 0
)

const neutralCount = computed(() =>
  newsStore.news?.filter(n => n.sentiment_label?.toUpperCase() === 'NEUTRAL').length || 0
)

const negativeCount = computed(() =>
  newsStore.news?.filter(n => n.sentiment_label?.toUpperCase() === 'NEGATIVE').length || 0
)

const averageSentiment = computed(() => {
  if (!newsStore.news || newsStore.news.length === 0) return 0.5
  const sentimentValues = newsStore.news.map(n => {
    const label = n.sentiment_label?.toUpperCase()
    if (label === 'POSITIVE') return 1
    if (label === 'NEUTRAL') return 0.5
    return 0
  })
  const sum = sentimentValues.reduce((acc, val) => acc + val, 0)
  return sum / sentimentValues.length
})

const topMentionedCoins = computed(() => {
  return newsStore.topMentionedCoins.slice(0, 5)
})

const filteredNews = computed(() => {
  if (!newsStore.news) return []
  if (selectedSentiment.value === 'all') {
    return newsStore.news
  }
  return newsStore.news.filter(n => n.sentiment_label?.toUpperCase() === selectedSentiment.value.toUpperCase())
})

const filteredSocialPosts = computed(() => {
  if (!newsStore.socialPosts) return []
  if (selectedPlatform.value === 'all') {
    return newsStore.socialPosts
  }
  return newsStore.getSocialPostsByPlatform(selectedPlatform.value)
})

// Helper functions
const isRecent = (date: string | Date) => {
  const now = new Date()
  const articleDate = new Date(date)
  const diffHours = (now.getTime() - articleDate.getTime()) / (1000 * 60 * 60)
  return diffHours <= 24
}

const getSentimentBadgeClass = (sentiment: string) => {
  const label = sentiment?.toUpperCase()
  const classes = {
    POSITIVE: 'sentiment-positive',
    NEUTRAL: 'sentiment-neutral',
    NEGATIVE: 'sentiment-negative'
  }
  return classes[label as keyof typeof classes] || 'sentiment-neutral'
}

const getSentimentDotClass = (sentiment: string) => {
  const label = sentiment?.toUpperCase()
  const classes = {
    POSITIVE: 'bg-green-500',
    NEUTRAL: 'bg-gray-500',
    NEGATIVE: 'bg-red-500'
  }
  return classes[label as keyof typeof classes] || 'bg-gray-500'
}

const getSentimentBarClass = (score: number) => {
  if (score >= 0.66) return 'bg-gradient-to-r from-green-500 to-emerald-500'
  if (score <= 0.33) return 'bg-gradient-to-r from-red-500 to-rose-500'
  return 'bg-gradient-to-r from-gray-500 to-slate-500'
}

// Initial fetch
onMounted(async () => {
  await Promise.all([
    newsStore.fetchLatestNews(100),
    newsStore.fetchSocialPosts()
  ])
})
</script>

<style scoped>
.news-view {
  @apply min-h-screen;
}

.header-section {
  @apply animate-fade-in;
}

.glass-card {
  @apply bg-gray-800/50 backdrop-blur-lg rounded-2xl border border-gray-700/50
         shadow-xl hover:shadow-2xl transition-all duration-300 hover:border-cyan-500/30;
}

.select-input {
  @apply bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2.5 text-white
         focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500
         transition-all duration-200 cursor-pointer hover:bg-gray-700;
}

.news-card {
  @apply bg-gray-700/30 backdrop-blur-sm rounded-xl p-5 border border-gray-600/30
         hover:border-cyan-500/30 transition-all duration-300
         transform hover:scale-[1.02] cursor-pointer
         animate-fade-in;
}

.social-post-card {
  @apply bg-gray-700/30 backdrop-blur-sm rounded-xl p-4 border border-gray-600/30
         hover:border-cyan-500/30 transition-all duration-300
         animate-fade-in;
}

.sentiment-badge {
  @apply px-3 py-1 rounded-full text-xs font-semibold uppercase;
}

.sentiment-positive {
  @apply bg-green-500/20 text-green-400 border border-green-500/30;
}

.sentiment-neutral {
  @apply bg-gray-500/20 text-gray-400 border border-gray-500/30;
}

.sentiment-negative {
  @apply bg-red-500/20 text-red-400 border border-red-500/30;
}

.sentiment-dot {
  @apply w-2 h-2 rounded-full;
}

.platform-badge {
  @apply w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0;
}

.platform-reddit {
  @apply bg-orange-500/20 text-orange-400;
}

.platform-twitter {
  @apply bg-blue-500/20 text-blue-400;
}

.line-clamp-2 {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.line-clamp-3 {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.5s ease-out;
}
</style>
