#!/usr/bin/env python3
"""
Clustering Service
Provides cluster analysis and insights for cryptocurrency grouping
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from postgres_reader import PostgreSQLReader

logger = logging.getLogger(__name__)


class ClusteringService:
    """Service for handling cryptocurrency clustering analytics"""

    def __init__(self, postgres_reader: Optional[PostgreSQLReader] = None):
        """Initialize clustering service"""
        self.pg_reader = postgres_reader or PostgreSQLReader()
        logger.info("Clustering Service initialized")

    def get_cluster_insights(self, cluster_id: int) -> Dict[str, Any]:
        """
        Get insights for a specific cluster

        Args:
            cluster_id: Cluster ID to analyze

        Returns:
            Dictionary with cluster characteristics and crypto list
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            # Get all cryptos in this cluster
            cursor.execute("""
                SELECT
                    symbol,
                    cluster_label,
                    distance_to_centroid,
                    silhouette_score,
                    feature_values,
                    assigned_at
                FROM v_current_cluster_assignments
                WHERE cluster_id = %s
                ORDER BY symbol
            """, (cluster_id,))

            cryptos = cursor.fetchall()

            if not cryptos:
                return {
                    'cluster_id': cluster_id,
                    'cluster_label': f'Cluster {cluster_id}',
                    'crypto_count': 0,
                    'cryptos': [],
                    'characteristics': {}
                }

            # Extract cluster label from first result
            cluster_label = cryptos[0]['cluster_label'] if cryptos[0]['cluster_label'] else f'Cluster {cluster_id}'

            # Calculate cluster characteristics
            feature_values_list = [c['feature_values'] for c in cryptos if c['feature_values']]

            characteristics = {}
            if feature_values_list:
                # Calculate averages
                for key in feature_values_list[0].keys():
                    values = [fv.get(key, 0) for fv in feature_values_list if fv.get(key) is not None]
                    if values:
                        characteristics[key] = {
                            'avg': sum(values) / len(values),
                            'min': min(values),
                            'max': max(values)
                        }

            # Format crypto list
            crypto_list = [{
                'symbol': c['symbol'],
                'distance_to_centroid': float(c['distance_to_centroid']) if c['distance_to_centroid'] else None,
                'silhouette_score': float(c['silhouette_score']) if c['silhouette_score'] else None,
                'assigned_at': c['assigned_at'].isoformat() if c['assigned_at'] else None
            } for c in cryptos]

            return {
                'cluster_id': cluster_id,
                'cluster_label': cluster_label,
                'crypto_count': len(cryptos),
                'cryptos': crypto_list,
                'characteristics': characteristics,
                'avg_silhouette_score': sum(c['silhouette_score'] for c in cryptos if c['silhouette_score']) / len(cryptos) if cryptos else 0
            }

        except Exception as e:
            logger.error(f"Error getting cluster insights: {e}")
            return {
                'cluster_id': cluster_id,
                'error': str(e)
            }
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def get_similar_cryptos(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get cryptocurrencies similar to the given symbol (same cluster)

        Args:
            symbol: Cryptocurrency symbol
            limit: Maximum number of similar cryptos to return

        Returns:
            List of similar cryptocurrencies
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            # First, find the cluster of the given symbol
            cursor.execute("""
                SELECT cluster_id, cluster_label
                FROM v_current_cluster_assignments
                WHERE symbol = %s
            """, (symbol.upper(),))

            result = cursor.fetchone()
            if not result:
                return []

            cluster_id = result['cluster_id']
            cluster_label = result['cluster_label']

            # Get other cryptos in the same cluster
            cursor.execute("""
                SELECT
                    symbol,
                    distance_to_centroid,
                    silhouette_score,
                    feature_values
                FROM v_current_cluster_assignments
                WHERE cluster_id = %s AND symbol != %s
                ORDER BY distance_to_centroid ASC NULLS LAST
                LIMIT %s
            """, (cluster_id, symbol.upper(), limit))

            similar_cryptos = cursor.fetchall()

            return [{
                'symbol': c['symbol'],
                'cluster_id': cluster_id,
                'cluster_label': cluster_label,
                'distance_to_centroid': float(c['distance_to_centroid']) if c['distance_to_centroid'] else None,
                'silhouette_score': float(c['silhouette_score']) if c['silhouette_score'] else None,
                'similarity_reason': cluster_label
            } for c in similar_cryptos]

        except Exception as e:
            logger.error(f"Error getting similar cryptos for {symbol}: {e}")
            return []
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def get_cluster_statistics(self) -> Dict[str, Any]:
        """
        Get overall clustering statistics

        Returns:
            Dictionary with clustering statistics
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            # Get cluster distribution
            cursor.execute("""
                SELECT
                    cluster_id,
                    cluster_label,
                    COUNT(*) as crypto_count,
                    AVG(silhouette_score) as avg_silhouette
                FROM v_current_cluster_assignments
                GROUP BY cluster_id, cluster_label
                ORDER BY cluster_id
            """)

            clusters = cursor.fetchall()

            # Get total number of clustered cryptos
            cursor.execute("""
                SELECT COUNT(DISTINCT symbol) as total_cryptos
                FROM v_current_cluster_assignments
            """)

            total_cryptos = cursor.fetchone()['total_cryptos']

            # Get overall silhouette score
            cursor.execute("""
                SELECT AVG(silhouette_score) as overall_silhouette
                FROM v_current_cluster_assignments
            """)

            overall_silhouette = cursor.fetchone()['overall_silhouette']

            return {
                'total_cryptos': total_cryptos,
                'num_clusters': len(clusters),
                'overall_silhouette_score': float(overall_silhouette) if overall_silhouette else 0,
                'clusters': [{
                    'cluster_id': c['cluster_id'],
                    'cluster_label': c['cluster_label'],
                    'crypto_count': c['crypto_count'],
                    'avg_silhouette_score': float(c['avg_silhouette']) if c['avg_silhouette'] else 0
                } for c in clusters]
            }

        except Exception as e:
            logger.error(f"Error getting cluster statistics: {e}")
            return {
                'total_cryptos': 0,
                'num_clusters': 0,
                'clusters': [],
                'error': str(e)
            }
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def get_all_clusters(self) -> List[Dict[str, Any]]:
        """
        Get all current cluster assignments

        Returns:
            List of all cluster assignments
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    symbol,
                    cluster_id,
                    cluster_label,
                    distance_to_centroid,
                    silhouette_score,
                    feature_values,
                    assigned_at
                FROM v_current_cluster_assignments
                ORDER BY cluster_id, symbol
            """)

            assignments = cursor.fetchall()

            return [{
                'symbol': a['symbol'],
                'cluster_id': a['cluster_id'],
                'cluster_label': a['cluster_label'],
                'distance_to_centroid': float(a['distance_to_centroid']) if a['distance_to_centroid'] else None,
                'silhouette_score': float(a['silhouette_score']) if a['silhouette_score'] else None,
                'feature_values': a['feature_values'],
                'assigned_at': a['assigned_at'].isoformat() if a['assigned_at'] else None
            } for a in assignments]

        except Exception as e:
            logger.error(f"Error getting all clusters: {e}")
            return []
        finally:
            if conn:
                self.pg_reader.return_connection(conn)


# Singleton instance
_clustering_service = None


def get_clustering_service() -> ClusteringService:
    """Get singleton clustering service instance"""
    global _clustering_service
    if _clustering_service is None:
        _clustering_service = ClusteringService()
    return _clustering_service
