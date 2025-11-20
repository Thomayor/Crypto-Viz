-- =====================================================
-- CRYPTO TOOL - ROW LEVEL SECURITY POLICIES (FINAL)
-- Real-Time Cryptocurrency Tool - EPITECH Project
-- =====================================================

-- Enable RLS on all user-related tables
ALTER TABLE public.user_portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_alerts ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- USER PORTFOLIOS POLICIES
-- =====================================================

-- Policy: Users can view their own portfolios
CREATE POLICY "Users can view own portfolios" ON public.user_portfolios
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can insert their own portfolios
CREATE POLICY "Users can insert own portfolios" ON public.user_portfolios
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own portfolios
CREATE POLICY "Users can update own portfolios" ON public.user_portfolios
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete their own portfolios
CREATE POLICY "Users can delete own portfolios" ON public.user_portfolios
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- USER ALERTS POLICIES
-- =====================================================

-- Policy: Users can view their own alerts
CREATE POLICY "Users can view own alerts" ON public.user_alerts
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can insert their own alerts
CREATE POLICY "Users can insert own alerts" ON public.user_alerts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own alerts
CREATE POLICY "Users can update own alerts" ON public.user_alerts
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete their own alerts
CREATE POLICY "Users can delete own alerts" ON public.user_alerts
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- PUBLIC DATA POLICIES (Read-only for authenticated users)
-- =====================================================

-- Enable RLS on public data tables but allow read access
ALTER TABLE public.cryptocurrencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crypto_prices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crypto_news ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_aggregates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hourly_aggregates ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read cryptocurrencies
CREATE POLICY "Authenticated users can read cryptocurrencies" ON public.cryptocurrencies
    FOR SELECT USING (auth.role() = 'authenticated');

-- Policy: Authenticated users can read crypto prices
CREATE POLICY "Authenticated users can read crypto_prices" ON public.crypto_prices
    FOR SELECT USING (auth.role() = 'authenticated');

-- Policy: Authenticated users can read crypto news
CREATE POLICY "Authenticated users can read crypto_news" ON public.crypto_news
    FOR SELECT USING (auth.role() = 'authenticated');

-- Policy: Authenticated users can read daily aggregates
CREATE POLICY "Authenticated users can read daily_aggregates" ON public.daily_aggregates
    FOR SELECT USING (auth.role() = 'authenticated');

-- Policy: Authenticated users can read hourly aggregates
CREATE POLICY "Authenticated users can read hourly_aggregates" ON public.hourly_aggregates
    FOR SELECT USING (auth.role() = 'authenticated');

-- =====================================================
-- SERVICE ROLE POLICIES (for backend operations)
-- =====================================================

-- Policy: Service role can manage cryptocurrencies
CREATE POLICY "Service role can manage cryptocurrencies" ON public.cryptocurrencies
    FOR ALL USING (auth.role() = 'service_role');

-- Policy: Service role can manage crypto prices
CREATE POLICY "Service role can manage crypto_prices" ON public.crypto_prices
    FOR ALL USING (auth.role() = 'service_role');

-- Policy: Service role can manage crypto news
CREATE POLICY "Service role can manage crypto_news" ON public.crypto_news
    FOR ALL USING (auth.role() = 'service_role');

-- Policy: Service role can manage daily aggregates
CREATE POLICY "Service role can manage daily_aggregates" ON public.daily_aggregates
    FOR ALL USING (auth.role() = 'service_role');

-- Policy: Service role can manage hourly aggregates
CREATE POLICY "Service role can manage hourly_aggregates" ON public.hourly_aggregates
    FOR ALL USING (auth.role() = 'service_role');

-- Policy: Service role can manage processing jobs
ALTER TABLE public.processing_jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can manage processing_jobs" ON public.processing_jobs
    FOR ALL USING (auth.role() = 'service_role');

-- Policy: Service role can manage API sources
ALTER TABLE public.api_sources ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can manage api_sources" ON public.api_sources
    FOR ALL USING (auth.role() = 'service_role');

-- =====================================================
-- ANONYMOUS ACCESS POLICIES (for public endpoints)
-- =====================================================

-- Policy: Anonymous users can read cryptocurrency list
CREATE POLICY "Anonymous can read cryptocurrency list" ON public.cryptocurrencies
    FOR SELECT USING (auth.role() = 'anon');

-- Policy: Anonymous users can read crypto prices
CREATE POLICY "Anonymous can read crypto_prices" ON public.crypto_prices
    FOR SELECT USING (auth.role() = 'anon');

-- Policy: Anonymous users can read crypto news
CREATE POLICY "Anonymous can read crypto_news" ON public.crypto_news
    FOR SELECT USING (auth.role() = 'anon');

-- =====================================================
-- GRANT PERMISSIONS
-- =====================================================

-- Revoke default permissions
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;

-- Grant specific permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO anon;

-- Grant SELECT on public data tables to authenticated users
GRANT SELECT ON public.cryptocurrencies TO authenticated, anon;
GRANT SELECT ON public.crypto_prices TO authenticated, anon;
GRANT SELECT ON public.crypto_news TO authenticated, anon;
GRANT SELECT ON public.daily_aggregates TO authenticated, anon;
GRANT SELECT ON public.hourly_aggregates TO authenticated, anon;

-- Grant CRUD on user tables to authenticated users (RLS will handle access control)
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_portfolios TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_alerts TO authenticated;

-- Grant usage on sequences
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- =====================================================
-- BASIC INDEXES FOR RLS PERFORMANCE
-- =====================================================

-- Create indexes to optimize RLS queries (without temporal predicates)
CREATE INDEX IF NOT EXISTS idx_user_portfolios_user_id ON public.user_portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_user_alerts_user_id ON public.user_alerts(user_id);

-- Basic indexes for performance
CREATE INDEX IF NOT EXISTS idx_crypto_prices_timestamp ON public.crypto_prices(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_crypto_news_published ON public.crypto_news(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_crypto_prices_crypto_id ON public.crypto_prices(cryptocurrency_id);
CREATE INDEX IF NOT EXISTS idx_crypto_news_source ON public.crypto_news(source);