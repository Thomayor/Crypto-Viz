# Database Initialization Scripts

This directory contains SQL scripts that are automatically executed by PostgreSQL when the database is first created.

## How It Works

When the PostgreSQL Docker container starts for the **first time** (or after a volume cleanup with `docker-compose down -v`), it automatically executes all `.sql` and `.sh` files in `/docker-entrypoint-initdb.d/` in alphabetical order.

Our `docker-compose.yml` mounts this directory:
```yaml
volumes:
  - ./database/init:/docker-entrypoint-initdb.d:ro
```

## Files

### 01_schema.sql
**Purpose**: Creates the complete database schema including:
- All tables (crypto_news, crypto_prices, user_portfolios, etc.)
- All indexes for performance
- All triggers for auto-updates
- Initial seed data (cryptocurrencies, API sources)
- Views for common queries

**When it runs**: Automatically on first PostgreSQL startup

**Contains**:
- ✅ `analysis_method` and `confidence_score` columns (previously in migration 002)
- ✅ All indexes including sentiment metadata indexes
- ✅ Complete and up-to-date schema

## Testing

### Clean Rebuild
```bash
# Remove all data and rebuild
docker-compose down -v
docker-compose up -d postgres

# Wait for initialization (check logs)
docker logs crypto-viz-postgres -f

# Verify schema
docker exec crypto-viz-postgres psql -U crypto_viz -d crypto_analytics -c "\d crypto_news"
```

### Verify Specific Columns
```bash
# Check that analysis_method and confidence_score exist
docker exec crypto-viz-postgres psql -U crypto_viz -d crypto_analytics -c "
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'crypto_news'
AND column_name IN ('analysis_method', 'confidence_score')
ORDER BY column_name;
"
```

## Adding New Initialization Scripts

If you need to add additional initialization:

1. Create a new file: `02_additional_data.sql` (use sequential numbers)
2. Scripts run in **alphabetical order**
3. All scripts must be **idempotent** (use `IF NOT EXISTS`)
4. Test with a clean rebuild

Example:
```sql
-- 02_additional_data.sql
INSERT INTO cryptocurrencies (symbol, name) VALUES
('MATIC', 'Polygon')
ON CONFLICT (symbol) DO NOTHING;
```

## Important Notes

⚠️ **First Startup Only**: These scripts only run when the database is **created**, not on every restart

✅ **Idempotent**: All DDL statements use `IF NOT EXISTS` to avoid errors if run multiple times

🔄 **Updates**: To apply schema updates to an existing database:
- Either: Clean rebuild with `docker-compose down -v` (⚠️ deletes data)
- Or: Apply manual migration (see `database/migrations/README.md`)

📝 **Version Control**: Keep this directory in Git so all developers have the same schema

🐳 **Docker Volume**: The PostgreSQL data is stored in the `postgres_data` Docker volume. Delete this volume to trigger re-initialization.
