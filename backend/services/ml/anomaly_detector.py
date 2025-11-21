#!/usr/bin/env python3
"""
Anomaly Detector Service
Real-time monitoring and management of detected anomalies
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from postgres_reader import PostgreSQLReader

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Service for handling anomaly detection and monitoring"""

    def __init__(self, postgres_reader: Optional[PostgreSQLReader] = None):
        """Initialize anomaly detector service"""
        self.pg_reader = postgres_reader or PostgreSQLReader()
        logger.info("Anomaly Detector Service initialized")

    def get_active_anomalies(
        self,
        severity_filter: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get currently active (unresolved) anomalies

        Args:
            severity_filter: Filter by severity ('low', 'medium', 'high', 'critical')
            symbol: Filter by cryptocurrency symbol
            limit: Maximum number of anomalies to return

        Returns:
            List of active anomalies
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            query = """
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
                FROM v_active_anomalies
                WHERE 1=1
            """
            params = []

            if severity_filter:
                query += " AND severity = %s"
                params.append(severity_filter)

            if symbol:
                query += " AND symbol = %s"
                params.append(symbol.upper())

            query += " ORDER BY severity DESC, detected_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            anomalies = cursor.fetchall()

            return [{
                'id': str(a['id']),
                'symbol': a['symbol'],
                'anomaly_type': a['anomaly_type'],
                'severity': a['severity'],
                'anomaly_score': float(a['anomaly_score']),
                'description': a['description'],
                'expected_value': float(a['expected_value']) if a['expected_value'] else None,
                'actual_value': float(a['actual_value']) if a['actual_value'] else None,
                'deviation': float(a['deviation']) if a['deviation'] else None,
                'detection_method': a['detection_method'],
                'detected_at': a['detected_at'].isoformat() if a['detected_at'] else None,
                'metadata': a['metadata']
            } for a in anomalies]

        except Exception as e:
            logger.error(f"Error getting active anomalies: {e}")
            return []
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def get_anomaly_history(
        self,
        symbol: Optional[str] = None,
        days: int = 7,
        include_resolved: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get historical anomalies

        Args:
            symbol: Filter by cryptocurrency symbol
            days: Number of days to look back
            include_resolved: Include resolved anomalies

        Returns:
            List of historical anomalies
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            cutoff = datetime.now() - timedelta(days=days)

            query = """
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
                    is_resolved,
                    resolved_at,
                    resolution_notes,
                    detected_at,
                    metadata
                FROM anomalies
                WHERE detected_at >= %s
            """
            params = [cutoff]

            if symbol:
                query += " AND symbol = %s"
                params.append(symbol.upper())

            if not include_resolved:
                query += " AND is_resolved = false"

            query += " ORDER BY detected_at DESC"

            cursor.execute(query, params)
            anomalies = cursor.fetchall()

            return [{
                'id': str(a['id']),
                'symbol': a['symbol'],
                'anomaly_type': a['anomaly_type'],
                'severity': a['severity'],
                'anomaly_score': float(a['anomaly_score']),
                'description': a['description'],
                'expected_value': float(a['expected_value']) if a['expected_value'] else None,
                'actual_value': float(a['actual_value']) if a['actual_value'] else None,
                'deviation': float(a['deviation']) if a['deviation'] else None,
                'detection_method': a['detection_method'],
                'is_resolved': a['is_resolved'],
                'resolved_at': a['resolved_at'].isoformat() if a['resolved_at'] else None,
                'resolution_notes': a['resolution_notes'],
                'detected_at': a['detected_at'].isoformat() if a['detected_at'] else None,
                'metadata': a['metadata']
            } for a in anomalies]

        except Exception as e:
            logger.error(f"Error getting anomaly history: {e}")
            return []
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def get_anomaly_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get anomaly detection statistics

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with statistics
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            cutoff = datetime.now() - timedelta(days=days)

            # Overall statistics
            cursor.execute("""
                SELECT
                    COUNT(*) as total_anomalies,
                    COUNT(CASE WHEN is_resolved THEN 1 END) as resolved_count,
                    COUNT(CASE WHEN is_resolved = false THEN 1 END) as active_count,
                    AVG(anomaly_score) as avg_score,
                    MAX(anomaly_score) as max_score
                FROM anomalies
                WHERE detected_at >= %s
            """, (cutoff,))

            overall = cursor.fetchone()

            # By severity
            cursor.execute("""
                SELECT
                    severity,
                    COUNT(*) as count,
                    AVG(anomaly_score) as avg_score
                FROM anomalies
                WHERE detected_at >= %s
                GROUP BY severity
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END
            """, (cutoff,))

            by_severity = cursor.fetchall()

            # By type
            cursor.execute("""
                SELECT
                    anomaly_type,
                    COUNT(*) as count
                FROM anomalies
                WHERE detected_at >= %s
                GROUP BY anomaly_type
                ORDER BY count DESC
            """, (cutoff,))

            by_type = cursor.fetchall()

            # By symbol
            cursor.execute("""
                SELECT
                    symbol,
                    COUNT(*) as count,
                    MAX(severity) as max_severity
                FROM anomalies
                WHERE detected_at >= %s
                GROUP BY symbol
                ORDER BY count DESC
                LIMIT 10
            """, (cutoff,))

            by_symbol = cursor.fetchall()

            # Detection rate over time (daily)
            cursor.execute("""
                SELECT
                    DATE(detected_at) as date,
                    COUNT(*) as count
                FROM anomalies
                WHERE detected_at >= %s
                GROUP BY DATE(detected_at)
                ORDER BY date DESC
            """, (cutoff,))

            daily_rate = cursor.fetchall()

            return {
                'period_days': days,
                'overall': {
                    'total_anomalies': overall['total_anomalies'],
                    'resolved_count': overall['resolved_count'],
                    'active_count': overall['active_count'],
                    'avg_score': float(overall['avg_score']) if overall['avg_score'] else 0,
                    'max_score': float(overall['max_score']) if overall['max_score'] else 0,
                    'resolution_rate': (overall['resolved_count'] / overall['total_anomalies'] * 100) if overall['total_anomalies'] > 0 else 0
                },
                'by_severity': [{
                    'severity': s['severity'],
                    'count': s['count'],
                    'avg_score': float(s['avg_score'])
                } for s in by_severity],
                'by_type': [{
                    'anomaly_type': t['anomaly_type'],
                    'count': t['count']
                } for t in by_type],
                'by_symbol': [{
                    'symbol': s['symbol'],
                    'count': s['count'],
                    'max_severity': s['max_severity']
                } for s in by_symbol],
                'daily_rate': [{
                    'date': d['date'].isoformat() if d['date'] else None,
                    'count': d['count']
                } for d in daily_rate]
            }

        except Exception as e:
            logger.error(f"Error getting anomaly statistics: {e}")
            return {
                'period_days': days,
                'error': str(e)
            }
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def resolve_anomaly(
        self,
        anomaly_id: str,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """
        Mark an anomaly as resolved

        Args:
            anomaly_id: UUID of the anomaly
            resolution_notes: Optional notes about the resolution

        Returns:
            True if successful
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE anomalies
                SET is_resolved = true,
                    resolved_at = %s,
                    resolution_notes = %s
                WHERE id = %s
            """, (datetime.now(), resolution_notes, anomaly_id))

            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Resolved anomaly {anomaly_id}")
                return True
            else:
                logger.warning(f"Anomaly {anomaly_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error resolving anomaly {anomaly_id}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.pg_reader.return_connection(conn)


# Singleton instance
_anomaly_detector = None


def get_anomaly_detector() -> AnomalyDetector:
    """Get singleton anomaly detector instance"""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector()
    return _anomaly_detector
