-- =====================================================
-- CRYPTO VIZ - ML ANALYTICS SCHEMA
-- Machine Learning and Advanced Analytics Tables
-- =====================================================

-- =====================================================
-- ML PREDICTIONS TABLE
-- =====================================================

-- Table for storing ML model predictions
CREATE TABLE IF NOT EXISTS public.ml_predictions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    prediction_type VARCHAR(50) NOT NULL CHECK (prediction_type IN ('price', 'volatility', 'trend', 'momentum')),
    predicted_value DECIMAL(20,8) NOT NULL,
    confidence DECIMAL(5,4) CHECK (confidence >= 0 AND confidence <= 1),
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    model_version VARCHAR(50),
    model_name VARCHAR(100) DEFAULT 'LinearRegression',

    -- Feature metadata
    features_used JSONB,

    -- Prediction metadata
    rmse DECIMAL(20,8),
    r2_score DECIMAL(10,6),

    -- Additional context
    metadata JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- ANOMALIES TABLE
-- =====================================================

-- Table for storing detected anomalies
CREATE TABLE IF NOT EXISTS public.anomalies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL CHECK (anomaly_type IN ('price_spike', 'price_drop', 'volume_spike', 'volatility', 'pattern', 'correlation_break')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),

    -- Anomaly details
    anomaly_score DECIMAL(10,6) NOT NULL,
    description TEXT NOT NULL,
    expected_value DECIMAL(20,8),
    actual_value DECIMAL(20,8),
    deviation DECIMAL(10,6),

    -- Detection method
    detection_method VARCHAR(50) DEFAULT 'z-score' CHECK (detection_method IN ('z-score', 'isolation_forest', 'dbscan', 'statistical')),

    -- Status tracking
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,

    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Additional metadata
    metadata JSONB
);

-- =====================================================
-- ANALYTICS RESULTS TABLE
-- =====================================================

-- Generic table for storing various analytics metrics
CREATE TABLE IF NOT EXISTS public.analytics_results (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    metric_type VARCHAR(100) NOT NULL CHECK (metric_type IN (
        'rsi', 'macd', 'moving_average', 'bollinger_bands',
        'momentum_score', 'trend_strength', 'volume_profile',
        'support_level', 'resistance_level', 'fibonacci_level',
        'cluster_assignment', 'correlation_coefficient'
    )),

    -- Metric value and details
    metric_value DECIMAL(20,8) NOT NULL,
    metric_label VARCHAR(50),

    -- Time window
    time_window VARCHAR(20),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Additional data
    metadata JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- SENTIMENT RESULTS TABLE
-- =====================================================

-- Table for aggregated sentiment analysis results
CREATE TABLE IF NOT EXISTS public.sentiment_results (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(20),

    -- Sentiment metrics
    sentiment_score DECIMAL(5,4) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    sentiment_label VARCHAR(20) CHECK (sentiment_label IN ('very_negative', 'negative', 'neutral', 'positive', 'very_positive')),
    sentiment_count INTEGER DEFAULT 0,

    -- Fear & Greed Index (0-100)
    fear_greed_index DECIMAL(5,2) CHECK (fear_greed_index >= 0 AND fear_greed_index <= 100),

    -- Source breakdown
    source VARCHAR(50) CHECK (source IN ('news', 'social', 'reddit', 'twitter', 'ollama', 'aggregated')),

    -- Time window
    time_window VARCHAR(20) DEFAULT '24h',
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Sentiment distribution
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,

    -- Confidence
    confidence DECIMAL(5,4),

    -- Additional metadata
    metadata JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- CRYPTO CORRELATIONS TABLE
-- =====================================================

-- Table for storing correlation analysis between crypto pairs
CREATE TABLE IF NOT EXISTS public.crypto_correlations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol_1 VARCHAR(20) NOT NULL,
    symbol_2 VARCHAR(20) NOT NULL,

    -- Correlation metrics
    correlation_coefficient DECIMAL(10,6) NOT NULL CHECK (correlation_coefficient >= -1 AND correlation_coefficient <= 1),
    correlation_type VARCHAR(20) DEFAULT 'pearson' CHECK (correlation_type IN ('pearson', 'spearman', 'kendall')),

    -- Time window
    time_window VARCHAR(20) DEFAULT '7d',
    sample_size INTEGER,

    -- Statistical significance
    p_value DECIMAL(10,8),
    is_significant BOOLEAN DEFAULT false,

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure unique pairs
    UNIQUE(symbol_1, symbol_2, time_window, calculated_at)
);

-- =====================================================
-- ML CLUSTER ASSIGNMENTS TABLE
-- =====================================================

-- Table for storing KMeans cluster assignments
CREATE TABLE IF NOT EXISTS public.ml_cluster_assignments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,

    -- Cluster information
    cluster_id INTEGER NOT NULL,
    cluster_label VARCHAR(100),

    -- Distance metrics
    distance_to_centroid DECIMAL(20,8),
    silhouette_score DECIMAL(10,6),

    -- Features used for clustering
    features_used JSONB,
    feature_values JSONB,

    -- Model metadata
    model_version VARCHAR(50),
    num_clusters INTEGER DEFAULT 5,

    -- Timestamps
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    metadata JSONB
);

-- =====================================================
-- MOMENTUM SCORES TABLE
-- =====================================================

-- Table for custom momentum scoring
CREATE TABLE IF NOT EXISTS public.momentum_scores (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,

    -- Momentum components
    rsi_score DECIMAL(5,2),
    macd_score DECIMAL(5,2),
    volume_score DECIMAL(5,2),
    trend_score DECIMAL(5,2),

    -- Overall momentum
    total_momentum_score DECIMAL(5,2) NOT NULL,
    momentum_label VARCHAR(20) CHECK (momentum_label IN ('very_bearish', 'bearish', 'neutral', 'bullish', 'very_bullish')),

    -- Recommendation
    recommendation VARCHAR(50) CHECK (recommendation IN ('strong_sell', 'sell', 'hold', 'buy', 'strong_buy')),
    confidence DECIMAL(5,4),

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    metadata JSONB
);

-- =====================================================
-- PORTFOLIO RECOMMENDATIONS TABLE
-- =====================================================

-- Table for ML-based portfolio recommendations
CREATE TABLE IF NOT EXISTS public.portfolio_recommendations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID,
    symbol VARCHAR(20) NOT NULL,

    -- Recommendation details
    recommendation_type VARCHAR(50) CHECK (recommendation_type IN ('buy', 'sell', 'hold', 'rebalance')),
    recommendation_strength DECIMAL(5,4) CHECK (recommendation_strength >= 0 AND recommendation_strength <= 1),

    -- Reasoning
    reason TEXT,
    based_on VARCHAR(100), -- e.g., 'cluster_similarity', 'momentum_score', 'correlation_analysis'

    -- Target allocation
    suggested_allocation_percent DECIMAL(5,2),
    current_allocation_percent DECIMAL(5,2),

    -- Risk assessment
    risk_level VARCHAR(20) CHECK (risk_level IN ('very_low', 'low', 'medium', 'high', 'very_high')),

    -- Timestamps
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN DEFAULT true,

    metadata JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- ML MODEL REGISTRY TABLE
-- =====================================================

-- Table for tracking ML models and their versions
CREATE TABLE IF NOT EXISTS public.ml_model_registry (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) CHECK (model_type IN ('regression', 'classification', 'clustering', 'anomaly_detection')),
    model_version VARCHAR(50) NOT NULL,

    -- Model metadata
    model_path TEXT,
    model_size_bytes BIGINT,

    -- Training information
    trained_at TIMESTAMP WITH TIME ZONE,
    training_samples INTEGER,
    training_duration_seconds INTEGER,

    -- Performance metrics
    performance_metrics JSONB,

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_production BOOLEAN DEFAULT false,

    -- Deployment info
    deployed_at TIMESTAMP WITH TIME ZONE,
    deprecated_at TIMESTAMP WITH TIME ZONE,

    -- Additional metadata
    hyperparameters JSONB,
    features JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(model_name, model_version)
);

-- =====================================================
-- INDEXES FOR ML ANALYTICS TABLES
-- =====================================================

-- ML Predictions indexes
CREATE INDEX IF NOT EXISTS idx_ml_predictions_symbol_type ON public.ml_predictions(symbol, prediction_type);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_predicted_at ON public.ml_predictions(predicted_at DESC);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_valid_until ON public.ml_predictions(valid_until);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_active ON public.ml_predictions(symbol, prediction_type, valid_until) WHERE valid_until > NOW();

-- Anomalies indexes
CREATE INDEX IF NOT EXISTS idx_anomalies_symbol_severity ON public.anomalies(symbol, severity);
CREATE INDEX IF NOT EXISTS idx_anomalies_detected_at ON public.anomalies(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_active ON public.anomalies(symbol, is_resolved) WHERE is_resolved = false;
CREATE INDEX IF NOT EXISTS idx_anomalies_severity ON public.anomalies(severity);
CREATE INDEX IF NOT EXISTS idx_anomalies_type ON public.anomalies(anomaly_type);

-- Analytics Results indexes
CREATE INDEX IF NOT EXISTS idx_analytics_results_symbol_metric ON public.analytics_results(symbol, metric_type);
CREATE INDEX IF NOT EXISTS idx_analytics_results_calculated_at ON public.analytics_results(calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_results_metric_type ON public.analytics_results(metric_type);

-- Sentiment Results indexes
CREATE INDEX IF NOT EXISTS idx_sentiment_results_symbol ON public.sentiment_results(symbol);
CREATE INDEX IF NOT EXISTS idx_sentiment_results_calculated_at ON public.sentiment_results(calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_results_source ON public.sentiment_results(source);
CREATE INDEX IF NOT EXISTS idx_sentiment_results_window ON public.sentiment_results(time_window);

-- Crypto Correlations indexes
CREATE INDEX IF NOT EXISTS idx_crypto_correlations_pair ON public.crypto_correlations(symbol_1, symbol_2);
CREATE INDEX IF NOT EXISTS idx_crypto_correlations_calculated_at ON public.crypto_correlations(calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_crypto_correlations_significant ON public.crypto_correlations(is_significant) WHERE is_significant = true;

-- ML Cluster Assignments indexes
CREATE INDEX IF NOT EXISTS idx_ml_cluster_assignments_symbol ON public.ml_cluster_assignments(symbol);
CREATE INDEX IF NOT EXISTS idx_ml_cluster_assignments_cluster ON public.ml_cluster_assignments(cluster_id);
CREATE INDEX IF NOT EXISTS idx_ml_cluster_assignments_assigned_at ON public.ml_cluster_assignments(assigned_at DESC);

-- Momentum Scores indexes
CREATE INDEX IF NOT EXISTS idx_momentum_scores_symbol ON public.momentum_scores(symbol);
CREATE INDEX IF NOT EXISTS idx_momentum_scores_calculated_at ON public.momentum_scores(calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_momentum_scores_label ON public.momentum_scores(momentum_label);

-- Portfolio Recommendations indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_recommendations_user ON public.portfolio_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_recommendations_symbol ON public.portfolio_recommendations(symbol);
CREATE INDEX IF NOT EXISTS idx_portfolio_recommendations_active ON public.portfolio_recommendations(is_active) WHERE is_active = true;

-- ML Model Registry indexes
CREATE INDEX IF NOT EXISTS idx_ml_model_registry_name ON public.ml_model_registry(model_name);
CREATE INDEX IF NOT EXISTS idx_ml_model_registry_active ON public.ml_model_registry(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_ml_model_registry_production ON public.ml_model_registry(is_production) WHERE is_production = true;

-- =====================================================
-- VIEWS FOR ML ANALYTICS
-- =====================================================

-- View for active anomalies
CREATE OR REPLACE VIEW v_active_anomalies AS
SELECT
    id,
    symbol,
    anomaly_type,
    severity,
    anomaly_score,
    description,
    expected_value,
    actual_value,
    deviation,
    detection_method,
    detected_at,
    metadata
FROM public.anomalies
WHERE is_resolved = false
ORDER BY severity DESC, detected_at DESC;

-- View for latest predictions per symbol
CREATE OR REPLACE VIEW v_latest_predictions AS
SELECT DISTINCT ON (symbol, prediction_type)
    id,
    symbol,
    prediction_type,
    predicted_value,
    confidence,
    predicted_at,
    valid_until,
    model_name,
    model_version,
    rmse,
    r2_score,
    features_used,
    metadata
FROM public.ml_predictions
WHERE valid_until > NOW()
ORDER BY symbol, prediction_type, predicted_at DESC;

-- View for current cluster assignments
CREATE OR REPLACE VIEW v_current_cluster_assignments AS
SELECT DISTINCT ON (symbol)
    id,
    symbol,
    cluster_id,
    cluster_label,
    distance_to_centroid,
    silhouette_score,
    assigned_at
FROM public.ml_cluster_assignments
ORDER BY symbol, assigned_at DESC;

-- View for latest sentiment by symbol
CREATE OR REPLACE VIEW v_latest_sentiment AS
SELECT DISTINCT ON (symbol, source)
    id,
    symbol,
    sentiment_score,
    sentiment_label,
    fear_greed_index,
    source,
    time_window,
    calculated_at,
    positive_count,
    negative_count,
    neutral_count,
    confidence
FROM public.sentiment_results
ORDER BY symbol, source, calculated_at DESC;

-- View for latest momentum scores
CREATE OR REPLACE VIEW v_latest_momentum AS
SELECT DISTINCT ON (symbol)
    id,
    symbol,
    rsi_score,
    macd_score,
    volume_score,
    trend_score,
    total_momentum_score,
    momentum_label,
    recommendation,
    confidence,
    calculated_at
FROM public.momentum_scores
ORDER BY symbol, calculated_at DESC;

-- View for correlation matrix (pivot-style)
CREATE OR REPLACE VIEW v_correlation_matrix AS
SELECT
    symbol_1,
    symbol_2,
    correlation_coefficient,
    correlation_type,
    time_window,
    sample_size,
    is_significant,
    calculated_at
FROM public.crypto_correlations
WHERE calculated_at >= NOW() - INTERVAL '7 days'
ORDER BY calculated_at DESC;

-- View for active portfolio recommendations
CREATE OR REPLACE VIEW v_active_recommendations AS
SELECT
    id,
    user_id,
    symbol,
    recommendation_type,
    recommendation_strength,
    reason,
    based_on,
    suggested_allocation_percent,
    risk_level,
    generated_at,
    expires_at
FROM public.portfolio_recommendations
WHERE is_active = true
  AND expires_at > NOW()
ORDER BY recommendation_strength DESC;

-- View for production ML models
CREATE OR REPLACE VIEW v_production_models AS
SELECT
    model_name,
    model_type,
    model_version,
    trained_at,
    performance_metrics,
    deployed_at,
    hyperparameters
FROM public.ml_model_registry
WHERE is_production = true
  AND is_active = true
ORDER BY model_name, trained_at DESC;

-- =====================================================
-- TRIGGERS FOR ML ANALYTICS TABLES
-- =====================================================

-- Apply updated_at triggers for ML tables
DROP TRIGGER IF EXISTS update_ml_predictions_updated_at ON public.ml_predictions;
CREATE TRIGGER update_ml_predictions_updated_at
    BEFORE UPDATE ON public.ml_predictions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_anomalies_updated_at ON public.anomalies;
CREATE TRIGGER update_anomalies_updated_at
    BEFORE UPDATE ON public.anomalies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ml_model_registry_updated_at ON public.ml_model_registry;
CREATE TRIGGER update_ml_model_registry_updated_at
    BEFORE UPDATE ON public.ml_model_registry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-resolve old anomalies
CREATE OR REPLACE FUNCTION auto_resolve_old_anomalies()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.anomalies
    SET is_resolved = true,
        resolved_at = NOW(),
        resolution_notes = 'Auto-resolved: Anomaly older than 7 days'
    WHERE is_resolved = false
      AND detected_at < NOW() - INTERVAL '7 days'
      AND severity IN ('low', 'medium');

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_auto_resolve_anomalies ON public.anomalies;
CREATE TRIGGER trigger_auto_resolve_anomalies
    AFTER INSERT ON public.anomalies
    FOR EACH STATEMENT
    EXECUTE FUNCTION auto_resolve_old_anomalies();

-- Trigger to expire old predictions
CREATE OR REPLACE FUNCTION expire_old_predictions()
RETURNS TRIGGER AS $$
BEGIN
    -- No action needed - we use valid_until in queries
    -- This is a placeholder for future logic
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SAMPLE DATA FOR TESTING
-- =====================================================

-- Insert sample ML model
INSERT INTO public.ml_model_registry (
    model_name, model_type, model_version,
    trained_at, training_samples,
    is_active, is_production,
    performance_metrics,
    hyperparameters
) VALUES (
    'LinearRegression_v1', 'regression', '1.0.0',
    NOW() - INTERVAL '1 day', 10000,
    true, true,
    '{"rmse": 0.0234, "r2_score": 0.87, "mae": 0.0189}'::jsonb,
    '{"max_iter": 100, "learning_rate": 0.01}'::jsonb
),
(
    'KMeans_v1', 'clustering', '1.0.0',
    NOW() - INTERVAL '1 day', 5000,
    true, true,
    '{"silhouette_score": 0.65, "inertia": 1245.67}'::jsonb,
    '{"n_clusters": 5, "max_iter": 300}'::jsonb
)
ON CONFLICT (model_name, model_version) DO NOTHING;

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON TABLE public.ml_predictions IS 'Stores ML model predictions for prices, volatility, and trends';
COMMENT ON TABLE public.anomalies IS 'Tracks detected anomalies in price, volume, and patterns';
COMMENT ON TABLE public.analytics_results IS 'Generic storage for various analytics metrics';
COMMENT ON TABLE public.sentiment_results IS 'Aggregated sentiment analysis from multiple sources';
COMMENT ON TABLE public.crypto_correlations IS 'Correlation analysis between cryptocurrency pairs';
COMMENT ON TABLE public.ml_cluster_assignments IS 'KMeans cluster assignments for cryptocurrencies';
COMMENT ON TABLE public.momentum_scores IS 'Custom momentum scoring combining multiple indicators';
COMMENT ON TABLE public.portfolio_recommendations IS 'ML-based portfolio recommendations for users';
COMMENT ON TABLE public.ml_model_registry IS 'Registry of ML models, versions, and performance metrics';

COMMENT ON VIEW v_active_anomalies IS 'Shows only unresolved anomalies';
COMMENT ON VIEW v_latest_predictions IS 'Shows latest valid predictions per symbol';
COMMENT ON VIEW v_current_cluster_assignments IS 'Shows current cluster assignment per symbol';
COMMENT ON VIEW v_latest_sentiment IS 'Shows latest sentiment score per symbol and source';
COMMENT ON VIEW v_latest_momentum IS 'Shows latest momentum score per symbol';
COMMENT ON VIEW v_correlation_matrix IS 'Recent correlation coefficients between crypto pairs';
COMMENT ON VIEW v_active_recommendations IS 'Active portfolio recommendations for users';
COMMENT ON VIEW v_production_models IS 'Currently deployed production ML models';
