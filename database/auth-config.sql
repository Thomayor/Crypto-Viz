-- =====================================================
-- CRYPTO TOOL - SUPABASE AUTHENTICATION CONFIGURATION
-- Real-Time Cryptocurrency Tool - EPITECH Project
-- =====================================================

-- =====================================================
-- USER PROFILE EXTENSION
-- =====================================================

-- Create user profiles table to extend auth.users
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'premium', 'admin')),

    -- Preferences
    preferred_currency VARCHAR(10) DEFAULT 'USD',
    timezone VARCHAR(50) DEFAULT 'UTC',
    notification_preferences JSONB DEFAULT '{"email": true, "push": false, "sms": false}'::jsonb,

    -- Subscription info
    subscription_tier VARCHAR(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'basic', 'premium', 'enterprise')),
    subscription_expires_at TIMESTAMP WITH TIME ZONE,

    -- Usage tracking
    api_requests_today INTEGER DEFAULT 0,
    api_requests_month INTEGER DEFAULT 0,
    last_login_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on user profiles
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- USER PROFILES RLS POLICIES
-- =====================================================

-- Users can view their own profile
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Users can insert their own profile
CREATE POLICY "Users can insert own profile" ON public.user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Admins can view all profiles
CREATE POLICY "Admins can view all profiles" ON public.user_profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles up
            WHERE up.id = auth.uid() AND up.role = 'admin'
        )
    );

-- Service role can manage all profiles
CREATE POLICY "Service role can manage profiles" ON public.user_profiles
    FOR ALL USING (auth.role() = 'service_role');

-- =====================================================
-- AUTHENTICATION FUNCTIONS
-- =====================================================

-- Function to create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to automatically create user profile
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update last login
CREATE OR REPLACE FUNCTION public.update_last_login()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.user_profiles
    SET last_login_at = NOW()
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for login tracking
DROP TRIGGER IF EXISTS on_auth_user_login ON auth.users;
CREATE TRIGGER on_auth_user_login
    AFTER UPDATE OF last_sign_in_at ON auth.users
    FOR EACH ROW
    WHEN (OLD.last_sign_in_at IS DISTINCT FROM NEW.last_sign_in_at)
    EXECUTE FUNCTION public.update_last_login();

-- =====================================================
-- SUBSCRIPTION MANAGEMENT
-- =====================================================

-- Function to check subscription status
CREATE OR REPLACE FUNCTION public.is_subscription_active(user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    expires_at TIMESTAMP WITH TIME ZONE;
    tier TEXT;
BEGIN
    SELECT subscription_expires_at, subscription_tier
    INTO expires_at, tier
    FROM public.user_profiles
    WHERE id = user_id;

    -- Free tier is always "active"
    IF tier = 'free' THEN
        RETURN true;
    END IF;

    -- Check if subscription hasn't expired
    RETURN expires_at IS NULL OR expires_at > NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user subscription limits
CREATE OR REPLACE FUNCTION public.get_user_limits(user_id UUID)
RETURNS JSONB AS $$
DECLARE
    user_tier TEXT;
    limits JSONB;
BEGIN
    SELECT subscription_tier INTO user_tier
    FROM public.user_profiles
    WHERE id = user_id;

    CASE user_tier
        WHEN 'free' THEN
            limits := '{"api_calls_per_day": 100, "alerts_max": 3, "portfolios_max": 1, "data_retention_days": 7}'::jsonb;
        WHEN 'basic' THEN
            limits := '{"api_calls_per_day": 1000, "alerts_max": 10, "portfolios_max": 3, "data_retention_days": 30}'::jsonb;
        WHEN 'premium' THEN
            limits := '{"api_calls_per_day": 10000, "alerts_max": 50, "portfolios_max": 10, "data_retention_days": 365}'::jsonb;
        WHEN 'enterprise' THEN
            limits := '{"api_calls_per_day": -1, "alerts_max": -1, "portfolios_max": -1, "data_retention_days": -1}'::jsonb;
        ELSE
            limits := '{"api_calls_per_day": 100, "alerts_max": 3, "portfolios_max": 1, "data_retention_days": 7}'::jsonb;
    END CASE;

    RETURN limits;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- API RATE LIMITING
-- =====================================================

-- Table for tracking API usage
CREATE TABLE IF NOT EXISTS public.user_api_requests (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    response_time_ms INTEGER,
    status_code INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for rate limiting queries
CREATE INDEX IF NOT EXISTS idx_user_api_requests_user_time ON public.user_api_requests(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_api_requests_cleanup ON public.user_api_requests(created_at);

-- Enable RLS on API requests
ALTER TABLE public.user_api_requests ENABLE ROW LEVEL SECURITY;

-- Users can only see their own API requests
CREATE POLICY "Users can view own api requests" ON public.user_api_requests
    FOR SELECT USING (auth.uid() = user_id);

-- Service role can manage all API requests
CREATE POLICY "Service role can manage api requests" ON public.user_api_requests
    FOR ALL USING (auth.role() = 'service_role');

-- Function to log API request
CREATE OR REPLACE FUNCTION public.log_api_request(
    endpoint TEXT,
    ip_addr INET DEFAULT NULL,
    user_agent_string TEXT DEFAULT NULL,
    response_time INTEGER DEFAULT NULL,
    status INTEGER DEFAULT 200
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO public.user_api_requests (
        user_id, endpoint, ip_address, user_agent, response_time_ms, status_code
    ) VALUES (
        auth.uid(), endpoint, ip_addr, user_agent_string, response_time, status
    );

    -- Update daily counter
    UPDATE public.user_profiles
    SET api_requests_today = api_requests_today + 1,
        api_requests_month = api_requests_month + 1
    WHERE id = auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user can make API request
CREATE OR REPLACE FUNCTION public.can_make_api_request(user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    daily_limit INTEGER;
    current_count INTEGER;
    user_limits JSONB;
BEGIN
    -- Get user limits
    user_limits := public.get_user_limits(user_id);
    daily_limit := (user_limits->>'api_calls_per_day')::INTEGER;

    -- -1 means unlimited
    IF daily_limit = -1 THEN
        RETURN true;
    END IF;

    -- Get current count for today
    SELECT api_requests_today INTO current_count
    FROM public.user_profiles
    WHERE id = user_id;

    RETURN COALESCE(current_count, 0) < daily_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- SESSION MANAGEMENT
-- =====================================================

-- Table for tracking user sessions
CREATE TABLE IF NOT EXISTS public.user_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on sessions
ALTER TABLE public.user_sessions ENABLE ROW LEVEL SECURITY;

-- Users can only see their own sessions
CREATE POLICY "Users can view own sessions" ON public.user_sessions
    FOR SELECT USING (auth.uid() = user_id);

-- Users can update their own sessions (for logout)
CREATE POLICY "Users can update own sessions" ON public.user_sessions
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Service role can manage all sessions
CREATE POLICY "Service role can manage sessions" ON public.user_sessions
    FOR ALL USING (auth.role() = 'service_role');

-- =====================================================
-- SECURITY AUDIT SYSTEM
-- =====================================================

-- Create audit logs table for security events
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on audit logs
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Only admins can view audit logs
CREATE POLICY "Only admins can view audit logs" ON public.audit_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- System can insert audit logs
CREATE POLICY "System can insert audit logs" ON public.audit_logs
    FOR INSERT WITH CHECK (true);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_operation ON public.audit_logs(table_name, operation);

-- =====================================================
-- SECURITY AUDIT FUNCTIONS
-- =====================================================

-- Function to log security events
CREATE OR REPLACE FUNCTION public.log_security_event(
    event_type TEXT,
    event_data JSONB DEFAULT '{}'::jsonb,
    ip_addr INET DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO public.audit_logs (
        user_id, table_name, operation, new_values, ip_address
    ) VALUES (
        auth.uid(), 'security_events', event_type, event_data, ip_addr
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to detect suspicious activity
CREATE OR REPLACE FUNCTION public.detect_suspicious_activity(user_id UUID)
RETURNS JSONB AS $$
DECLARE
    recent_requests INTEGER;
    unique_ips INTEGER;
    failed_logins INTEGER;
    result JSONB;
BEGIN
    -- Count recent API requests (last hour)
    SELECT COUNT(*) INTO recent_requests
    FROM public.user_api_requests
    WHERE user_id = detect_suspicious_activity.user_id
    AND created_at > NOW() - INTERVAL '1 hour';

    -- Count unique IPs (last 24 hours)
    SELECT COUNT(DISTINCT ip_address) INTO unique_ips
    FROM public.user_api_requests
    WHERE user_id = detect_suspicious_activity.user_id
    AND created_at > NOW() - INTERVAL '24 hours';

    -- Count failed login attempts (last hour)
    SELECT COUNT(*) INTO failed_logins
    FROM public.audit_logs
    WHERE user_id = detect_suspicious_activity.user_id
    AND operation = 'failed_login'
    AND created_at > NOW() - INTERVAL '1 hour';

    result := jsonb_build_object(
        'high_api_usage', recent_requests > 1000,
        'multiple_ips', unique_ips > 5,
        'failed_logins', failed_logins > 10,
        'api_requests_hour', recent_requests,
        'unique_ips_day', unique_ips,
        'failed_logins_hour', failed_logins
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- CLEANUP FUNCTIONS
-- =====================================================

-- Function to cleanup expired sessions
CREATE OR REPLACE FUNCTION public.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.user_sessions
    WHERE expires_at < NOW() OR (expires_at IS NULL AND created_at < NOW() - INTERVAL '30 days');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to reset daily API counters
CREATE OR REPLACE FUNCTION public.reset_daily_api_counters()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE public.user_profiles
    SET api_requests_today = 0
    WHERE api_requests_today > 0;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to cleanup old API request logs
CREATE OR REPLACE FUNCTION public.cleanup_old_api_requests(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.user_api_requests
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to cleanup old audit logs
CREATE OR REPLACE FUNCTION public.cleanup_old_audit_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.audit_logs
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to cleanup expired sessions
CREATE OR REPLACE FUNCTION public.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.user_sessions
    WHERE expires_at < NOW() OR last_activity_at < NOW() - INTERVAL '30 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- GRANT PERMISSIONS
-- =====================================================

-- Grant access to authenticated users
GRANT SELECT, INSERT, UPDATE ON public.user_profiles TO authenticated;
GRANT SELECT, INSERT ON public.user_api_requests TO authenticated;
GRANT SELECT, UPDATE ON public.user_sessions TO authenticated;

-- Grant usage on sequences
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;