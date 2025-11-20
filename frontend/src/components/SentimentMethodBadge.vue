<template>
  <div class="sentiment-method-badge" :class="`method-${method}`" v-if="method">
    <div class="badge-content">
      <span class="method-icon">{{ methodIcon }}</span>
      <span class="method-text">{{ methodLabel }}</span>
      <span v-if="confidence !== undefined" class="confidence-indicator" :style="confidenceStyle">
        {{ (confidence * 100).toFixed(0) }}%
      </span>
    </div>
    <div v-if="showTooltip" class="tooltip">
      <div class="tooltip-title">{{ tooltipTitle }}</div>
      <div class="tooltip-content">
        <p><strong>Method:</strong> {{ methodDescription }}</p>
        <p v-if="confidence !== undefined"><strong>Confidence:</strong> {{ (confidence * 100).toFixed(1) }}%</p>
        <p v-if="keywords && keywords.length > 0">
          <strong>Keywords:</strong> {{ keywords.slice(0, 3).join(', ') }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  method?: 'ollama' | 'lexicon' | 'fallback'
  confidence?: number
  keywords?: string[]
  showTooltip?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  method: undefined,
  confidence: undefined,
  keywords: () => [],
  showTooltip: true
})

const methodIcon = computed(() => {
  switch (props.method) {
    case 'ollama':
      return '🤖'
    case 'lexicon':
    case 'fallback':
      return '📊'
    default:
      return '❓'
  }
})

const methodLabel = computed(() => {
  switch (props.method) {
    case 'ollama':
      return 'Ollama AI'
    case 'lexicon':
      return 'Lexicon'
    case 'fallback':
      return 'Fallback'
    default:
      return 'Unknown'
  }
})

const methodDescription = computed(() => {
  switch (props.method) {
    case 'ollama':
      return 'AI-powered sentiment analysis using Ollama (gemma:2b model)'
    case 'lexicon':
      return 'Rule-based lexicon sentiment analysis'
    case 'fallback':
      return 'Fallback rule-based classifier'
    default:
      return 'Unknown analysis method'
  }
})

const tooltipTitle = computed(() => {
  return `Sentiment Analysis: ${methodLabel.value}`
})

const confidenceStyle = computed(() => {
  if (props.confidence === undefined) return {}

  const hue = props.confidence * 120 // 0 = red, 120 = green
  return {
    backgroundColor: `hsl(${hue}, 70%, 50%)`,
    color: 'white'
  }
})
</script>

<style scoped>
.sentiment-method-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  position: relative;
  cursor: help;
  transition: all 0.2s ease;
}

.sentiment-method-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.method-ollama {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.method-lexicon,
.method-fallback {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.badge-content {
  display: flex;
  align-items: center;
  gap: 6px;
}

.method-icon {
  font-size: 1rem;
  line-height: 1;
}

.method-text {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.confidence-indicator {
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 0.65rem;
  font-weight: 700;
  margin-left: 4px;
}

.tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-8px);
  background: rgba(0, 0, 0, 0.95);
  color: white;
  padding: 12px;
  border-radius: 8px;
  min-width: 220px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.sentiment-method-badge:hover .tooltip {
  opacity: 1;
  pointer-events: auto;
}

.tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.95);
}

.tooltip-title {
  font-weight: 700;
  font-size: 0.8rem;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.tooltip-content {
  font-size: 0.7rem;
  line-height: 1.4;
}

.tooltip-content p {
  margin: 4px 0;
}

.tooltip-content strong {
  color: #10b981;
}
</style>
