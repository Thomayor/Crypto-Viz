<template>
  <div class="data-table-wrapper">
    <div class="table-header mb-4 flex items-center justify-between">
      <div>
        <h3 v-if="title" class="text-lg font-bold text-white">{{ title }}</h3>
        <p v-if="subtitle" class="text-sm text-gray-400 mt-1">{{ subtitle }}</p>
      </div>

      <div v-if="searchable" class="search-box">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search..."
          class="search-input"
        />
      </div>
    </div>

    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              :class="['table-header-cell', column.align === 'right' ? 'text-right' : 'text-left']"
              @click="column.sortable && handleSort(column.key)"
            >
              <div class="flex items-center gap-2" :class="column.align === 'right' ? 'justify-end' : 'justify-start'">
                <span>{{ column.label }}</span>
                <component
                  v-if="column.sortable && sortKey === column.key"
                  :is="sortDirection === 'asc' ? ChevronUpIcon : ChevronDownIcon"
                  class="h-4 w-4 text-cyan-400"
                />
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, index) in paginatedData"
            :key="index"
            class="table-row"
          >
            <td
              v-for="column in columns"
              :key="column.key"
              :class="['table-cell', column.align === 'right' ? 'text-right' : 'text-left']"
            >
              <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
                {{ formatCell(row[column.key], column) }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredData.length === 0" class="empty-state">
        <p class="text-gray-400">No data available</p>
      </div>
    </div>

    <div v-if="paginated && totalPages > 1" class="pagination">
      <button
        @click="currentPage--"
        :disabled="currentPage === 1"
        class="pagination-btn"
      >
        Previous
      </button>

      <div class="pagination-info">
        Page {{ currentPage }} of {{ totalPages }}
      </div>

      <button
        @click="currentPage++"
        :disabled="currentPage === totalPages"
        class="pagination-btn"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'

interface Column {
  key: string
  label: string
  sortable?: boolean
  align?: 'left' | 'right'
  format?: 'currency' | 'percentage' | 'number' | 'date'
}

interface Props {
  columns: Column[]
  data: any[]
  title?: string
  subtitle?: string
  searchable?: boolean
  paginated?: boolean
  itemsPerPage?: number
}

const props = withDefaults(defineProps<Props>(), {
  searchable: true,
  paginated: true,
  itemsPerPage: 10
})

const searchQuery = ref('')
const sortKey = ref<string>('')
const sortDirection = ref<'asc' | 'desc'>('asc')
const currentPage = ref(1)

const filteredData = computed(() => {
  let data = [...props.data]

  // Search filtering
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    data = data.filter(row =>
      Object.values(row).some(value =>
        String(value).toLowerCase().includes(query)
      )
    )
  }

  // Sorting
  if (sortKey.value) {
    data.sort((a, b) => {
      const aVal = a[sortKey.value]
      const bVal = b[sortKey.value]

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection.value === 'asc' ? aVal - bVal : bVal - aVal
      }

      const aStr = String(aVal).toLowerCase()
      const bStr = String(bVal).toLowerCase()

      if (sortDirection.value === 'asc') {
        return aStr.localeCompare(bStr)
      } else {
        return bStr.localeCompare(aStr)
      }
    })
  }

  return data
})

const paginatedData = computed(() => {
  if (!props.paginated) return filteredData.value

  const start = (currentPage.value - 1) * props.itemsPerPage
  const end = start + props.itemsPerPage
  return filteredData.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredData.value.length / props.itemsPerPage)
})

const handleSort = (key: string) => {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDirection.value = 'asc'
  }
}

const formatCell = (value: any, column: Column) => {
  if (value === null || value === undefined) return '-'

  switch (column.format) {
    case 'currency':
      return '$' + Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    case 'percentage':
      return Number(value).toFixed(2) + '%'
    case 'number':
      return Number(value).toLocaleString('en-US')
    case 'date':
      return new Date(value).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    default:
      return value
  }
}
</script>

<style scoped>
.data-table-wrapper {
  @apply bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6;
}

.search-box {
  @apply relative;
}

.search-input {
  @apply bg-gray-700/50 border border-gray-600 rounded-lg px-4 py-2 text-sm text-white
         placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500
         transition-all duration-200;
}

.table-container {
  @apply overflow-x-auto rounded-lg;
}

.data-table {
  @apply w-full;
}

.table-header-cell {
  @apply px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider
         border-b border-gray-700/50 cursor-pointer hover:text-cyan-400 transition-colors;
}

.table-row {
  @apply border-b border-gray-700/30 hover:bg-gray-700/20 transition-colors;
}

.table-cell {
  @apply px-4 py-4 text-sm text-gray-300;
}

.empty-state {
  @apply py-12 text-center;
}

.pagination {
  @apply mt-6 flex items-center justify-between;
}

.pagination-btn {
  @apply px-4 py-2 bg-gray-700/50 text-white text-sm font-medium rounded-lg
         hover:bg-gray-600/50 disabled:opacity-50 disabled:cursor-not-allowed
         transition-all duration-200;
}

.pagination-info {
  @apply text-sm text-gray-400;
}
</style>
