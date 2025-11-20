# Subreddits Monitored for Crypto Sentiment

This file lists all Reddit subreddits monitored by the Social Sentiment Scraper for cryptocurrency discussions and sentiment analysis.

## Current Subreddits (10)

### Primary Crypto Communities
1. **r/CryptoCurrency** - Main cryptocurrency discussion subreddit
2. **r/Bitcoin** - Bitcoin-focused community
3. **r/ethereum** - Ethereum and ETH 2.0 discussions
4. **r/cardano** - Cardano (ADA) community
5. **r/solana** - Solana (SOL) ecosystem

### Specific Topics
6. **r/polkadot** - Polkadot (DOT) and parachains
7. **r/CryptoMarkets** - Crypto trading and market analysis
8. **r/altcoin** - Alternative cryptocurrency discussions
9. **r/defi** - Decentralized Finance (DeFi)
10. **r/NFT** - NFT and digital collectibles

## Scraping Configuration

- **Scraping Interval**: 10 minutes (600 seconds)
- **Posts per Subreddit**: 10 hot posts per cycle
- **Total Posts per Cycle**: ~100 posts (10 subreddits × 10 posts)
- **Rate Limiting**: 60 API calls per minute

## Adding New Subreddits

To add more subreddits to monitor, edit `social_sentiment_scraper.py` and update the `CRYPTO_SUBREDDITS` list:

```python
CRYPTO_SUBREDDITS = [
    'CryptoCurrency',
    'Bitcoin',
    'ethereum',
    # Add your new subreddit here
    'your_new_subreddit',
]
```

## Filtering Criteria

Posts are included in the sentiment analysis if they:
- ✅ Mention at least one cryptocurrency (by name or symbol)
- ✅ Have a minimum score threshold (configurable)
- ✅ Are posted within the scraping time window

## Excluded Content

The scraper automatically excludes:
- ❌ Posts without cryptocurrency mentions
- ❌ Deleted or removed posts
- ❌ Posts from banned/suspended users
- ❌ Duplicate posts (already seen in previous cycles)

## Data Extracted

For each relevant post, the following data is collected:
- Post ID and author
- Title and text content
- Score (upvotes - downvotes)
- Number of comments
- Creation timestamp
- Subreddit name
- Post URL
- Cryptocurrencies mentioned

## Kafka Topic

All scraped social media posts are published to:
- **Topic**: `social-posts`
- **Partitions**: 3
- **Retention**: 7 days
- **Format**: JSON

## Privacy & Ethics

This scraper:
- ✅ Respects Reddit API rate limits
- ✅ Only collects publicly available data
- ✅ Follows Reddit's API Terms of Service
- ✅ Implements exponential backoff for errors
- ✅ Handles user privacy (anonymizes deleted accounts)
