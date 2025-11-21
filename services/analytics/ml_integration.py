#!/usr/bin/env python3
"""
ML Integration Module
Connects Spark ML Pipeline outputs to PostgreSQL persistence
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from postgres_writer import PostgreSQLWriter

logger = logging.getLogger(__name__)


class MLIntegration:
    """
    Handles integration between Spark ML Pipeline and PostgreSQL
    Converts Spark DataFrame outputs to PostgreSQL records
    """

    def __init__(self, postgres_writer: Optional[PostgreSQLWriter] = None):
        """Initialize ML integration with PostgreSQL writer"""
        self.pg_writer = postgres_writer or PostgreSQLWriter()
        logger.info("ML Integration initialized")

    def save_predictions_to_postgres(
        self,
        predictions_df: DataFrame,
        symbol: str,
        rmse: float,
        r2_score: float,
        model_name: str = "LinearRegression",
        model_version: str = "1.0.0",
        prediction_horizon_hours: int = 1
    ) -> int:
        """
        Convert Spark DataFrame predictions to PostgreSQL records

        Args:
            predictions_df: Spark DataFrame with columns [symbol, timestamp, price, prediction]
            symbol: Cryptocurrency symbol
            rmse: Root Mean Squared Error of the model
            r2_score: R-squared score of the model
            model_name: Name of the ML model
            model_version: Version of the model
            prediction_horizon_hours: How many hours ahead the prediction is for

        Returns:
            Number of predictions saved
        """
        try:
            if predictions_df is None or predictions_df.count() == 0:
                logger.warning(f"No predictions to save for {symbol}")
                return 0

            # Convert to pandas for easier processing
            pandas_df = predictions_df.select(
                "symbol", "timestamp", "price", "prediction"
            ).toPandas()

            # Calculate confidence based on R² score
            confidence = min(max(r2_score, 0.0), 1.0)

            # Prepare batch data
            predictions_data = []
            for _, row in pandas_df.iterrows():
                # Calculate valid_until (prediction is valid for next X hours)
                predicted_at = row['timestamp']
                if isinstance(predicted_at, str):
                    predicted_at = pd.to_datetime(predicted_at)

                valid_until = predicted_at + timedelta(hours=prediction_horizon_hours)

                prediction_record = {
                    'symbol': symbol,
                    'prediction_type': 'price',
                    'predicted_value': float(row['prediction']),
                    'confidence': confidence,
                    'predicted_at': predicted_at,
                    'valid_until': valid_until,
                    'model_name': model_name,
                    'model_version': model_version,
                    'rmse': rmse,
                    'r2_score': r2_score,
                    'features_used': {
                        'price_lags': [1, 4, 24],
                        'volatility': True,
                        'volume': True
                    },
                    'metadata': {
                        'horizon_hours': prediction_horizon_hours,
                        'actual_price': float(row['price'])
                    }
                }
                predictions_data.append(prediction_record)

            # Batch write to PostgreSQL
            # Note: postgres_writer doesn't have batch method, so we'll write individually
            # TODO: Add batch method to postgres_writer for better performance
            saved_count = 0
            for pred in predictions_data:
                if self.pg_writer.write_ml_prediction(pred):
                    saved_count += 1

            logger.info(f"✓ Saved {saved_count}/{len(predictions_data)} predictions for {symbol}")
            return saved_count

        except Exception as e:
            logger.error(f"Failed to save predictions to PostgreSQL: {e}")
            return 0

    def save_anomalies_to_postgres(
        self,
        anomalies_df: DataFrame,
        detection_method: str = "z-score",
        threshold: float = 3.0
    ) -> int:
        """
        Convert Spark DataFrame anomalies to PostgreSQL records

        Args:
            anomalies_df: Spark DataFrame with columns [symbol, timestamp, price, price_change_1h, anomaly_score, price_zscore]
            detection_method: Method used for detection
            threshold: Threshold value used

        Returns:
            Number of anomalies saved
        """
        try:
            if anomalies_df is None or anomalies_df.count() == 0:
                logger.info("No anomalies detected")
                return 0

            # Convert to pandas
            pandas_df = anomalies_df.toPandas()

            # Prepare batch data
            anomalies_data = []
            for _, row in pandas_df.iterrows():
                # Determine anomaly type
                price_change = row.get('price_change_1h', 0)
                anomaly_type = 'price_spike' if price_change > 0 else 'price_drop'

                # Determine severity based on anomaly score
                score = abs(row['anomaly_score'])
                if score >= 5.0:
                    severity = 'critical'
                elif score >= 4.0:
                    severity = 'high'
                elif score >= 3.5:
                    severity = 'medium'
                else:
                    severity = 'low'

                # Calculate expected vs actual
                price_zscore = row.get('price_zscore', 0)
                actual_value = float(row['price'])
                # Rough estimate of expected value (reverse z-score calculation)
                # This is approximate - ideally we'd store mean/std from the model
                expected_value = None  # TODO: Calculate from stored statistics

                description = f"Detected {anomaly_type.replace('_', ' ')}: "
                if price_change:
                    description += f"{abs(price_change):.2f}% price change in 1 hour. "
                description += f"Anomaly score: {score:.2f} (threshold: {threshold})"

                anomaly_record = {
                    'symbol': row['symbol'],
                    'anomaly_type': anomaly_type,
                    'severity': severity,
                    'anomaly_score': float(score),
                    'description': description,
                    'expected_value': expected_value,
                    'actual_value': actual_value,
                    'deviation': float(price_zscore) if price_zscore else None,
                    'detection_method': detection_method,
                    'detected_at': row['timestamp'] if isinstance(row['timestamp'], datetime) else pd.to_datetime(row['timestamp']),
                    'metadata': {
                        'price_change_1h': float(price_change) if price_change else None,
                        'threshold_used': threshold
                    }
                }
                anomalies_data.append(anomaly_record)

            # Write to PostgreSQL
            saved_count = 0
            for anom in anomalies_data:
                if self.pg_writer.write_anomaly(anom):
                    saved_count += 1

            logger.info(f"✓ Saved {saved_count}/{len(anomalies_data)} anomalies")
            return saved_count

        except Exception as e:
            logger.error(f"Failed to save anomalies to PostgreSQL: {e}")
            return 0

    def save_clusters_to_postgres(
        self,
        clustered_df: DataFrame,
        silhouette_score: float,
        model_version: str = "1.0.0",
        num_clusters: int = 5
    ) -> int:
        """
        Convert Spark DataFrame cluster assignments to PostgreSQL records

        Args:
            clustered_df: Spark DataFrame with columns [symbol, avg_price, price_volatility, avg_volume, market_cap, cluster]
            silhouette_score: Overall silhouette score of clustering
            model_version: Version of the clustering model
            num_clusters: Number of clusters

        Returns:
            Number of cluster assignments saved
        """
        try:
            if clustered_df is None or clustered_df.count() == 0:
                logger.warning("No cluster assignments to save")
                return 0

            # Convert to pandas
            pandas_df = clustered_df.toPandas()

            # Define cluster labels based on characteristics
            cluster_labels = self._generate_cluster_labels(pandas_df)

            # Prepare batch data
            assignments_data = []
            for _, row in pandas_df.iterrows():
                cluster_id = int(row['cluster'])
                cluster_label = cluster_labels.get(cluster_id, f"Cluster {cluster_id}")

                assignment_record = {
                    'symbol': row['symbol'],
                    'cluster_id': cluster_id,
                    'cluster_label': cluster_label,
                    'distance_to_centroid': None,  # Spark KMeans doesn't provide this directly
                    'silhouette_score': silhouette_score,  # Overall score, not per-sample
                    'features_used': {
                        'price_volatility': True,
                        'avg_volume': True,
                        'market_cap': True
                    },
                    'feature_values': {
                        'avg_price': float(row.get('avg_price', 0)),
                        'price_volatility': float(row.get('price_volatility', 0)),
                        'avg_volume': float(row.get('avg_volume', 0)),
                        'market_cap': float(row.get('market_cap', 0))
                    },
                    'model_version': model_version,
                    'num_clusters': num_clusters,
                    'assigned_at': datetime.now(),
                    'metadata': {
                        'silhouette_score': silhouette_score
                    }
                }
                assignments_data.append(assignment_record)

            # Write to PostgreSQL using batch method
            saved_count = self.pg_writer.write_cluster_assignments_batch(assignments_data)

            logger.info(f"✓ Saved {saved_count}/{len(assignments_data)} cluster assignments")
            return saved_count

        except Exception as e:
            logger.error(f"Failed to save cluster assignments to PostgreSQL: {e}")
            return 0

    def save_correlations_to_postgres(
        self,
        correlations: Dict[Tuple[str, str], float],
        time_window: str = "7d",
        sample_size: Optional[int] = None,
        correlation_type: str = "pearson"
    ) -> int:
        """
        Save correlation matrix to PostgreSQL

        Args:
            correlations: Dictionary mapping (symbol1, symbol2) tuples to correlation coefficients
            time_window: Time window for correlation calculation
            sample_size: Number of samples used
            correlation_type: Type of correlation (pearson, spearman, kendall)

        Returns:
            Number of correlations saved
        """
        try:
            if not correlations:
                logger.info("No correlations to save")
                return 0

            # Prepare batch data
            correlations_data = []
            for (symbol1, symbol2), coeff in correlations.items():
                # Simple significance test: |r| > 0.5 is considered significant
                is_significant = abs(coeff) > 0.5

                correlation_record = {
                    'symbol_1': symbol1,
                    'symbol_2': symbol2,
                    'correlation_coefficient': float(coeff),
                    'correlation_type': correlation_type,
                    'time_window': time_window,
                    'sample_size': sample_size,
                    'p_value': None,  # TODO: Calculate p-value for significance
                    'is_significant': is_significant,
                    'calculated_at': datetime.now()
                }
                correlations_data.append(correlation_record)

            # Write to PostgreSQL using batch method
            saved_count = self.pg_writer.write_correlations_batch(correlations_data)

            logger.info(f"✓ Saved {saved_count}/{len(correlations_data)} correlations")
            return saved_count

        except Exception as e:
            logger.error(f"Failed to save correlations to PostgreSQL: {e}")
            return 0

    def _generate_cluster_labels(self, pandas_df: pd.DataFrame) -> Dict[int, str]:
        """
        Generate human-readable cluster labels based on cluster characteristics

        Args:
            pandas_df: Pandas DataFrame with cluster assignments and features

        Returns:
            Dictionary mapping cluster_id to label
        """
        labels = {}

        # Group by cluster and calculate characteristics
        cluster_stats = pandas_df.groupby('cluster').agg({
            'price_volatility': 'mean',
            'avg_volume': 'mean',
            'market_cap': 'mean'
        }).reset_index()

        # Determine labels based on characteristics
        for _, row in cluster_stats.iterrows():
            cluster_id = int(row['cluster'])
            volatility = row['price_volatility']
            market_cap = row['market_cap']

            # High/Low thresholds (these could be configured)
            high_volatility_threshold = pandas_df['price_volatility'].median()
            high_market_cap_threshold = pandas_df['market_cap'].median()

            if market_cap > high_market_cap_threshold:
                if volatility > high_volatility_threshold:
                    labels[cluster_id] = "High Cap Volatile"
                else:
                    labels[cluster_id] = "High Cap Stable"
            else:
                if volatility > high_volatility_threshold:
                    labels[cluster_id] = "Low Cap High Risk"
                else:
                    labels[cluster_id] = "Low Cap Stable"

        return labels

    def close(self):
        """Close PostgreSQL connections"""
        if self.pg_writer:
            self.pg_writer.close_all()
            logger.info("ML Integration closed")


# Convenience function
def get_ml_integration() -> MLIntegration:
    """Get ML integration instance"""
    return MLIntegration()
