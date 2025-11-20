# Database Migrations

This directory contains historical PostgreSQL database migrations for the Crypto Viz project.

## ⚠️ IMPORTANT: Automatic Schema Initialization

**As of 2025-11-20**, all migrations have been consolidated into the main schema file at `database/init/01_schema.sql`. This file is automatically applied when PostgreSQL starts for the first time.

**You no longer need to manually apply migrations!**

## How Database Initialization Works

When you start the PostgreSQL container for the first time (or after a clean rebuild with `docker-compose down -v`), Docker automatically executes all `.sql` files in `/docker-entrypoint-initdb.d/`. Our setup mounts `database/init/` to this directory.

### Clean Rebuild (Recommended for Development)

```bash
# Stop all services and remove volumes (⚠️ DELETES ALL DATA)
docker-compose down -v

# Start services (schema applied automatically)
docker-compose up -d

# Verify schema was applied
docker exec crypto-viz-postgres psql -U crypto_viz -d crypto_analytics -c "\d crypto_news"
```

### Update Existing Database (Manual Migration)

If you already have data and want to add new columns without losing it:

```bash
# Apply specific migration
docker exec -i crypto-viz-postgres psql -U crypto_viz -d crypto_analytics < database/migrations/002_add_sentiment_metadata.sql

# Or use SQL directly
docker exec crypto-viz-postgres psql -U crypto_viz -d crypto_analytics -c "
ALTER TABLE crypto_news ADD COLUMN IF NOT EXISTS new_column VARCHAR(50);
"

# Restart services to pick up schema changes
docker-compose restart backend web-scraper analytics-builder
```

## Migration History

### 002_add_sentiment_metadata.sql (2025-11-20) - ✅ INTEGRATED
**Status**: Integrated into `database/init/01_schema.sql`

**Changes**:
- Added `analysis_method` column (VARCHAR(20), default 'fallback') - tracks sentiment analysis method (ollama, lexicon, or fallback)
- Added `confidence_score` column (DECIMAL(5,4)) - confidence score for sentiment analysis (0.0-1.0)
- Added `sentiment_label` column (VARCHAR(20)) if not exists - sentiment label (POSITIVE, NEGATIVE, NEUTRAL)
- Created indexes for performance optimization

**Why this was needed**:
The web-scraper and analytics services were attempting to insert `analysis_method` and `confidence_score` but the PostgreSQL table didn't have these columns, causing insertion failures.

**Rollback** (⚠️ Data loss):
```sql
DROP INDEX IF EXISTS idx_crypto_news_confidence;
DROP INDEX IF EXISTS idx_crypto_news_analysis_method;
ALTER TABLE crypto_news DROP COLUMN IF EXISTS confidence_score;
ALTER TABLE crypto_news DROP COLUMN IF EXISTS analysis_method;
```

## For Developers

### Adding New Schema Changes

**Development (clean rebuilds OK)**:
1. Edit `database/init/01_schema.sql`
2. Run `docker-compose down -v && docker-compose up -d`

**Production (preserve data)**:
1. Create migration file: `database/migrations/003_your_change.sql`
2. Test migration locally
3. Apply to production manually
4. Update `database/init/01_schema.sql` to include changes
5. Document in this README

### Testing Schema

```bash
# Fresh database test
docker-compose down -v
docker-compose up -d postgres
sleep 15

# Verify all tables exist
docker exec crypto-viz-postgres psql -U crypto_viz -d crypto_analytics -c "
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' ORDER BY table_name;
"

# Check specific table structure
docker exec crypto-viz-postgres psql -U crypto_viz -d crypto_analytics -c "\d crypto_news"
```

## Important Notes

✅ **Automatic**: Schema applied automatically on first startup
✅ **Idempotent**: All DDL uses `IF NOT EXISTS` / `IF EXISTS`
✅ **Version Control**: Schema tracked in Git
⚠️ **Development**: Use `down -v` for development only
🔒 **Production**: Manual migrations to preserve data
📝 **Always Restart**: After schema changes, restart backend/scraper/analytics
