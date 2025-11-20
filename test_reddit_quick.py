#!/usr/bin/env python3
"""Quick test of Reddit API connection"""

import os
import sys

# Set environment variables
os.environ['REDDIT_CLIENT_ID'] = '5xbAVfJS63zIfA-fM1_j3Q'
os.environ['REDDIT_CLIENT_SECRET'] = 'Z2ijlLDNkuNNphhp4OlGyTAVropGbw'
os.environ['REDDIT_USER_AGENT'] = 'CryptoViz/1.0'

print("=" * 60)
print("Testing Reddit API Connection")
print("=" * 60)

try:
    import praw
    print("✓ praw module imported")
except ImportError:
    print("✗ praw not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "praw"])
    import praw
    print("✓ praw installed and imported")

print("\nConnecting to Reddit API...")
try:
    reddit = praw.Reddit(
        client_id=os.environ['REDDIT_CLIENT_ID'],
        client_secret=os.environ['REDDIT_CLIENT_SECRET'],
        user_agent=os.environ['REDDIT_USER_AGENT']
    )

    print("✓ Reddit API initialized")

    # Test connection
    subreddit = reddit.subreddit('CryptoCurrency')
    print(f"✓ Connected to r/{subreddit.display_name}")
    print(f"  Subscribers: {subreddit.subscribers:,}")

    # Get some posts
    print("\nFetching recent posts...")
    crypto_posts = []

    for i, post in enumerate(subreddit.hot(limit=10), 1):
        # Check if post mentions crypto
        text = (post.title + " " + post.selftext).lower()
        has_crypto = any(coin in text for coin in ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto'])

        if has_crypto:
            crypto_posts.append(post)
            print(f"\n{len(crypto_posts)}. {post.title[:60]}...")
            print(f"   Score: {post.score}, Comments: {post.num_comments}")
            print(f"   Author: {post.author}")

    print("\n" + "=" * 60)
    print(f"✓ SUCCESS! Found {len(crypto_posts)} crypto-related posts")
    print("=" * 60)
    print("\n✓ Reddit Social Sentiment Scraper is ready!")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
