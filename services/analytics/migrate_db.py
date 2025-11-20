#!/usr/bin/env python3
"""
PostgreSQL Database Migration Runner
Executes SQL migration files in order and tracks migration history
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handles database migrations for PostgreSQL"""

    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'postgres')
        self.port = int(os.getenv('POSTGRES_PORT', '5432'))
        self.user = os.getenv('POSTGRES_USER', 'crypto_viz')
        self.password = os.getenv('POSTGRES_PASSWORD', 'crypto_viz_password')
        self.database = os.getenv('POSTGRES_DB', 'crypto_analytics')
        self.migrations_dir = Path(__file__).parent / 'migrations'
        self.conn = None

    def connect(self, max_retries: int = 5) -> bool:
        """Connect to PostgreSQL with retries"""
        import time

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempting to connect to PostgreSQL (attempt {attempt}/{max_retries})...")
                self.conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    connect_timeout=10
                )
                logger.info("✓ Successfully connected to PostgreSQL")
                return True
            except psycopg2.OperationalError as e:
                logger.warning(f"Connection attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    wait_time = 5 * attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("Failed to connect to PostgreSQL after all retries")
                    return False
        return False

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def create_migrations_table(self):
        """Create migrations tracking table if it doesn't exist"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id SERIAL PRIMARY KEY,
                        migration_name VARCHAR(255) NOT NULL UNIQUE,
                        applied_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                """)
                self.conn.commit()
                logger.info("✓ Migrations tracking table ready")
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
            self.conn.rollback()
            raise

    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT migration_name FROM schema_migrations
                    ORDER BY applied_at
                """)
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []

    def get_pending_migrations(self) -> List[Tuple[str, Path]]:
        """Get list of pending SQL migration files"""
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return []

        applied = set(self.get_applied_migrations())
        pending = []

        for migration_file in sorted(self.migrations_dir.glob('*.sql')):
            migration_name = migration_file.name
            if migration_name not in applied:
                pending.append((migration_name, migration_file))

        return pending

    def apply_migration(self, migration_name: str, migration_file: Path) -> bool:
        """Apply a single migration file"""
        try:
            logger.info(f"Applying migration: {migration_name}")

            # Read migration SQL
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()

            # Execute migration
            with self.conn.cursor() as cursor:
                cursor.execute(sql)

                # Record migration
                cursor.execute(
                    "INSERT INTO schema_migrations (migration_name) VALUES (%s)",
                    (migration_name,)
                )

            self.conn.commit()
            logger.info(f"✓ Successfully applied: {migration_name}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to apply {migration_name}: {e}")
            self.conn.rollback()
            return False

    def run_migrations(self) -> bool:
        """Run all pending migrations"""
        try:
            # Create migrations tracking table
            self.create_migrations_table()

            # Get pending migrations
            pending = self.get_pending_migrations()

            if not pending:
                logger.info("✓ No pending migrations to apply")
                return True

            logger.info(f"Found {len(pending)} pending migration(s)")

            # Apply each migration
            success_count = 0
            for migration_name, migration_file in pending:
                if self.apply_migration(migration_name, migration_file):
                    success_count += 1
                else:
                    logger.error(f"Migration failed, stopping at: {migration_name}")
                    return False

            logger.info(f"✓ Successfully applied {success_count} migration(s)")
            return True

        except Exception as e:
            logger.error(f"Migration process failed: {e}")
            return False

    def verify_schema(self) -> bool:
        """Verify that key tables exist"""
        expected_tables = [
            'crypto_prices',
            'crypto_news',
            'social_posts',
            'analytics_results',
            'sentiment_results',
            'ml_predictions',
            'anomalies',
            'system_logs'
        ]

        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                """)
                existing_tables = set(row[0] for row in cursor.fetchall())

                missing_tables = set(expected_tables) - existing_tables

                if missing_tables:
                    logger.warning(f"Missing tables: {', '.join(missing_tables)}")
                    return False

                logger.info(f"✓ All {len(expected_tables)} required tables exist")
                return True

        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            return False


def main():
    """Main migration runner"""
    logger.info("=" * 60)
    logger.info("CRYPTO VIZ - Database Migration Runner")
    logger.info("=" * 60)

    migrator = DatabaseMigrator()

    try:
        # Connect to database
        if not migrator.connect():
            logger.error("Failed to connect to database")
            sys.exit(1)

        # Run migrations
        if not migrator.run_migrations():
            logger.error("Migration process failed")
            sys.exit(1)

        # Verify schema
        if not migrator.verify_schema():
            logger.warning("Schema verification found issues")

        logger.info("=" * 60)
        logger.info("✓ Database migration completed successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        migrator.close()


if __name__ == "__main__":
    main()
