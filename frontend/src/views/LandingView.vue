<template>
  <div class="landing-page">
    <!-- Hero Section with Animated Background -->
    <section class="hero-section relative overflow-hidden bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 min-h-screen flex items-center">
      <!-- Animated Background -->
      <div class="absolute inset-0 overflow-hidden">
        <div class="crypto-grid">
          <div v-for="i in 50" :key="i" class="crypto-particle" :style="getParticleStyle(i)"></div>
        </div>
      </div>

      <!-- Hero Content -->
      <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div class="animate-fade-in-up">
          <h1 class="text-6xl md:text-8xl font-black text-white mb-6 tracking-tight">
            <span class="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 animate-gradient">
              CRYPTO VIZ
            </span>
          </h1>
          <p class="text-xl md:text-3xl text-gray-200 mb-4 font-light">
            Real-Time Cryptocurrency Analytics
          </p>
          <p class="text-lg md:text-xl text-blue-200 mb-12 max-w-3xl mx-auto">
            Powered by <span class="font-semibold text-cyan-300">pandas</span>,
            <span class="font-semibold text-purple-300">DuckDB</span> &
            <span class="font-semibold text-pink-300">Apache Spark</span>
          </p>

          <!-- CTA Buttons -->
          <div class="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <button
              @click="goToDashboard"
              class="group relative px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full text-white font-bold text-lg shadow-2xl hover:shadow-cyan-500/50 transform hover:scale-105 transition-all duration-300"
            >
              <span class="relative z-10 flex items-center gap-2">
                <RocketLaunchIcon class="h-6 w-6" />
                Launch Dashboard
              </span>
              <div class="absolute inset-0 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 blur-lg opacity-50 group-hover:opacity-75 transition-opacity"></div>
            </button>

            <button
              @click="scrollToFeatures"
              class="px-8 py-4 bg-white/10 backdrop-blur-lg border-2 border-white/20 rounded-full text-white font-bold text-lg hover:bg-white/20 transform hover:scale-105 transition-all duration-300"
            >
              Explore Features
            </button>
          </div>

          <!-- Stats Counter -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            <div class="stat-card">
              <div class="text-4xl font-black text-cyan-400 mb-2">50+</div>
              <div class="text-sm text-gray-300">Cryptocurrencies</div>
            </div>
            <div class="stat-card">
              <div class="text-4xl font-black text-purple-400 mb-2">24/7</div>
              <div class="text-sm text-gray-300">Real-Time Data</div>
            </div>
            <div class="stat-card">
              <div class="text-4xl font-black text-pink-400 mb-2">AI</div>
              <div class="text-sm text-gray-300">Sentiment Analysis</div>
            </div>
            <div class="stat-card">
              <div class="text-4xl font-black text-blue-400 mb-2">ML</div>
              <div class="text-sm text-gray-300">Price Predictions</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Scroll Indicator -->
      <div class="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
        <ChevronDownIcon class="h-8 w-8 text-white/50" />
      </div>
    </section>

    <!-- Features Section -->
    <section ref="featuresSection" class="py-24 bg-gray-900">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-5xl font-black text-white mb-4">
            Powerful <span class="text-cyan-400">Features</span>
          </h2>
          <p class="text-xl text-gray-400">Everything you need to analyze the crypto market</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <!-- Feature 1 -->
          <div class="feature-card group">
            <div class="feature-icon bg-gradient-to-br from-cyan-500 to-blue-600">
              <ChartBarIcon class="h-8 w-8 text-white" />
            </div>
            <h3 class="text-2xl font-bold text-white mb-3">Real-Time Dashboard</h3>
            <p class="text-gray-400 mb-4">
              Live price tracking with beautiful charts and visualizations. Monitor market trends in real-time.
            </p>
            <ul class="space-y-2 text-sm text-gray-500">
              <li class="flex items-center gap-2">
                <CheckCircleIcon class="h-5 w-5 text-cyan-400" />
                <span>Live price updates every 30s</span>
              </li>
              <li class="flex items-center gap-2">
                <CheckCircleIcon class="h-5 w-5 text-cyan-400" />
                <span>Top gainers & losers</span>
              </li>
              <li class="flex items-center gap-2">
                <CheckCircleIcon class="h-5 w-5 text-cyan-400" />
                <span>Market cap tracking</span>
              </li>
            </ul>
          </div>

          <!-- Feature 2 -->
          <div class="feature-card group">
            <div class="feature-icon bg-gradient-to-br from-purple-500 to-pink-600">
              <CpuChipIcon class="h-8 w-8 text-white" />
            </div>
            <h3 class="text-2xl font-bold text-white mb-3">ML Predictions</h3>
            <p class="text-gray-400 mb-4">
              Advanced machine learning models predict price movements and detect anomalies automatically.
            </p>
            <ul class="space-y-2 text-sm text-gray-500">
              <li class="flex items-center gap-2">
                <CheckCircleIcon class="h-5 w-5 text-purple-400" />
                <span>Linear Regression forecasts</span>
              </li>
              <li class="flex items-center gap-2">
                <CheckCircleIcon class="h-5 w-5 text-purple-400" />
                <span>Anomaly detection</span>
              </li>
              <li class="flex items-center gap-2">
                <CheckCircleIcon class="h-5 w-5 text-purple-400" />
                <span>Confidence scoring</span>
              </li>
            </ul>
          </div>

          <!-- Feature 3 -->
          <div class="feature-card group">
            <div class="feature-icon bg-gradient-to-br from-pink-500 to-rose-600">
              <NewspaperIcon class="h-8 w-8 text-white" />
            </div>
            <h3 class="text-2xl font-bold text-white mb-3">AI Sentiment Analysis</h3>
            <p class="text-gray-400 mb-4">
              Analyze news and social media sentiment with AI-powered natural language processing.
            </p>
            <ul class="space-y-2 text-sm text-gray-500">
              <li class="flex items-center gap-2">
                <CheckCircleIcon class="h-5 w-5 text-pink-400" />
                <span>News sentiment scoring</span>
              </li>
              <li class="flex items-center gap-2">
                <CheckCircleIcon class="h-5 w-5 text-pink-400" />
                <span>Reddit & Twitter tracking</span>
              </li>
              <li class="flex items-center gap-2">
                <CheckCircleIcon class="h-5 w-5 text-pink-400" />
                <span>Trend identification</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- Tech Stack Section -->
    <section class="py-24 bg-gradient-to-b from-gray-900 to-gray-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-5xl font-black text-white mb-4">
            Built with <span class="text-cyan-400">Modern Tech</span>
          </h2>
          <p class="text-xl text-gray-400">Industry-leading data engineering tools</p>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-8">
          <div class="tech-card">
            <div class="tech-icon">🐼</div>
            <div class="text-white font-semibold">pandas</div>
          </div>
          <div class="tech-card">
            <div class="tech-icon">🦆</div>
            <div class="text-white font-semibold">DuckDB</div>
          </div>
          <div class="tech-card">
            <div class="tech-icon">⚡</div>
            <div class="text-white font-semibold">Spark</div>
          </div>
          <div class="tech-card">
            <div class="tech-icon">🔥</div>
            <div class="text-white font-semibold">FastAPI</div>
          </div>
          <div class="tech-card">
            <div class="tech-icon">💚</div>
            <div class="text-white font-semibold">Vue 3</div>
          </div>
          <div class="tech-card">
            <div class="tech-icon">🎨</div>
            <div class="text-white font-semibold">Tailwind</div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="py-24 bg-gradient-to-r from-cyan-600 via-blue-600 to-purple-600 relative overflow-hidden">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')]"></div>
      </div>

      <div class="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-5xl md:text-6xl font-black text-white mb-6">
          Ready to Dive In?
        </h2>
        <p class="text-xl text-white/90 mb-10">
          Start analyzing cryptocurrency markets with cutting-edge AI and ML technology
        </p>
        <button
          @click="goToDashboard"
          class="group relative px-12 py-5 bg-white rounded-full text-blue-600 font-bold text-xl shadow-2xl hover:shadow-white/50 transform hover:scale-110 transition-all duration-300"
        >
          <span class="relative z-10 flex items-center gap-3">
            <SparklesIcon class="h-7 w-7" />
            Get Started Now
            <ArrowRightIcon class="h-6 w-6 group-hover:translate-x-2 transition-transform" />
          </span>
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-950 py-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div class="text-gray-400 mb-4">
          <span class="font-bold text-white">CRYPTO VIZ</span> - Real-time cryptocurrency analytics platform
        </div>
        <div class="text-sm text-gray-600">
          Built for EPITECH MSc Pro Project • Powered by Bootstrap Stack (pandas, DuckDB, Spark)
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  RocketLaunchIcon,
  ChartBarIcon,
  CpuChipIcon,
  NewspaperIcon,
  CheckCircleIcon,
  SparklesIcon,
  ArrowRightIcon,
  ChevronDownIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const featuresSection = ref<HTMLElement | null>(null)

const goToDashboard = () => {
  router.push('/dashboard')
}

const scrollToFeatures = () => {
  featuresSection.value?.scrollIntoView({ behavior: 'smooth' })
}

const getParticleStyle = (index: number) => {
  const delay = Math.random() * 5
  const duration = 10 + Math.random() * 20
  const x = Math.random() * 100
  const y = Math.random() * 100

  return {
    left: `${x}%`,
    top: `${y}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
  }
}
</script>

<style scoped>
@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  33% { transform: translateY(-20px) rotate(5deg); }
  66% { transform: translateY(-10px) rotate(-5deg); }
}

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-gradient {
  background-size: 200% 200%;
  animation: gradient-shift 3s ease infinite;
}

.animate-fade-in-up {
  animation: fade-in-up 1s ease-out;
}

.crypto-particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 50%;
  animation: float linear infinite;
}

.stat-card {
  @apply bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10 transform hover:scale-105 transition-all duration-300 hover:bg-white/10;
}

.feature-card {
  @apply bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 border border-gray-700/50 transform hover:scale-105 transition-all duration-300 hover:border-cyan-500/50 hover:shadow-2xl hover:shadow-cyan-500/20;
}

.feature-icon {
  @apply w-16 h-16 rounded-2xl flex items-center justify-center mb-6 transform group-hover:scale-110 group-hover:rotate-6 transition-all duration-300 shadow-lg;
}

.tech-card {
  @apply bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700/50 flex flex-col items-center gap-3 transform hover:scale-110 transition-all duration-300 hover:border-cyan-500/50;
}

.tech-icon {
  @apply text-4xl;
}
</style>
