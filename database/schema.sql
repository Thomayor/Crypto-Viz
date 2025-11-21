-- =====================================================
-- CRYPTO TOOL - SUPABASE DATABASE SCHEMA
-- Real-Time Cryptocurrency Tool - EPITECH Project
-- =====================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =====================================================
-- CRYPTO DATA TABLES
-- =====================================================

-- Table for storing cryptocurrency information
CREATE TABLE IF NOT EXISTS public.cryptocurrencies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    coingecko_id VARCHAR(100),
    market_cap_rank INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing real-time crypto prices
CREATE TABLE IF NOT EXISTS public.crypto_prices (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    price DECIMAL(20,8) NOT NULL,
    volume_24h DECIMAL(30,2),
    market_cap DECIMAL(30,2),
    percent_change_1h DECIMAL(10,4),
    percent_change_24h DECIMAL(10,4),
    percent_change_7d DECIMAL(10,4),
    circulating_supply DECIMAL(30,2),
    total_supply DECIMAL(30,2),
    max_supply DECIMAL(30,2),
    rank INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source VARCHAR(50) DEFAULT 'coinmarketcap',
    UNIQUE(symbol, timestamp)
);

-- Table for storing crypto news data (scraped)
CREATE TABLE IF NOT EXISTS public.crypto_news (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT UNIQUE,
    source VARCHAR(100) NOT NULL,
    author VARCHAR(200),
    published_at TIMESTAMP WITH TIME ZONE,
    sentiment_score DECIMAL(3,2), -- -1.00 to 1.00
    sentiment_label VARCHAR(20), -- POSITIVE, NEGATIVE, NEUTRAL
    keywords TEXT[], -- Array of keywords
    mentioned_cryptos UUID[], -- Array of cryptocurrency IDs
    analysis_method VARCHAR(20) DEFAULT 'fallback', -- ollama, lexicon, or fallback
    confidence_score DECIMAL(5,4), -- Confidence score (0.0 to 1.0)
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- USER MANAGEMENT TABLES
-- =====================================================

-- Table for user portfolios
CREATE TABLE IF NOT EXISTS public.user_portfolios (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    cryptocurrency_id UUID REFERENCES public.cryptocurrencies(id) ON DELETE CASCADE,
    quantity DECIMAL(20,8) NOT NULL CHECK (quantity >= 0),
    average_buy_price DECIMAL(20,8),
    total_invested DECIMAL(20,8) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, cryptocurrency_id)
);

-- Table for user alerts
CREATE TABLE IF NOT EXISTS public.user_alerts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    cryptocurrency_id UUID REFERENCES public.cryptocurrencies(id) ON DELETE CASCADE,
    alert_type VARCHAR(20) NOT NULL CHECK (alert_type IN ('price_above', 'price_below', 'volume_spike', 'news_sentiment')),
    threshold_value DECIMAL(20,8),
    is_active BOOLEAN DEFAULT true,
    notification_method VARCHAR(20) DEFAULT 'email' CHECK (notification_method IN ('email', 'push', 'sms')),
    triggered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- ANALYTICS AND AGGREGATION TABLES
-- =====================================================

-- Table for daily aggregates (OLAP-style)
CREATE TABLE IF NOT EXISTS public.daily_aggregates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    date DATE NOT NULL,
    cryptocurrency_id UUID REFERENCES public.cryptocurrencies(id) ON DELETE CASCADE,

    -- Price metrics
    open_price DECIMAL(20,8),
    close_price DECIMAL(20,8),
    high_price DECIMAL(20,8),
    low_price DECIMAL(20,8),
    avg_price DECIMAL(20,8),

    -- Volume metrics
    total_volume DECIMAL(20,8),
    avg_volume DECIMAL(20,8),
    volume_variance DECIMAL(20,8),

    -- Market metrics
    market_cap_start DECIMAL(20,8),
    market_cap_end DECIMAL(20,8),
    market_cap_avg DECIMAL(20,8),

    -- News sentiment metrics
    news_count INTEGER DEFAULT 0,
    avg_sentiment_score DECIMAL(3,2),
    positive_news_count INTEGER DEFAULT 0,
    negative_news_count INTEGER DEFAULT 0,
    neutral_news_count INTEGER DEFAULT 0,

    -- Technical indicators
    rsi DECIMAL(5,2),
    moving_avg_7d DECIMAL(20,8),
    moving_avg_30d DECIMAL(20,8),
    volatility DECIMAL(10,6),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(date, cryptocurrency_id)
);

-- Table for hourly aggregates (for real-time analytics)
CREATE TABLE IF NOT EXISTS public.hourly_aggregates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    hour_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    cryptocurrency_id UUID REFERENCES public.cryptocurrencies(id) ON DELETE CASCADE,

    -- Price metrics
    open_price DECIMAL(20,8),
    close_price DECIMAL(20,8),
    high_price DECIMAL(20,8),
    low_price DECIMAL(20,8),
    avg_price DECIMAL(20,8),
    price_variance DECIMAL(20,8),

    -- Volume metrics
    total_volume DECIMAL(20,8),
    trade_count INTEGER DEFAULT 0,

    -- News metrics
    news_count INTEGER DEFAULT 0,
    avg_sentiment DECIMAL(3,2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(hour_timestamp, cryptocurrency_id)
);

-- =====================================================
-- SYSTEM TABLES
-- =====================================================

-- Table for tracking data processing jobs
CREATE TABLE IF NOT EXISTS public.processing_jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    job_status VARCHAR(20) DEFAULT 'pending' CHECK (job_status IN ('pending', 'running', 'completed', 'failed')),
    job_data JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for API rate limiting and source management
CREATE TABLE IF NOT EXISTS public.api_sources (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL UNIQUE,
    base_url TEXT NOT NULL,
    api_key_required BOOLEAN DEFAULT false,
    rate_limit_per_minute INTEGER DEFAULT 60,
    last_request_at TIMESTAMP WITH TIME ZONE,
    request_count_today INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Crypto prices indexes
CREATE INDEX IF NOT EXISTS idx_crypto_prices_crypto_timestamp ON public.crypto_prices(cryptocurrency_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_crypto_prices_timestamp ON public.crypto_prices(timestamp DESC);

-- News indexes
CREATE INDEX IF NOT EXISTS idx_crypto_news_published ON public.crypto_news(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_crypto_news_source ON public.crypto_news(source);
CREATE INDEX IF NOT EXISTS idx_crypto_news_sentiment ON public.crypto_news(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_crypto_news_keywords ON public.crypto_news USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_crypto_news_mentioned_cryptos ON public.crypto_news USING GIN(mentioned_cryptos);
CREATE INDEX IF NOT EXISTS idx_crypto_news_analysis_method ON public.crypto_news(analysis_method);
CREATE INDEX IF NOT EXISTS idx_crypto_news_confidence ON public.crypto_news(confidence_score) WHERE confidence_score IS NOT NULL;

-- Portfolio indexes
CREATE INDEX IF NOT EXISTS idx_user_portfolios_user ON public.user_portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_user_portfolios_crypto ON public.user_portfolios(cryptocurrency_id);

-- Alerts indexes
CREATE INDEX IF NOT EXISTS idx_user_alerts_user_active ON public.user_alerts(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_alerts_crypto_active ON public.user_alerts(cryptocurrency_id, is_active);

-- Daily aggregates indexes
CREATE INDEX IF NOT EXISTS idx_daily_aggregates_date_crypto ON public.daily_aggregates(date DESC, cryptocurrency_id);
CREATE INDEX IF NOT EXISTS idx_daily_aggregates_crypto_date ON public.daily_aggregates(cryptocurrency_id, date DESC);

-- Hourly aggregates indexes
CREATE INDEX IF NOT EXISTS idx_hourly_aggregates_hour_crypto ON public.hourly_aggregates(hour_timestamp DESC, cryptocurrency_id);

-- Processing jobs indexes
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON public.processing_jobs(job_status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_type ON public.processing_jobs(job_type);

-- =====================================================
-- TRIGGERS FOR AUTO-UPDATES
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_cryptocurrencies_updated_at BEFORE UPDATE ON public.cryptocurrencies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_portfolios_updated_at BEFORE UPDATE ON public.user_portfolios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_alerts_updated_at BEFORE UPDATE ON public.user_alerts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_daily_aggregates_updated_at BEFORE UPDATE ON public.daily_aggregates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_api_sources_updated_at BEFORE UPDATE ON public.api_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Insert major cryptocurrencies
INSERT INTO public.cryptocurrencies (symbol, name, coingecko_id, market_cap_rank) VALUES
('BTC', 'Bitcoin', 'bitcoin', 1),
('ETH', 'Ethereum', 'ethereum', 2),
('BNB', 'BNB', 'binancecoin', 3),
('SOL', 'Solana', 'solana', 4),
('USDC', 'USD Coin', 'usd-coin', 5),
('XRP', 'XRP', 'ripple', 6),
('DOGE', 'Dogecoin', 'dogecoin', 7),
('TON', 'Toncoin', 'the-open-network', 8),
('ADA', 'Cardano', 'cardano', 9),
('AVAX', 'Avalanche', 'avalanche-2', 10)
ON CONFLICT (symbol) DO NOTHING;

-- Insert API sources
INSERT INTO public.api_sources (source_name, base_url, api_key_required, rate_limit_per_minute) VALUES
('CoinGecko', 'https://api.coingecko.com/api/v3', false, 30),
('CoinMarketCap', 'https://pro-api.coinmarketcap.com/v1', true, 333),
('CryptoCompare', 'https://min-api.cryptocompare.com/data', true, 100),
('NewsAPI', 'https://newsapi.org/v2', true, 1000),
('CryptoPanic', 'https://cryptopanic.com/api/v1', true, 200)
ON CONFLICT (source_name) DO NOTHING;