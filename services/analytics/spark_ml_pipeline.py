#!/usr/bin/env python3
"""
Spark ML Pipeline
Distributed machine learning for crypto analytics
Part of Bootstrap Stack (EPITECH requirement)
"""

import logging
import os
import yaml
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import time

# Spark imports
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import VectorAssembler, StandardScaler, StringIndexer
from pyspark.ml.regression import LinearRegression
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import RegressionEvaluator, ClusteringEvaluator

logger = logging.getLogger(__name__)


class SparkMLPipeline:
    """Spark ML pipeline for distributed machine learning on crypto data"""

    def __init__(self, config_path: str = "config/analytics_config.yaml"):
        """Initialize Spark session with configuration"""
        self.config = self._load_config(config_path)
        self.spark_config = self.config['bootstrap_stack']['spark']
        self.ml_config = self.config['ml_pipeline']

        # Don't create session at init - use lazy initialization
        self._spark = None
        logger.info("Spark ML Pipeline initialized (lazy session creation)")

    @property
    def spark(self):
        """Lazy initialization of Spark session"""
        if self._spark is None or self._spark._jsc is None:
            logger.info("Creating Spark session...")
            self._spark = self._create_spark_session()
            logger.info("Spark session created (master: {})".format(self.spark_config['master_url']))
        return self._spark

    def _load_config(self, config_path: str) -> Dict:
        """Load analytics configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            # Return minimal default config
            return {
                'bootstrap_stack': {
                    'spark': {
                        'master_url': 'spark://spark-master:7077',
                        'app_name': 'crypto-viz-ml-pipeline',
                        'executor_memory': '1g',
                        'executor_cores': 1,
                        'max_cores': 4,
                        'driver_memory': '512m',
                        'shuffle_partitions': 10
                    }
                },
                'ml_pipeline': {
                    'price_prediction': {'enabled': True},
                    'clustering': {'enabled': True},
                    'anomaly': {'enabled': True}
                }
            }

    def _create_spark_session(self) -> SparkSession:
        """Create and configure Spark session"""
        builder = SparkSession.builder \
            .appName(self.spark_config['app_name']) \
            .master(self.spark_config['master_url']) \
            .config("spark.executor.memory", self.spark_config['executor_memory']) \
            .config("spark.executor.cores", self.spark_config['executor_cores']) \
            .config("spark.cores.max", self.spark_config['max_cores']) \
            .config("spark.driver.memory", self.spark_config['driver_memory']) \
            .config("spark.sql.shuffle.partitions", self.spark_config['shuffle_partitions']) \
            .config("spark.sql.parquet.compression.codec", "snappy")

        spark = builder.getOrCreate()
        spark.sparkContext.setLogLevel("WARN")

        logger.info(f"Spark session created (master: {self.spark_config['master_url']})")
        return spark

    def stop(self):
        """Stop Spark session"""
        if self._spark:
            try:
                self._spark.stop()
                logger.info("Spark session stopped")
            except Exception as e:
                logger.warning(f"Error stopping Spark session: {e}")
            finally:
                self._spark = None

    # ========================================
    # DATA LOADING & PREPARATION
    # ========================================

    def load_parquet(self, path: str) -> Optional[DataFrame]:
        """Load data from Parquet file(s)"""
        try:
            start_time = time.time()
            df = self.spark.read.parquet(path)
            elapsed = time.time() - start_time

            count = df.count()
            logger.info(f"✓ Loaded {count} rows from {path} ({elapsed:.2f}s)")
            return df

        except Exception as e:
            logger.error(f"Failed to load Parquet from {path}: {e}")
            return None

    def save_parquet(self, df: DataFrame, path: str, mode: str = "overwrite") -> bool:
        """Save DataFrame to Parquet"""
        try:
            start_time = time.time()

            # Create output directory
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            df.write.mode(mode).parquet(path)

            elapsed = time.time() - start_time
            logger.info(f"✓ Saved {df.count()} rows to {path} ({elapsed:.2f}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to save Parquet to {path}: {e}")
            return False

    def prepare_crypto_features(self, df: DataFrame) -> DataFrame:
        """Prepare features for ML models"""
        try:
            # Sort by symbol and timestamp
            df = df.orderBy("symbol", "timestamp")

            # Create lag features for price
            window_1h = F.lag("price", 60).over(
                Window.partitionBy("symbol").orderBy("timestamp")
            )
            window_4h = F.lag("price", 240).over(
                Window.partitionBy("symbol").orderBy("timestamp")
            )
            window_24h = F.lag("price", 1440).over(
                Window.partitionBy("symbol").orderBy("timestamp")
            )

            df = df.withColumn("price_lag_1h", window_1h) \
                   .withColumn("price_lag_4h", window_4h) \
                   .withColumn("price_lag_24h", window_24h)

            # Calculate price changes
            df = df.withColumn("price_change_1h",
                              (F.col("price") - F.col("price_lag_1h")) / F.col("price_lag_1h") * 100)
            df = df.withColumn("price_change_4h",
                              (F.col("price") - F.col("price_lag_4h")) / F.col("price_lag_4h") * 100)
            df = df.withColumn("price_change_24h",
                              (F.col("price") - F.col("price_lag_24h")) / F.col("price_lag_24h") * 100)

            # Calculate volatility (rolling std dev)
            # Using window function for last 60 records
            from pyspark.sql.window import Window
            window_spec = Window.partitionBy("symbol").orderBy("timestamp").rowsBetween(-60, 0)
            df = df.withColumn("volatility", F.stddev("price").over(window_spec))

            # Volume features
            if "volume_24h" in df.columns:
                df = df.withColumn("volume_change",
                                  (F.col("volume_24h") - F.lag("volume_24h", 60).over(
                                      Window.partitionBy("symbol").orderBy("timestamp")
                                  )) / F.lag("volume_24h", 60).over(
                                      Window.partitionBy("symbol").orderBy("timestamp")
                                  ) * 100)

            # Drop rows with null features
            df = df.dropna(subset=["price_lag_1h", "price_lag_4h", "price_lag_24h", "volatility"])

            logger.info(f"Prepared features for {df.count()} records")
            return df

        except Exception as e:
            logger.error(f"Failed to prepare features: {e}")
            return df

    # ========================================
    # PRICE PREDICTION (Linear Regression)
    # ========================================

    def train_price_prediction_model(self, df: DataFrame, symbol: str = "BTC") -> Optional[PipelineModel]:
        """Train price prediction model using Linear Regression"""
        try:
            if not self.ml_config['price_prediction']['enabled']:
                logger.info("Price prediction disabled in config")
                return None

            logger.info(f"Training price prediction model for {symbol}...")
            start_time = time.time()

            # Filter for specific symbol
            df_symbol = df.filter(F.col("symbol") == symbol)

            # Prepare features
            df_symbol = self.prepare_crypto_features(df_symbol)

            # Create target variable (price 1 hour ahead)
            df_symbol = df_symbol.withColumn("price_1h_ahead",
                                            F.lead("price", 60).over(
                                                Window.partitionBy("symbol").orderBy("timestamp")
                                            ))
            df_symbol = df_symbol.dropna(subset=["price_1h_ahead"])

            # Feature columns
            feature_cols = [
                "price_lag_1h", "price_lag_4h", "price_lag_24h",
                "volatility", "price_change_1h", "price_change_4h"
            ]

            if "volume_24h" in df_symbol.columns:
                feature_cols.append("volume_24h")
                feature_cols.append("volume_change")

            # Remove rows with null features
            df_symbol = df_symbol.dropna(subset=feature_cols + ["price_1h_ahead"])

            # Split train/test
            train_ratio = self.ml_config['price_prediction'].get('train_test_split', 0.8)
            train_df, test_df = df_symbol.randomSplit([train_ratio, 1 - train_ratio], seed=42)

            # Build ML pipeline
            assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw")
            scaler = StandardScaler(inputCol="features_raw", outputCol="features", withMean=True, withStd=True)
            lr = LinearRegression(featuresCol="features", labelCol="price_1h_ahead", maxIter=100)

            pipeline = Pipeline(stages=[assembler, scaler, lr])

            # Train model
            model = pipeline.fit(train_df)

            # Evaluate
            predictions = model.transform(test_df)
            evaluator = RegressionEvaluator(labelCol="price_1h_ahead", predictionCol="prediction", metricName="rmse")
            rmse = evaluator.evaluate(predictions)
            evaluator.setMetricName("r2")
            r2 = evaluator.evaluate(predictions)

            elapsed = time.time() - start_time
            logger.info(f"✓ Price prediction model trained for {symbol} (RMSE: {rmse:.2f}, R²: {r2:.4f}, {elapsed:.2f}s)")

            return model

        except Exception as e:
            logger.error(f"Failed to train price prediction model: {e}")
            return None

    def predict_prices(self, model: PipelineModel, df: DataFrame, symbol: str = "BTC") -> Optional[DataFrame]:
        """Make price predictions using trained model"""
        try:
            # Filter and prepare features
            df_symbol = df.filter(F.col("symbol") == symbol)
            df_symbol = self.prepare_crypto_features(df_symbol)

            # Make predictions
            predictions = model.transform(df_symbol)

            # Select relevant columns
            result = predictions.select(
                "symbol", "timestamp", "price",
                "prediction", "features"
            )

            logger.info(f"Generated {result.count()} price predictions for {symbol}")
            return result

        except Exception as e:
            logger.error(f"Failed to make predictions: {e}")
            return None

    # ========================================
    # CLUSTERING (K-Means)
    # ========================================

    def perform_clustering(self, df: DataFrame, n_clusters: int = 5) -> Tuple[Optional[PipelineModel], Optional[DataFrame]]:
        """Cluster cryptocurrencies based on behavior patterns"""
        try:
            if not self.ml_config['clustering']['enabled']:
                logger.info("Clustering disabled in config")
                return None, None

            logger.info(f"Performing K-Means clustering (k={n_clusters})...")
            start_time = time.time()

            # Aggregate features per symbol
            agg_df = df.groupBy("symbol").agg(
                F.avg("price").alias("avg_price"),
                F.stddev("price").alias("price_volatility"),
                F.avg("volume_24h").alias("avg_volume"),
                F.max("market_cap").alias("market_cap")
            ).dropna()

            # Feature columns
            feature_cols = ["price_volatility", "avg_volume", "market_cap"]

            # Build ML pipeline
            assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw")
            scaler = StandardScaler(inputCol="features_raw", outputCol="features", withMean=True, withStd=True)
            kmeans = KMeans(k=n_clusters, seed=42, featuresCol="features", predictionCol="cluster")

            pipeline = Pipeline(stages=[assembler, scaler, kmeans])

            # Train model
            model = pipeline.fit(agg_df)

            # Make predictions
            clustered = model.transform(agg_df)

            # Evaluate
            evaluator = ClusteringEvaluator(featuresCol="features", metricName="silhouette")
            silhouette = evaluator.evaluate(clustered)

            elapsed = time.time() - start_time
            logger.info(f"✓ Clustering completed (silhouette: {silhouette:.4f}, {elapsed:.2f}s)")

            return model, clustered

        except Exception as e:
            logger.error(f"Failed to perform clustering: {e}")
            return None, None

    # ========================================
    # ANOMALY DETECTION (Isolation Forest approximation)
    # ========================================

    def detect_anomalies(self, df: DataFrame, contamination: float = 0.1) -> Optional[DataFrame]:
        """Detect price/volume anomalies using statistical methods"""
        try:
            if not self.ml_config['anomaly']['enabled']:
                logger.info("Anomaly detection disabled in config")
                return None

            logger.info("Detecting anomalies using z-score method...")
            start_time = time.time()

            # Calculate z-scores for price and volume changes
            from pyspark.sql.window import Window

            # Z-score for price changes
            price_stats = df.groupBy("symbol").agg(
                F.mean("price_change_1h").alias("price_mean"),
                F.stddev("price_change_1h").alias("price_std")
            )

            df = df.join(price_stats, on="symbol", how="left")
            df = df.withColumn("price_zscore",
                              (F.col("price_change_1h") - F.col("price_mean")) / F.col("price_std"))

            # Z-score for volume changes (if available)
            if "volume_change" in df.columns:
                volume_stats = df.groupBy("symbol").agg(
                    F.mean("volume_change").alias("volume_mean"),
                    F.stddev("volume_change").alias("volume_std")
                )
                df = df.join(volume_stats, on="symbol", how="left")
                df = df.withColumn("volume_zscore",
                                  (F.col("volume_change") - F.col("volume_mean")) / F.col("volume_std"))

                # Combined anomaly score
                df = df.withColumn("anomaly_score",
                                  (F.abs(F.col("price_zscore")) + F.abs(F.col("volume_zscore"))) / 2)
            else:
                df = df.withColumn("anomaly_score", F.abs(F.col("price_zscore")))

            # Flag anomalies (score > threshold)
            threshold = 3.0  # 3 standard deviations
            df = df.withColumn("is_anomaly", F.col("anomaly_score") > threshold)

            # Filter to anomalies only
            anomalies = df.filter(F.col("is_anomaly") == True) \
                         .select("symbol", "timestamp", "price", "price_change_1h",
                                "anomaly_score", "price_zscore")

            anomaly_count = anomalies.count()
            elapsed = time.time() - start_time
            logger.info(f"✓ Detected {anomaly_count} anomalies ({elapsed:.2f}s)")

            return anomalies

        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            return None

    # ========================================
    # MODEL PERSISTENCE
    # ========================================

    def save_model(self, model: PipelineModel, path: str) -> bool:
        """Save trained model to disk"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            model.write().overwrite().save(path)
            logger.info(f"✓ Model saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def load_model(self, path: str) -> Optional[PipelineModel]:
        """Load trained model from disk"""
        try:
            model = PipelineModel.load(path)
            logger.info(f"✓ Model loaded from {path}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None

    # ========================================
    # PERFORMANCE METRICS
    # ========================================

    def get_spark_metrics(self) -> Dict[str, Any]:
        """Get Spark performance metrics"""
        try:
            metrics = {}

            # Spark context info
            sc = self.spark.sparkContext
            metrics['app_id'] = sc.applicationId
            metrics['app_name'] = sc.appName
            metrics['master'] = sc.master
            metrics['executor_memory'] = sc.getConf().get("spark.executor.memory")
            metrics['executor_cores'] = sc.getConf().get("spark.executor.cores")

            # Active jobs/stages
            status = sc.statusTracker()
            metrics['active_jobs'] = len(status.getActiveJobIds())
            metrics['active_stages'] = len(status.getActiveStageIds())

            return metrics

        except Exception as e:
            logger.error(f"Failed to get Spark metrics: {e}")
            return {}


# Utility functions
def create_pipeline(config_path: str = "config/analytics_config.yaml") -> SparkMLPipeline:
    """Factory function to create Spark ML pipeline"""
    return SparkMLPipeline(config_path)


# Fix missing Window import
from pyspark.sql.window import Window
