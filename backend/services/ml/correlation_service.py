#!/usr/bin/env python3
"""
Correlation Service
Provides correlation matrix and analysis for cryptocurrency pairs
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from postgres_reader import PostgreSQLReader

logger = logging.getLogger(__name__)


class CorrelationService:
    """Service for handling cryptocurrency correlation analysis"""

    def __init__(self, postgres_reader: Optional[PostgreSQLReader] = None):
        """Initialize correlation service"""
        self.pg_reader = postgres_reader or PostgreSQLReader()
        logger.info("Correlation Service initialized")

    def get_correlation_matrix(
        self,
        symbols: Optional[List[str]] = None,
        time_window: str = "7d",
        min_coefficient: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get correlation matrix for specified symbols

        Args:
            symbols: List of symbols (None for all available)
            time_window: Time window ('1d', '7d', '30d')
            min_coefficient: Minimum correlation coefficient to include

        Returns:
            Dictionary with correlation matrix data
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            # Build query
            query = """
                SELECT
                    symbol_1,
                    symbol_2,
                    correlation_coefficient,
                    correlation_type,
                    time_window,
                    sample_size,
                    is_significant,
                    calculated_at
                FROM v_correlation_matrix
                WHERE time_window = %s
            """
            params = [time_window]

            if min_coefficient is not None:
                query += " AND ABS(correlation_coefficient) >= %s"
                params.append(abs(min_coefficient))

            query += " ORDER BY calculated_at DESC"

            cursor.execute(query, params)
            correlations = cursor.fetchall()

            # Filter by symbols if provided
            if symbols:
                symbols_upper = [s.upper() for s in symbols]
                correlations = [
                    c for c in correlations
                    if c['symbol_1'] in symbols_upper and c['symbol_2'] in symbols_upper
                ]

            # Build matrix format
            # Get all unique symbols
            all_symbols = set()
            for c in correlations:
                all_symbols.add(c['symbol_1'])
                all_symbols.add(c['symbol_2'])

            all_symbols = sorted(list(all_symbols))

            # Create matrix
            matrix = {}
            for sym1 in all_symbols:
                matrix[sym1] = {}
                for sym2 in all_symbols:
                    if sym1 == sym2:
                        matrix[sym1][sym2] = 1.0
                    else:
                        matrix[sym1][sym2] = None

            # Fill matrix
            for c in correlations:
                sym1 = c['symbol_1']
                sym2 = c['symbol_2']
                coeff = float(c['correlation_coefficient'])

                matrix[sym1][sym2] = coeff
                matrix[sym2][sym1] = coeff  # Symmetric

            # Convert to list format for easier API consumption
            matrix_list = []
            for sym1 in all_symbols:
                row = {'symbol': sym1, 'correlations': {}}
                for sym2 in all_symbols:
                    row['correlations'][sym2] = matrix[sym1][sym2]
                matrix_list.append(row)

            return {
                'symbols': all_symbols,
                'time_window': time_window,
                'matrix': matrix_list,
                'correlation_count': len(correlations),
                'calculated_at': correlations[0]['calculated_at'].isoformat() if correlations else None
            }

        except Exception as e:
            logger.error(f"Error getting correlation matrix: {e}")
            return {
                'symbols': symbols or [],
                'time_window': time_window,
                'matrix': [],
                'error': str(e)
            }
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def get_top_correlations(
        self,
        symbol: str,
        limit: int = 10,
        time_window: str = "7d",
        positive_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get top correlations for a specific symbol

        Args:
            symbol: Cryptocurrency symbol
            limit: Maximum number of correlations to return
            time_window: Time window for correlations
            positive_only: Only return positive correlations

        Returns:
            List of top correlated pairs
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    symbol_1,
                    symbol_2,
                    correlation_coefficient,
                    correlation_type,
                    sample_size,
                    is_significant,
                    calculated_at
                FROM crypto_correlations
                WHERE time_window = %s
                  AND (symbol_1 = %s OR symbol_2 = %s)
            """
            params = [time_window, symbol.upper(), symbol.upper()]

            if positive_only:
                query += " AND correlation_coefficient > 0"

            query += """
                ORDER BY ABS(correlation_coefficient) DESC
                LIMIT %s
            """
            params.append(limit)

            cursor.execute(query, params)
            correlations = cursor.fetchall()

            result = []
            for c in correlations:
                # Determine the other symbol
                other_symbol = c['symbol_2'] if c['symbol_1'] == symbol.upper() else c['symbol_1']

                result.append({
                    'symbol': other_symbol,
                    'correlation_coefficient': float(c['correlation_coefficient']),
                    'correlation_strength': self._get_correlation_strength(c['correlation_coefficient']),
                    'correlation_type': c['correlation_type'],
                    'sample_size': c['sample_size'],
                    'is_significant': c['is_significant'],
                    'calculated_at': c['calculated_at'].isoformat() if c['calculated_at'] else None
                })

            return result

        except Exception as e:
            logger.error(f"Error getting top correlations for {symbol}: {e}")
            return []
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def get_inverse_correlations(
        self,
        symbol: str,
        limit: int = 10,
        time_window: str = "7d",
        min_coefficient: float = -0.5
    ) -> List[Dict[str, Any]]:
        """
        Get inverse (negative) correlations for hedging opportunities

        Args:
            symbol: Cryptocurrency symbol
            limit: Maximum number of correlations to return
            time_window: Time window for correlations
            min_coefficient: Minimum negative correlation (e.g., -0.5)

        Returns:
            List of inversely correlated pairs
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    symbol_1,
                    symbol_2,
                    correlation_coefficient,
                    correlation_type,
                    sample_size,
                    is_significant,
                    calculated_at
                FROM crypto_correlations
                WHERE time_window = %s
                  AND (symbol_1 = %s OR symbol_2 = %s)
                  AND correlation_coefficient < 0
                  AND correlation_coefficient >= %s
                ORDER BY correlation_coefficient ASC
                LIMIT %s
            """, (time_window, symbol.upper(), symbol.upper(), min_coefficient, limit))

            correlations = cursor.fetchall()

            result = []
            for c in correlations:
                # Determine the other symbol
                other_symbol = c['symbol_2'] if c['symbol_1'] == symbol.upper() else c['symbol_1']

                result.append({
                    'symbol': other_symbol,
                    'correlation_coefficient': float(c['correlation_coefficient']),
                    'correlation_strength': self._get_correlation_strength(c['correlation_coefficient']),
                    'hedging_potential': self._get_hedging_potential(c['correlation_coefficient']),
                    'correlation_type': c['correlation_type'],
                    'sample_size': c['sample_size'],
                    'is_significant': c['is_significant'],
                    'calculated_at': c['calculated_at'].isoformat() if c['calculated_at'] else None
                })

            return result

        except Exception as e:
            logger.error(f"Error getting inverse correlations for {symbol}: {e}")
            return []
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def get_correlation_statistics(self, time_window: str = "7d") -> Dict[str, Any]:
        """
        Get overall correlation statistics

        Args:
            time_window: Time window for statistics

        Returns:
            Dictionary with correlation statistics
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            # Get correlation counts by strength
            cursor.execute("""
                SELECT
                    COUNT(*) as total_correlations,
                    AVG(correlation_coefficient) as avg_correlation,
                    COUNT(CASE WHEN is_significant THEN 1 END) as significant_count,
                    COUNT(CASE WHEN correlation_coefficient > 0.7 THEN 1 END) as strong_positive,
                    COUNT(CASE WHEN correlation_coefficient > 0.3 AND correlation_coefficient <= 0.7 THEN 1 END) as moderate_positive,
                    COUNT(CASE WHEN correlation_coefficient < -0.7 THEN 1 END) as strong_negative,
                    COUNT(CASE WHEN correlation_coefficient < -0.3 AND correlation_coefficient >= -0.7 THEN 1 END) as moderate_negative,
                    COUNT(CASE WHEN ABS(correlation_coefficient) <= 0.3 THEN 1 END) as weak
                FROM crypto_correlations
                WHERE time_window = %s
            """, (time_window,))

            stats = cursor.fetchone()

            return {
                'time_window': time_window,
                'total_correlations': stats['total_correlations'],
                'avg_correlation': float(stats['avg_correlation']) if stats['avg_correlation'] else 0,
                'significant_count': stats['significant_count'],
                'by_strength': {
                    'strong_positive': stats['strong_positive'],
                    'moderate_positive': stats['moderate_positive'],
                    'weak': stats['weak'],
                    'moderate_negative': stats['moderate_negative'],
                    'strong_negative': stats['strong_negative']
                }
            }

        except Exception as e:
            logger.error(f"Error getting correlation statistics: {e}")
            return {
                'time_window': time_window,
                'error': str(e)
            }
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def _get_correlation_strength(self, coefficient: float) -> str:
        """Get correlation strength label"""
        abs_coeff = abs(coefficient)
        if abs_coeff >= 0.7:
            return "strong"
        elif abs_coeff >= 0.3:
            return "moderate"
        else:
            return "weak"

    def _get_hedging_potential(self, coefficient: float) -> str:
        """Get hedging potential label for negative correlations"""
        if coefficient >= -0.3:
            return "low"
        elif coefficient >= -0.7:
            return "moderate"
        else:
            return "high"


# Singleton instance
_correlation_service = None


def get_correlation_service() -> CorrelationService:
    """Get singleton correlation service instance"""
    global _correlation_service
    if _correlation_service is None:
        _correlation_service = CorrelationService()
    return _correlation_service
