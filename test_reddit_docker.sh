#!/bin/bash

echo "=========================================="
echo "Testing Reddit Social Sentiment Scraper"
echo "=========================================="

docker run --rm \
  --network t-dat-901-nce_10_crypto-viz-network \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 \
  -e REDDIT_CLIENT_ID=5xbAVfJS63zIfA-fM1_j3Q \
  -e REDDIT_CLIENT_SECRET=Z2ijlLDNkuNNphhp4OlGyTAVropGbw \
  -e REDDIT_USER_AGENT=CryptoViz/1.0 \
  -v /mnt/c/Users/kevco/Documents/EPITECH/T-DAT-901-NCE_10/test_reddit_quick.py:/test.py \
  python:3.11-slim \
  bash -c "pip install -q praw && python3 /test.py"
