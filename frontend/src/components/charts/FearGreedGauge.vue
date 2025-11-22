<template>
  <div class="fear-greed-gauge">
    <div class="gauge-container">
      <svg viewBox="0 0 400 240" class="gauge-svg">
        <!-- Background arc segments -->
        <path
          :d="getArcPath(0, 20)"
          fill="#DC2626"
          class="gauge-segment"
        />
        <path
          :d="getArcPath(20, 40)"
          fill="#F59E0B"
          class="gauge-segment"
        />
        <path
          :d="getArcPath(40, 60)"
          fill="#EAB308"
          class="gauge-segment"
        />
        <path
          :d="getArcPath(60, 80)"
          fill="#10B981"
          class="gauge-segment"
        />
        <path
          :d="getArcPath(80, 100)"
          fill="#059669"
          class="gauge-segment"
        />

        <!-- Center circle -->
        <circle cx="200" cy="200" r="120" fill="#1F2937" />

        <!-- Needle -->
        <g>
          <line
            :x1="200"
            :y1="200"
            :x2="needleEndX"
            :y2="needleEndY"
            stroke="#EF4444"
            stroke-width="4"
            stroke-linecap="round"
            class="needle"
          />
          <circle cx="200" cy="200" r="10" fill="#1F2937" stroke="#EF4444" stroke-width="3" />
        </g>

        <!-- Value display -->
        <text x="200" y="160" text-anchor="middle" class="gauge-value">
          {{ currentValue }}
        </text>
        <text x="200" y="230" text-anchor="middle" class="gauge-label">
          {{ currentLabel }}
        </text>
      </svg>

      <!-- Legend -->
      <div class="gauge-legend">
        <div class="legend-item">
          <span class="legend-color" style="background: #DC2626"></span>
          <span class="legend-text">Extreme Fear</span>
          <span class="legend-range">0-25</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #F59E0B"></span>
          <span class="legend-text">Fear</span>
          <span class="legend-range">25-45</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #EAB308"></span>
          <span class="legend-text">Neutral</span>
          <span class="legend-range">45-55</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #10B981"></span>
          <span class="legend-text">Greed</span>
          <span class="legend-range">55-75</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #059669"></span>
          <span class="legend-text">Extreme Greed</span>
          <span class="legend-range">75-100</span>
        </div>
      </div>
    </div>

    <!-- Additional info -->
    <div class="gauge-info">
      <div class="info-item">
        <span class="info-label">Data Points</span>
        <span class="info-value">{{ dataPoints }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">Ollama Analyzed</span>
        <span class="info-value">{{ ollamaAnalyzed }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">Confidence</span>
        <span class="info-value">{{ (avgConfidence * 100).toFixed(0) }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  value: number // 0-100
  dataPoints?: number
  ollamaAnalyzed?: number
  avgConfidence?: number
}

const props = withDefaults(defineProps<Props>(), {
  value: 50,
  dataPoints: 0,
  ollamaAnalyzed: 0,
  avgConfidence: 0
})

// Calculate needle angle (180° to 0°, where 180° is 0% and 0° is 100%)
const needleAngle = computed(() => {
  return 180 - (props.value * 1.8) // 1.8 = 180° / 100
})

// Calculate needle endpoint coordinates (CORRECTED for upper arc)
const needleEndX = computed(() => {
  const angleRad = (needleAngle.value * Math.PI) / 180
  const needleLength = 140 // Length of the needle
  return 200 + needleLength * Math.cos(angleRad)
})

const needleEndY = computed(() => {
  const angleRad = (needleAngle.value * Math.PI) / 180
  const needleLength = 140
  return 200 - needleLength * Math.sin(angleRad) // MINUS for upper arc
})

const currentValue = computed(() => {
  return Math.round(props.value)
})

const currentLabel = computed(() => {
  if (props.value <= 25) return 'Extreme Fear'
  if (props.value <= 45) return 'Fear'
  if (props.value <= 55) return 'Neutral'
  if (props.value <= 75) return 'Greed'
  return 'Extreme Greed'
})

// Helper function to create arc path
const getArcPath = (startPercent: number, endPercent: number) => {
  const radius = 160
  const centerX = 200
  const centerY = 200
  const innerRadius = 120

  // Convert percentage to angle: 0% = 180° (left), 100% = 0° (right)
  // For upper semi-circle: subtract from 180 to flip vertically
  const startAngle = 180 - (startPercent * 1.8)
  const endAngle = 180 - (endPercent * 1.8)

  const startRad = (startAngle * Math.PI) / 180
  const endRad = (endAngle * Math.PI) / 180

  // Outer arc points (CORRECTED: use -sin for upper arc)
  const x1 = centerX + radius * Math.cos(startRad)
  const y1 = centerY - radius * Math.sin(startRad)
  const x2 = centerX + radius * Math.cos(endRad)
  const y2 = centerY - radius * Math.sin(endRad)

  // Inner arc points (CORRECTED: use -sin for upper arc)
  const x3 = centerX + innerRadius * Math.cos(endRad)
  const y3 = centerY - innerRadius * Math.sin(endRad)
  const x4 = centerX + innerRadius * Math.cos(startRad)
  const y4 = centerY - innerRadius * Math.sin(startRad)

  // Create the arc path: outer arc clockwise (passing through top), then inner arc counter-clockwise back
  return `M ${x1} ${y1} A ${radius} ${radius} 0 0 1 ${x2} ${y2} L ${x3} ${y3} A ${innerRadius} ${innerRadius} 0 0 0 ${x4} ${y4} Z`
}
</script>

<style scoped>
.fear-greed-gauge {
  @apply w-full flex flex-col items-center;
}

.gauge-container {
  @apply w-full max-w-md;
}

.gauge-svg {
  @apply w-full h-auto;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.3));
}

.gauge-segment {
  transition: opacity 0.3s ease;
}

.gauge-segment:hover {
  opacity: 0.8;
}

.needle {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
  transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.gauge-value {
  @apply text-5xl font-bold fill-white;
  font-family: 'Inter', sans-serif;
}

.gauge-label {
  @apply text-lg fill-gray-400;
  font-family: 'Inter', sans-serif;
}

.gauge-legend {
  @apply mt-6 grid grid-cols-2 md:grid-cols-5 gap-3;
}

.legend-item {
  @apply flex flex-col items-center gap-1 p-2 rounded-lg bg-gray-800/30 hover:bg-gray-800/50 transition-colors;
}

.legend-color {
  @apply w-8 h-2 rounded-full;
}

.legend-text {
  @apply text-xs font-medium text-white;
}

.legend-range {
  @apply text-xs text-gray-400;
}

.gauge-info {
  @apply mt-6 grid grid-cols-3 gap-4 w-full max-w-md;
}

.info-item {
  @apply flex flex-col items-center p-3 rounded-lg bg-gray-800/30;
}

.info-label {
  @apply text-xs text-gray-400 mb-1;
}

.info-value {
  @apply text-lg font-bold text-white;
}
</style>
