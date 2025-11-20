#!/usr/bin/env python3
"""
Quick test script for Bootstrap Pipeline
Tests pandas → Parquet → DuckDB + Spark integration
"""

import asyncio
import logging
from postgres_writer import PostgreSQLWriter
from analytics_processor import BootstrapPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_bootstrap():
    """Test the Bootstrap Stack integration"""
    logger.info("=" * 60)
    logger.info("TESTING BOOTSTRAP STACK")
    logger.info("=" * 60)

    try:
        # Initialize
        pg_writer = PostgreSQLWriter(min_conn=1, max_conn=5)
        bootstrap = BootstrapPipeline(pg_writer)

        logger.info("✓ BootstrapPipeline initialized")

        # 1. Test pandas data extraction
        logger.info("\n[1] Testing pandas data extraction...")
        df_prices = bootstrap.extract_data_with_pandas('crypto_prices', hours=1)
        logger.info(f"  - Extracted {len(df_prices)} price records")

        df_news = bootstrap.extract_data_with_pandas('crypto_news', hours=1)
        logger.info(f"  - Extracted {len(df_news)} news records")

        # 2. Test Parquet export
        logger.info("\n[2] Testing Parquet export...")
        if not df_prices.empty:
            parquet_path = bootstrap.export_to_parquet(df_prices, 'test_prices.parquet')
            if parquet_path:
                logger.info(f"  ✓ Parquet exported to {parquet_path}")

            # 3. Test DuckDB analytics
            if bootstrap.duckdb:
                logger.info("\n[3] Testing DuckDB analytics...")
                results = bootstrap.run_duckdb_analytics(parquet_path)
                logger.info(f"  ✓ DuckDB analytics completed: {len(results)} result sets")
                for key in results.keys():
                    logger.info(f"    - {key}: {len(results[key])} records")
            else:
                logger.warning("\n[3] DuckDB not initialized, skipping")

            # 4. Test Spark ML (basic test, skip if slow)
            if bootstrap.spark_ml:
                logger.info("\n[4] Testing Spark ML...")
                try:
                    logger.info("  - Loading Parquet into Spark...")
                    spark_df = bootstrap.spark_ml.load_parquet(parquet_path)
                    if spark_df:
                        count = spark_df.count()
                        logger.info(f"  ✓ Spark loaded {count} records")
                    else:
                        logger.warning("  - Spark returned None")
                except Exception as e:
                    logger.error(f"  ✗ Spark test failed: {e}")
            else:
                logger.warning("\n[4] Spark not initialized, skipping")

        else:
            logger.warning("No price data available for testing")

        # Cleanup
        pg_writer.close_all()
        if bootstrap.duckdb:
            bootstrap.duckdb.close()
        if bootstrap.spark_ml:
            bootstrap.spark_ml.stop()

        logger.info("\n" + "=" * 60)
        logger.info("✓ BOOTSTRAP STACK TEST COMPLETED")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_bootstrap())
