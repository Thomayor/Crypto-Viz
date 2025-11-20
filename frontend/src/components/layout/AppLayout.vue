<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
    <!-- Navigation -->
    <nav class="bg-gray-900/80 backdrop-blur-xl shadow-lg border-b border-gray-700/50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Logo and Brand -->
          <div class="flex items-center gap-3">
            <div class="h-10 w-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg">
              <ChartBarIcon class="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 class="text-xl font-bold text-white">CRYPTO VIZ</h1>
              <p class="text-xs text-cyan-400">Real-time Analytics</p>
            </div>
          </div>

          <!-- Desktop Navigation -->
          <div class="hidden md:flex items-center gap-1">
            <router-link
              v-for="item in navigation"
              :key="item.name"
              :to="item.path"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300',
                isActive(item.path)
                  ? 'bg-cyan-500/20 text-cyan-400 shadow-lg shadow-cyan-500/20'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white',
              ]"
            >
              <component :is="item.icon" class="h-5 w-5" />
              <span>{{ item.name }}</span>
            </router-link>
          </div>

          <!-- Mobile Menu Button -->
          <div class="md:hidden">
            <button
              @click="mobileMenuOpen = !mobileMenuOpen"
              class="p-2 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white"
            >
              <Bars3Icon v-if="!mobileMenuOpen" class="h-6 w-6" />
              <XMarkIcon v-else class="h-6 w-6" />
            </button>
          </div>

          <!-- WebSocket Status -->
          <div class="hidden lg:flex">
            <ConnectionStatus
              :is-connected="realtime.isConnected.value"
              :is-connecting="realtime.isConnecting.value"
              :connection-status="realtime.connectionStatus.value"
              :reconnect-attempts="realtime.reconnectAttempts.value"
            />
          </div>
        </div>
      </div>

      <!-- Mobile Navigation -->
      <div v-if="mobileMenuOpen" class="md:hidden border-t border-gray-200 bg-white">
        <div class="px-2 pt-2 pb-3 space-y-1">
          <router-link
            v-for="item in navigation"
            :key="item.name"
            :to="item.path"
            @click="mobileMenuOpen = false"
            :class="[
              'flex items-center gap-2 px-3 py-2 rounded-lg text-base font-medium transition-colors',
              isActive(item.path)
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
            ]"
          >
            <component :is="item.icon" class="h-5 w-5" />
            <span>{{ item.name }}</span>
          </router-link>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 mt-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex flex-col md:flex-row items-center justify-between gap-4">
          <div class="text-sm text-gray-600">
            <span class="font-semibold">CRYPTO VIZ</span> - Real-time cryptocurrency data analytics
            powered by pandas, DuckDB & Apache Spark
          </div>
          <div class="flex items-center gap-4 text-sm text-gray-500">
            <span>EPITECH MSc Pro Project</span>
            <span>•</span>
            <a
              href="https://github.com/EpitechMscProPromo2026"
              target="_blank"
              rel="noopener noreferrer"
              class="hover:text-primary-600 transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChartBarIcon,
  HomeIcon,
  ChartPieIcon,
  NewspaperIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { useRealTimeData } from '@/composables/useRealTimeData'
import ConnectionStatus from '@/components/ui/ConnectionStatus.vue'

const route = useRoute()
const mobileMenuOpen = ref(false)
const realtime = useRealTimeData()

const navigation = [
  {
    name: 'Home',
    path: '/',
    icon: HomeIcon,
  },
  {
    name: 'Dashboard',
    path: '/dashboard',
    icon: ChartBarIcon,
  },
  {
    name: 'Analytics',
    path: '/analytics',
    icon: ChartPieIcon,
  },
  {
    name: 'News & Social',
    path: '/news',
    icon: NewspaperIcon,
  },
]

const isActive = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
