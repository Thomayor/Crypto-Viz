-- =====================================
-- Migration: Add sentiment metadata columns
-- =====================================
-- Version: 002
-- Date: 2025-11-20
-- Description: Add analysis_method and confidence_score to crypto_news table
-- =====================================

-- Add analysis_method column (tracks which method was used for sentiment analysis)
ALTER TABLE public.crypto_news
ADD COLUMN IF NOT EXISTS analysis_method VARCHAR(20) DEFAULT 'fallback';

-- Add confidence_score column (tracks confidence of sentiment analysis 0-1)
ALTER TABLE public.crypto_news
ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5, 4);

-- Add sentiment_label column if it doesn't exist
ALTER TABLE public.crypto_news
ADD COLUMN IF NOT EXISTS sentiment_label VARCHAR(20);

-- Update existing records to have default values
UPDATE public.crypto_news
SET analysis_method = 'fallback'
WHERE analysis_method IS NULL;

-- Add index for analysis method for analytics queries
CREATE INDEX IF NOT EXISTS idx_crypto_news_analysis_method
ON public.crypto_news(analysis_method);

-- Add index for confidence score
CREATE INDEX IF NOT EXISTS idx_crypto_news_confidence
ON public.crypto_news(confidence_score)
WHERE confidence_score IS NOT NULL;

-- Add comment to document the new columns
COMMENT ON COLUMN public.crypto_news.analysis_method IS 'Method used for sentiment analysis (ollama, lexicon, or fallback)';
COMMENT ON COLUMN public.crypto_news.confidence_score IS 'Confidence score for sentiment analysis (0.0 to 1.0)';
COMMENT ON COLUMN public.crypto_news.sentiment_label IS 'Sentiment label (POSITIVE, NEGATIVE, NEUTRAL)';
