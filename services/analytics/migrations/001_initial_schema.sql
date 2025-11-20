-- =====================================
-- CRYPTO VIZ - PostgreSQL Schema
-- =====================================
-- Initial schema for long-term storage
-- Version: 1.0.0
-- Date: 2025-11-06
-- =====================================

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================
-- CRYPTO PRICES TABLE
-- =====================================
CREATE TABLE IF NOT EXISTS crypto_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    market_cap DECIMAL(20, 2),
    volume_24h DECIMAL(20, 2),
    percent_change_1h DECIMAL(10, 4),
    percent_change_24h DECIMAL(10, 4),
    percent_change_7d DECIMAL(10, 4),
    circulating_supply DECIMAL(20, 2),
    total_supply DECIMAL(20, 2),
    max_supply DECIMAL(20, 2),
    rank INTEGER,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT crypto_prices_symbol_timestamp_unique UNIQUE (symbol, timestamp)
);

-- Index for time-series queries
CREATE INDEX idx_crypto_prices_symbol_timestamp ON crypto_prices (symbol, timestamp DESC);
CREATE INDEX idx_crypto_prices_timestamp ON crypto_prices (timestamp DESC);
CREATE INDEX idx_crypto_prices_rank ON crypto_prices (rank);

-- =====================================
-- CRYPTO NEWS TABLE
-- =====================================
CREATE TABLE IF NOT EXISTS crypto_news (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source VARCHAR(100),
    author VARCHAR(255),
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    url_to_image TEXT,
    content TEXT,
    published_at TIMESTAMP NOT NULL,
    sentiment_score DECIMAL(5, 4),
    sentiment_label VARCHAR(20),
    keywords TEXT[],
    mentioned_coins VARCHAR(20)[],
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT crypto_news_url_unique UNIQUE (url)
);

-- Indexes for news queries
CREATE INDEX idx_crypto_news_published_at ON crypto_news (published_at DESC);
CREATE INDEX idx_crypto_news_sentiment ON crypto_news (sentiment_score);
CREATE INDEX idx_crypto_news_mentioned_coins ON crypto_news USING GIN (mentioned_coins);
CREATE INDEX idx_crypto_news_keywords ON crypto_news USING GIN (keywords);

-- =====================================
-- SOCIAL POSTS TABLE
-- =====================================
CREATE TABLE IF NOT EXISTS social_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL,
    post_id VARCHAR(255) NOT NULL,
    subreddit VARCHAR(100),
    author VARCHAR(255),
    title TEXT,
    content TEXT,
    url TEXT,
    score INTEGER,
    num_comments INTEGER,
    upvote_ratio DECIMAL(5, 4),
    sentiment_score DECIMAL(5, 4),
    sentiment_label VARCHAR(20),
    mentioned_coins VARCHAR(20)[],
    published_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT social_posts_platform_post_id_unique UNIQUE (platform, post_id)
);

-- Indexes for social posts
CREATE INDEX idx_social_posts_platform_published ON social_posts (platform, published_at DESC);
CREATE INDEX idx_social_posts_subreddit ON social_posts (subreddit);
CREATE INDEX idx_social_posts_sentiment ON social_posts (sentiment_score);
CREATE INDEX idx_social_posts_mentioned_coins ON social_posts USING GIN (mentioned_coins);

-- =====================================
-- ANALYTICS RESULTS TABLE
-- =====================================
CREATE TABLE IF NOT EXISTS analytics_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(20, 8),
    metadata JSONB,
    calculated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for analytics queries
CREATE INDEX idx_analytics_results_symbol_metric ON analytics_results (symbol, metric_type, calculated_at DESC);
CREATE INDEX idx_analytics_results_calculated_at ON analytics_results (calculated_at DESC);
CREATE INDEX idx_analytics_results_metadata ON analytics_results USING GIN (metadata);

-- =====================================
-- SENTIMENT RESULTS TABLE
-- =====================================
CREATE TABLE IF NOT EXISTS sentiment_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    source VARCHAR(50) NOT NULL,
    sentiment_score DECIMAL(5, 4) NOT NULL,
    sentiment_label VARCHAR(20) NOT NULL,
    sentiment_count INTEGER NOT NULL DEFAULT 1,
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    time_window VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for sentiment queries
CREATE INDEX idx_sentiment_results_symbol_time ON sentiment_results (symbol, time_window, calculated_at DESC);
CREATE INDEX idx_sentiment_results_source ON sentiment_results (source, calculated_at DESC);

-- =====================================
-- ML PREDICTIONS TABLE
-- =====================================
CREATE TABLE IF NOT EXISTS ml_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    prediction_type VARCHAR(50) NOT NULL,
    predicted_value DECIMAL(20, 8),
    confidence_score DECIMAL(5, 4),
    features JSONB,
    prediction_horizon VARCHAR(20),
    predicted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for ML predictions
CREATE INDEX idx_ml_predictions_symbol_model ON ml_predictions (symbol, model_name, predicted_at DESC);
CREATE INDEX idx_ml_predictions_type ON ml_predictions (prediction_type, predicted_at DESC);

-- =====================================
-- ANOMALIES TABLE
-- =====================================
CREATE TABLE IF NOT EXISTS anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    anomaly_score DECIMAL(5, 4),
    metadata JSONB,
    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for anomalies
CREATE INDEX idx_anomalies_symbol_detected ON anomalies (symbol, detected_at DESC);
CREATE INDEX idx_anomalies_severity ON anomalies (severity, detected_at DESC);
CREATE INDEX idx_anomalies_resolved ON anomalies (resolved_at) WHERE resolved_at IS NULL;

-- =====================================
-- SYSTEM LOGS TABLE
-- =====================================
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service VARCHAR(50) NOT NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for logs
CREATE INDEX idx_system_logs_service_created ON system_logs (service, created_at DESC);
CREATE INDEX idx_system_logs_level ON system_logs (level, created_at DESC);

-- =====================================
-- VIEWS FOR COMMON QUERIES
-- =====================================

-- Latest crypto prices per symbol
CREATE OR REPLACE VIEW v_latest_crypto_prices AS
SELECT DISTINCT ON (symbol)
    id,
    symbol,
    name,
    price,
    market_cap,
    volume_24h,
    percent_change_1h,
    percent_change_24h,
    percent_change_7d,
    rank,
    timestamp
FROM crypto_prices
ORDER BY symbol, timestamp DESC;

-- Daily sentiment aggregation
CREATE OR REPLACE VIEW v_daily_sentiment AS
SELECT
    symbol,
    source,
    DATE(calculated_at) as date,
    AVG(sentiment_score) as avg_sentiment,
    SUM(positive_count) as total_positive,
    SUM(negative_count) as total_negative,
    SUM(neutral_count) as total_neutral,
    COUNT(*) as data_points
FROM sentiment_results
GROUP BY symbol, source, DATE(calculated_at)
ORDER BY date DESC, symbol;

-- Recent analytics summary
CREATE OR REPLACE VIEW v_recent_analytics AS
SELECT
    symbol,
    metric_type,
    metric_value,
    metadata,
    calculated_at
FROM analytics_results
WHERE calculated_at >= NOW() - INTERVAL '24 hours'
ORDER BY calculated_at DESC;

-- Active anomalies
CREATE OR REPLACE VIEW v_active_anomalies AS
SELECT
    id,
    symbol,
    anomaly_type,
    severity,
    description,
    anomaly_score,
    detected_at
FROM anomalies
WHERE resolved_at IS NULL
ORDER BY severity DESC, detected_at DESC;

-- =====================================
-- PARTITIONING SETUP (for future scalability)
-- =====================================
-- Note: Partitioning can be enabled later for high-volume tables
-- Example: Partition crypto_prices by month for time-series optimization

COMMENT ON TABLE crypto_prices IS 'Historical cryptocurrency price data from CoinMarketCap';
COMMENT ON TABLE crypto_news IS 'News articles about cryptocurrencies from NewsAPI';
COMMENT ON TABLE social_posts IS 'Social media posts from Reddit and Twitter';
COMMENT ON TABLE analytics_results IS 'Processed analytics results from Spark';
COMMENT ON TABLE sentiment_results IS 'Aggregated sentiment analysis results';
COMMENT ON TABLE ml_predictions IS 'Machine learning model predictions';
COMMENT ON TABLE anomalies IS 'Detected anomalies in price or sentiment data';
COMMENT ON TABLE system_logs IS 'System-wide logging for all services';
