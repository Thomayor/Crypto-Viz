-- =====================================================
-- CRYPTO VIZ - SUPABASE DATABASE SCHEMA
-- Real-Time Cryptocurrency Analytics - EPITECH Project
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
    source VARCHAR(100),
    author VARCHAR(255),
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL UNIQUE,
    url_to_image TEXT,
    content TEXT,
    published_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    sentiment_score DECIMAL(5,4),
    sentiment_label VARCHAR(20),
    keywords TEXT[],
    mentioned_coins VARCHAR(20)[],
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    analysis_method VARCHAR(20) DEFAULT 'fallback',
    confidence_score DECIMAL(5,4)
);

-- =====================================================
-- USER MANAGEMENT TABLES
-- =====================================================

-- Table for user portfolios
CREATE TABLE IF NOT EXISTS public.user_portfolios (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID,
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
    user_id UUID,
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
CREATE INDEX IF NOT EXISTS idx_crypto_prices_symbol_timestamp ON public.crypto_prices(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_crypto_prices_timestamp ON public.crypto_prices(timestamp DESC);

-- News indexes
CREATE INDEX IF NOT EXISTS idx_crypto_news_published_at ON public.crypto_news(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_crypto_news_source ON public.crypto_news(source);
CREATE INDEX IF NOT EXISTS idx_crypto_news_sentiment ON public.crypto_news(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_crypto_news_keywords ON public.crypto_news USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_crypto_news_mentioned_coins ON public.crypto_news USING GIN(mentioned_coins);
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
DROP TRIGGER IF EXISTS update_cryptocurrencies_updated_at ON public.cryptocurrencies;
CREATE TRIGGER update_cryptocurrencies_updated_at BEFORE UPDATE ON public.cryptocurrencies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_portfolios_updated_at ON public.user_portfolios;
CREATE TRIGGER update_user_portfolios_updated_at BEFORE UPDATE ON public.user_portfolios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_alerts_updated_at ON public.user_alerts;
CREATE TRIGGER update_user_alerts_updated_at BEFORE UPDATE ON public.user_alerts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_daily_aggregates_updated_at ON public.daily_aggregates;
CREATE TRIGGER update_daily_aggregates_updated_at BEFORE UPDATE ON public.daily_aggregates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_api_sources_updated_at ON public.api_sources;
CREATE TRIGGER update_api_sources_updated_at BEFORE UPDATE ON public.api_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- View for latest crypto prices
CREATE OR REPLACE VIEW v_latest_crypto_prices AS
SELECT DISTINCT ON (symbol)
    id,
    symbol,
    name,
    price,
    volume_24h,
    market_cap,
    percent_change_1h,
    percent_change_24h,
    percent_change_7d,
    circulating_supply,
    total_supply,
    max_supply,
    rank,
    timestamp,
    source
FROM crypto_prices
ORDER BY symbol, timestamp DESC;

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

-- =====================================================
-- SYSTEM LOGS TABLE
-- =====================================================

-- Table for storing system logs from all services
CREATE TABLE IF NOT EXISTS public.system_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    service VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster log queries
CREATE INDEX IF NOT EXISTS idx_system_logs_service ON public.system_logs(service);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON public.system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON public.system_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_logs_metadata ON public.system_logs USING GIN(metadata);
