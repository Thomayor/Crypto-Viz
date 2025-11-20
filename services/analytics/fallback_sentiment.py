"""
Fallback Sentiment Classifier
Rule-based sentiment analysis when Ollama is unavailable.
"""

import logging
import re
from typing import List, Dict, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FallbackSentimentResult:
    """Result from fallback sentiment analysis"""
    sentiment: str
    confidence: float
    keywords: List[str]
    method: str = "fallback_rules"

    def to_dict(self) -> Dict:
        return {
            'sentiment': self.sentiment,
            'confidence': self.confidence,
            'keywords': self.keywords,
            'method': self.method
        }


class FallbackSentimentClassifier:
    """
    Rule-based sentiment classifier for degraded mode operation.

    Uses keyword matching and simple heuristics to classify sentiment
    when Ollama is unavailable. Results have lower confidence scores
    to indicate they're from fallback logic.
    """

    # Positive indicators
    POSITIVE_KEYWORDS = {
        # Price action
        'moon', 'mooning', 'bullish', 'bull', 'pump', 'pumping', 'rally',
        'surge', 'soar', 'rocket', 'breakout', 'breakthrough',
        'ath', 'all-time high', 'gains', 'profit', 'winning',

        # Sentiment
        'amazing', 'awesome', 'great', 'excellent', 'fantastic',
        'good', 'positive', 'optimistic', 'confident', 'strong',
        'buy', 'accumulate', 'hodl', 'diamond hands',

        # Technical
        'uptrend', 'support', 'golden cross', 'oversold bounce',
        'volume spike', 'momentum', 'strength',

        # Emojis (as text)
        '🚀', '📈', '💎', '🌙', '💰', '🔥', '✅', '👍', '💪'
    }

    # Negative indicators
    NEGATIVE_KEYWORDS = {
        # Price action
        'dump', 'dumping', 'crash', 'bearish', 'bear', 'plunge',
        'drop', 'fall', 'falling', 'tank', 'tanking', 'collapse',
        'bloodbath', 'rekt', 'losses', 'losing',

        # Sentiment
        'bad', 'terrible', 'awful', 'horrible', 'worst',
        'negative', 'pessimistic', 'worried', 'concerned', 'weak',
        'sell', 'exit', 'paper hands', 'scam', 'rug pull',

        # Technical
        'downtrend', 'resistance', 'death cross', 'overbought',
        'breakdown', 'weakness',

        # Emojis (as text)
        '📉', '💩', '😱', '😢', '❌', '👎', '⚠️', '🔴'
    }

    # Strong positive/negative intensifiers
    INTENSIFIERS = {
        'very', 'extremely', 'absolutely', 'highly', 'super',
        'incredibly', 'really', 'so', 'too', 'much'
    }

    # Negation words that flip sentiment
    NEGATIONS = {
        'not', 'no', 'never', 'none', 'nobody', 'nothing',
        'neither', 'nowhere', 'isnt', "isn't", 'arent', "aren't",
        'wasnt', "wasn't", 'werent', "weren't", 'dont', "don't",
        'doesnt', "doesn't", 'didnt', "didn't", 'wont', "won't",
        'wouldnt', "wouldn't", 'cant', "can't", 'couldnt', "couldn't"
    }

    def __init__(self, confidence_penalty: float = 0.3):
        """
        Initialize fallback classifier.

        Args:
            confidence_penalty: Amount to reduce confidence vs Ollama (0.0-1.0)
        """
        self.confidence_penalty = confidence_penalty
        self.stats = {
            'total_classifications': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0
        }

        logger.info(
            f"Fallback sentiment classifier initialized "
            f"(confidence penalty: {confidence_penalty})"
        )

    def analyze(self, text: str) -> FallbackSentimentResult:
        """
        Analyze sentiment using rule-based approach.

        Args:
            text: Text to analyze

        Returns:
            FallbackSentimentResult
        """
        self.stats['total_classifications'] += 1

        # Preprocess text
        text_lower = text.lower()
        words = self._tokenize(text_lower)

        # Count positive and negative signals
        positive_score = 0
        negative_score = 0
        matched_keywords = []

        # Check for keywords with context
        for i, word in enumerate(words):
            # Check for negation in previous 2 words
            has_negation = False
            if i > 0:
                prev_words = words[max(0, i-2):i]
                has_negation = any(w in self.NEGATIONS for w in prev_words)

            # Check positive keywords
            if word in self.POSITIVE_KEYWORDS or text in self.POSITIVE_KEYWORDS:
                if has_negation:
                    negative_score += 1
                else:
                    positive_score += 1
                    matched_keywords.append(word)

            # Check negative keywords
            elif word in self.NEGATIVE_KEYWORDS or text in self.NEGATIVE_KEYWORDS:
                if has_negation:
                    positive_score += 1
                else:
                    negative_score += 1
                    matched_keywords.append(word)

            # Check for intensifiers
            if word in self.INTENSIFIERS:
                # Look at next word
                if i < len(words) - 1:
                    next_word = words[i + 1]
                    if next_word in self.POSITIVE_KEYWORDS:
                        positive_score += 0.5
                    elif next_word in self.NEGATIVE_KEYWORDS:
                        negative_score += 0.5

        # Price movement patterns (regex)
        price_patterns = self._analyze_price_patterns(text_lower)
        positive_score += price_patterns['positive']
        negative_score += price_patterns['negative']
        matched_keywords.extend(price_patterns['keywords'])

        # Determine sentiment
        sentiment, base_confidence = self._calculate_sentiment(
            positive_score,
            negative_score
        )

        # Apply confidence penalty for fallback
        confidence = max(0.0, base_confidence - self.confidence_penalty)

        # Update stats
        self.stats[f'{sentiment.lower()}_count'] += 1

        # Remove duplicates from keywords
        unique_keywords = list(set(matched_keywords))[:5]  # Top 5

        logger.debug(
            f"Fallback analysis: sentiment={sentiment}, "
            f"confidence={confidence:.2f}, "
            f"pos_score={positive_score}, neg_score={negative_score}"
        )

        return FallbackSentimentResult(
            sentiment=sentiment,
            confidence=confidence,
            keywords=unique_keywords
        )

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        # Remove punctuation except for emojis
        text = re.sub(r'[^\w\s\U0001F300-\U0001F9FF]', ' ', text)
        return text.split()

    def _analyze_price_patterns(self, text: str) -> Dict[str, any]:
        """
        Analyze price movement patterns.

        Returns:
            Dictionary with positive/negative scores and keywords
        """
        result = {
            'positive': 0,
            'negative': 0,
            'keywords': []
        }

        # Price increase patterns
        increase_patterns = [
            r'\+\d+%',  # +5%
            r'up \d+%',  # up 10%
            r'gain(ed)? \d+%',  # gained 15%
            r'\d+x',  # 2x, 10x gains
        ]

        for pattern in increase_patterns:
            if re.search(pattern, text):
                result['positive'] += 1
                result['keywords'].append('price_increase')

        # Price decrease patterns
        decrease_patterns = [
            r'-\d+%',  # -5%
            r'down \d+%',  # down 10%
            r'lost? \d+%',  # lost 15%
            r'drop(ped)? \d+%',  # dropped 20%
        ]

        for pattern in decrease_patterns:
            if re.search(pattern, text):
                result['negative'] += 1
                result['keywords'].append('price_decrease')

        return result

    def _calculate_sentiment(
        self,
        positive_score: float,
        negative_score: float
    ) -> tuple[str, float]:
        """
        Calculate sentiment and confidence from scores.

        Returns:
            Tuple of (sentiment, confidence)
        """
        total_score = positive_score + negative_score

        if total_score == 0:
            # No clear signals - neutral with low confidence
            return "NEUTRAL", 0.5

        # Calculate net sentiment
        net_score = positive_score - negative_score
        net_ratio = abs(net_score) / total_score

        # Determine sentiment
        if net_score > 0.5:
            sentiment = "POSITIVE"
        elif net_score < -0.5:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"

        # Calculate confidence based on strength of signal
        # More signals and higher ratio = higher confidence
        signal_strength = min(total_score / 5.0, 1.0)  # Normalize to 0-1
        confidence = (net_ratio * 0.7 + signal_strength * 0.3)

        # Cap at 0.85 for fallback (never too confident)
        confidence = min(confidence, 0.85)

        return sentiment, confidence

    def analyze_batch(self, texts: List[str]) -> List[FallbackSentimentResult]:
        """
        Analyze multiple texts.

        Args:
            texts: List of texts to analyze

        Returns:
            List of FallbackSentimentResult objects
        """
        results = []
        for text in texts:
            result = self.analyze(text)
            results.append(result)

        logger.info(f"Fallback batch analysis: {len(texts)} texts processed")
        return results

    def get_stats(self) -> Dict:
        """Get classification statistics"""
        stats = self.stats.copy()

        if stats['total_classifications'] > 0:
            for key in ['positive_count', 'negative_count', 'neutral_count']:
                pct_key = key.replace('_count', '_percentage')
                stats[pct_key] = (
                    stats[key] / stats['total_classifications'] * 100
                )

        return stats

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_classifications': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0
        }
        logger.info("Fallback classifier statistics reset")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    classifier = FallbackSentimentClassifier(confidence_penalty=0.3)

    test_texts = [
        "Bitcoin is mooning! 🚀 Up 15% today!",
        "Horrible dump, lost -20% on ETH 😱",
        "ADA price is stable around $0.50",
        "Not good at all, market is crashing",
        "Great bullish momentum but worried about resistance"
    ]

    print("\n=== Fallback Sentiment Analysis ===\n")

    for text in test_texts:
        result = classifier.analyze(text)
        print(f"Text: {text}")
        print(f"  Sentiment: {result.sentiment}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Keywords: {result.keywords}")
        print()

    print("=== Statistics ===")
    stats = classifier.get_stats()
    print(stats)
