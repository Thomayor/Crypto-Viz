-- =====================================================
-- FIX MISSING VIEWS
-- Create views that should have been created by init scripts
-- but weren't because the database already existed
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
