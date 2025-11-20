import { format, formatDistanceToNow, parseISO } from 'date-fns'

export function useFormatting() {
  const formatPrice = (price: string | number | null | undefined): string => {
    if (price === null || price === undefined) return 'N/A'
    const numPrice = typeof price === 'string' ? parseFloat(price) : price
    if (isNaN(numPrice)) return 'N/A'

    if (numPrice >= 1000) {
      return `$${numPrice.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`
    }

    return `$${numPrice.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 6,
    })}`
  }

  const formatMarketCap = (marketCap: string | number | null | undefined): string => {
    if (marketCap === null || marketCap === undefined) return 'N/A'
    const num = typeof marketCap === 'string' ? parseFloat(marketCap) : marketCap
    if (isNaN(num)) return 'N/A'

    if (num >= 1e12) {
      return `$${(num / 1e12).toFixed(2)}T`
    }
    if (num >= 1e9) {
      return `$${(num / 1e9).toFixed(2)}B`
    }
    if (num >= 1e6) {
      return `$${(num / 1e6).toFixed(2)}M`
    }
    if (num >= 1e3) {
      return `$${(num / 1e3).toFixed(2)}K`
    }
    return `$${num.toFixed(2)}`
  }

  const formatVolume = (volume: string | number): string => {
    return formatMarketCap(volume)
  }

  const formatPercentage = (percent: number | null | undefined): string => {
    if (percent === null || percent === undefined || isNaN(percent)) return 'N/A'
    const sign = percent >= 0 ? '+' : ''
    return `${sign}${percent.toFixed(2)}%`
  }

  // Alias for backward compatibility
  const formatPercent = formatPercentage

  const formatNumber = (num: string | number | null | undefined): string => {
    if (num === null || num === undefined) return 'N/A'
    const numValue = typeof num === 'string' ? parseFloat(num) : num
    if (isNaN(numValue)) return 'N/A'
    return formatMarketCap(numValue)
  }

  const formatDate = (dateString: string, formatString: string = 'MMM dd, yyyy HH:mm'): string => {
    try {
      const date = parseISO(dateString)
      return format(date, formatString)
    } catch {
      return dateString
    }
  }

  const formatRelativeTime = (dateString: string): string => {
    try {
      const date = parseISO(dateString)
      return formatDistanceToNow(date, { addSuffix: true })
    } catch {
      return dateString
    }
  }

  const formatSentiment = (score: number | null | undefined): string => {
    if (score === null || score === undefined || isNaN(score)) return 'Unknown'
    if (score >= 0.66) return 'Positive'
    if (score <= 0.33) return 'Negative'
    return 'Neutral'
  }

  const getSentimentColor = (score: number | null | undefined): string => {
    if (score === null || score === undefined || isNaN(score)) return 'text-gray-600'
    if (score >= 0.66) return 'text-green-600'
    if (score <= 0.33) return 'text-red-600'
    return 'text-gray-600'
  }

  const getSentimentBgColor = (score: number | null | undefined): string => {
    if (score === null || score === undefined || isNaN(score)) return 'bg-gray-100'
    if (score >= 0.66) return 'bg-green-100'
    if (score <= 0.33) return 'bg-red-100'
    return 'bg-gray-100'
  }

  const getPercentageColor = (percent: number | null | undefined): string => {
    if (percent === null || percent === undefined || isNaN(percent)) return 'text-gray-600'
    return percent >= 0 ? 'text-green-600' : 'text-red-600'
  }

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-100'
      case 'high':
        return 'text-orange-600 bg-orange-100'
      case 'medium':
        return 'text-yellow-600 bg-yellow-100'
      case 'low':
        return 'text-blue-600 bg-blue-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  return {
    formatPrice,
    formatMarketCap,
    formatVolume,
    formatPercentage,
    formatPercent,
    formatNumber,
    formatDate,
    formatRelativeTime,
    formatSentiment,
    getSentimentColor,
    getSentimentBgColor,
    getPercentageColor,
    getSeverityColor,
  }
}
