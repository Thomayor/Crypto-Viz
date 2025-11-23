"""
Run database migrations at startup
This ensures all required views and schema updates are applied
"""

import os
import psycopg2
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run all SQL migration files"""
    try:
        # Get database connection parameters
        conn_params = {
            'host': os.getenv('POSTGRES_HOST', 'postgres'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'user': os.getenv('POSTGRES_USER', 'crypto_viz'),
            'password': os.getenv('POSTGRES_PASSWORD', 'crypto_viz_password'),
            'database': os.getenv('POSTGRES_DB', 'crypto_analytics')
        }

        logger.info("Connecting to PostgreSQL to run migrations...")
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()

        # Path to migrations directory - try multiple locations
        # First try: /app/migrations (inside backend directory in Docker)
        # Second try: ../database/migrations (local development)
        migrations_dir = Path(__file__).parent / 'migrations'

        if not migrations_dir.exists():
            # Try alternative path for local development
            migrations_dir = Path(__file__).parent.parent / 'database' / 'migrations'

        if not migrations_dir.exists():
            logger.warning(f"Migrations directory not found at {Path(__file__).parent / 'migrations'}")
            return

        logger.info(f"Using migrations directory: {migrations_dir}")

        # Get all .sql files in migrations directory
        migration_files = sorted(migrations_dir.glob('*.sql'))

        if not migration_files:
            logger.info("No migration files found")
            return

        logger.info(f"Found {len(migration_files)} migration file(s)")

        # Execute each migration file
        for migration_file in migration_files:
            logger.info(f"Running migration: {migration_file.name}")

            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    sql = f.read()

                cursor.execute(sql)
                logger.info(f"✓ Migration {migration_file.name} completed successfully")

            except Exception as e:
                logger.error(f"✗ Error running migration {migration_file.name}: {e}")
                # Continue with other migrations even if one fails
                continue

        cursor.close()
        conn.close()
        logger.info("All migrations completed")

    except Exception as e:
        logger.error(f"Error connecting to database or running migrations: {e}")
        raise

if __name__ == '__main__':
    run_migrations()
