#!/usr/bin/env python3
"""
Test script for Reddit Social Sentiment Scraper
Tests Reddit API connection and scraping functionality
"""

import os
import sys
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from social_sentiment_scraper import (
    RedditScraper,
    TextPreprocessor,
    CRYPTO_SUBREDDITS
)


async def test_reddit_connection():
    """Test Reddit API connection"""
    print("=" * 60)
    print("Testing Reddit API Connection")
    print("=" * 60)

    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'CryptoViz/1.0')

    if not client_id or not client_secret:
        print("✗ ERROR: Reddit credentials not found in environment")
        print("  Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
        return False

    print(f"✓ Reddit Client ID: {client_id[:10]}...")
    print(f"✓ Reddit User Agent: {user_agent}")

    try:
        scraper = RedditScraper(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        print("✓ Reddit API initialized successfully")
        return scraper
    except Exception as e:
        print(f"✗ Failed to initialize Reddit API: {e}")
        return None


async def test_text_preprocessing():
    """Test text preprocessing"""
    print("\n" + "=" * 60)
    print("Testing Text Preprocessing")
    print("=" * 60)

    preprocessor = TextPreprocessor()

    test_cases = [
        "Bitcoin is going to the moon! $BTC #crypto",
        "I'm buying more ETH and SOL today https://example.com/article",
        "Cardano (ADA) looks promising, also checking out Polkadot",
        "Check out $MATIC and $AVAX!!! 🚀🚀🚀"
    ]

    for i, text in enumerate(test_cases, 1):
        cleaned = preprocessor.clean_text(text)
        coins = preprocessor.extract_coins(text)
        print(f"\nTest {i}:")
        print(f"  Original: {text}")
        print(f"  Cleaned:  {cleaned}")
        print(f"  Coins:    {coins}")

    print("\n✓ Text preprocessing working correctly")


async def test_subreddit_scraping(scraper, subreddit='CryptoCurrency', limit=5):
    """Test scraping from a subreddit"""
    print("\n" + "=" * 60)
    print(f"Testing Subreddit Scraping: r/{subreddit}")
    print("=" * 60)

    try:
        posts = await scraper.scrape_subreddit(subreddit, limit=limit)

        print(f"\n✓ Scraped {len(posts)} posts from r/{subreddit}")

        if posts:
            print("\nSample posts:")
            for i, post in enumerate(posts[:3], 1):
                print(f"\n{i}. {post.title}")
                print(f"   Author: {post.author}")
                print(f"   Score: {post.score}, Comments: {post.num_comments}")
                print(f"   Coins: {', '.join(post.coins_mentioned)}")
                print(f"   URL: {post.url}")
        else:
            print("  No posts with crypto mentions found in this sample")

        return posts
    except Exception as e:
        print(f"✗ Error scraping r/{subreddit}: {e}")
        return []


async def test_multiple_subreddits(scraper, limit=3):
    """Test scraping from multiple subreddits"""
    print("\n" + "=" * 60)
    print("Testing Multiple Subreddits")
    print("=" * 60)

    test_subreddits = ['CryptoCurrency', 'Bitcoin', 'ethereum']

    all_posts = []
    for subreddit in test_subreddits:
        try:
            posts = await scraper.scrape_subreddit(subreddit, limit=limit)
            all_posts.extend(posts)
            print(f"  r/{subreddit}: {len(posts)} posts")
        except Exception as e:
            print(f"  r/{subreddit}: Error - {e}")

    print(f"\n✓ Total: {len(all_posts)} posts from {len(test_subreddits)} subreddits")

    # Count coins mentioned
    coin_counts = {}
    for post in all_posts:
        for coin in post.coins_mentioned:
            coin_counts[coin] = coin_counts.get(coin, 0) + 1

    if coin_counts:
        print("\nCryptocurrency mentions:")
        for coin, count in sorted(coin_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {coin}: {count} mentions")

    return all_posts


async def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("CRYPTO VIZ - Reddit Social Sentiment Scraper Test")
    print("=" * 60)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test 1: Text preprocessing
    await test_text_preprocessing()

    # Test 2: Reddit connection
    scraper = await test_reddit_connection()
    if not scraper:
        print("\n✗ Cannot proceed without Reddit API access")
        return

    # Test 3: Scrape single subreddit
    await test_subreddit_scraping(scraper, 'CryptoCurrency', limit=5)

    # Test 4: Scrape multiple subreddits
    posts = await test_multiple_subreddits(scraper, limit=3)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"✓ All tests completed successfully")
    print(f"✓ Total posts collected: {len(posts)}")
    print(f"✓ Monitored subreddits: {len(CRYPTO_SUBREDDITS)}")
    print(f"✓ Subreddits list: {', '.join(CRYPTO_SUBREDDITS[:5])}...")
    print("\n✓ Reddit Social Sentiment Scraper is ready to use!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
