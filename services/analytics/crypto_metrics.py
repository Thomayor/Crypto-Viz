"""
Crypto Metrics Calculator
Advanced technical indicators and financial metrics for cryptocurrency analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from kafka import KafkaProducer
import json

logger = logging.getLogger(__name__)


class CryptoMetrics:
    """
    Advanced technical indicators calculator for cryptocurrency data

    Implements:
    - Moving Averages (MA20, MA50, MA200)
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Trend detection and breakouts
    - Crypto correlations
    """

    def __init__(self, kafka_bootstrap_servers: str = "kafka:29092"):
        """Initialize crypto metrics calculator"""
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.producer = None
        logger.info("Crypto Metrics Calculator initialized")

    def _get_kafka_producer(self) -> KafkaProducer:
        """Lazy initialization of Kafka producer"""
        if self.producer is None:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type='snappy',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"Kafka producer initialized: {self.kafka_bootstrap_servers}")
        return self.producer

    # ========================================
    # MOVING AVERAGES
    # ========================================

    def calculate_moving_averages(self, df: pd.DataFrame, symbol: str = None) -> pd.DataFrame:
        """
        Calculate moving averages (MA20, MA50, MA200)

        Args:
            df: DataFrame with columns [symbol, timestamp, price]
            symbol: Optional symbol filter

        Returns:
            DataFrame with MA columns added
        """
        try:
            if symbol:
                df = df[df['symbol'] == symbol].copy()

            # Sort by timestamp
            df = df.sort_values('timestamp')

            # Calculate moving averages for each symbol
            results = []
            for sym in df['symbol'].unique():
                symbol_df = df[df['symbol'] == sym].copy()

                # MA20 (20-period moving average)
                symbol_df['ma20'] = symbol_df['price'].rolling(window=20, min_periods=1).mean()

                # MA50 (50-period moving average)
                symbol_df['ma50'] = symbol_df['price'].rolling(window=50, min_periods=1).mean()

                # MA200 (200-period moving average)
                symbol_df['ma200'] = symbol_df['price'].rolling(window=200, min_periods=1).mean()

                # Golden Cross / Death Cross signals
                symbol_df['golden_cross'] = (symbol_df['ma50'] > symbol_df['ma200']) & \
                                           (symbol_df['ma50'].shift(1) <= symbol_df['ma200'].shift(1))
                symbol_df['death_cross'] = (symbol_df['ma50'] < symbol_df['ma200']) & \
                                          (symbol_df['ma50'].shift(1) >= symbol_df['ma200'].shift(1))

                results.append(symbol_df)

            result_df = pd.concat(results, ignore_index=True)
            logger.info(f"Calculated moving averages for {len(result_df['symbol'].unique())} symbols")

            return result_df

        except Exception as e:
            logger.error(f"Failed to calculate moving averages: {e}")
            return df

    # ========================================
    # RSI (Relative Strength Index)
    # ========================================

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14, symbol: str = None) -> pd.DataFrame:
        """
        Calculate RSI (Relative Strength Index)

        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss

        Args:
            df: DataFrame with columns [symbol, timestamp, price]
            period: RSI period (default 14)
            symbol: Optional symbol filter

        Returns:
            DataFrame with RSI column added
        """
        try:
            if symbol:
                df = df[df['symbol'] == symbol].copy()

            df = df.sort_values('timestamp')

            results = []
            for sym in df['symbol'].unique():
                symbol_df = df[df['symbol'] == sym].copy()

                # Calculate price changes
                delta = symbol_df['price'].diff()

                # Separate gains and losses
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)

                # Calculate average gain and loss
                avg_gain = gain.rolling(window=period, min_periods=1).mean()
                avg_loss = loss.rolling(window=period, min_periods=1).mean()

                # Calculate RS and RSI
                rs = avg_gain / avg_loss.replace(0, np.nan)
                symbol_df['rsi'] = 100 - (100 / (1 + rs))

                # RSI signals
                symbol_df['rsi_oversold'] = symbol_df['rsi'] < 30  # Oversold
                symbol_df['rsi_overbought'] = symbol_df['rsi'] > 70  # Overbought

                results.append(symbol_df)

            result_df = pd.concat(results, ignore_index=True)
            logger.info(f"Calculated RSI for {len(result_df['symbol'].unique())} symbols (period={period})")

            return result_df

        except Exception as e:
            logger.error(f"Failed to calculate RSI: {e}")
            return df

    # ========================================
    # MACD (Moving Average Convergence Divergence)
    # ========================================

    def calculate_macd(self, df: pd.DataFrame,
                       fast_period: int = 12,
                       slow_period: int = 26,
                       signal_period: int = 9,
                       symbol: str = None) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        MACD Line = EMA(12) - EMA(26)
        Signal Line = EMA(9) of MACD Line
        MACD Histogram = MACD Line - Signal Line

        Args:
            df: DataFrame with columns [symbol, timestamp, price]
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line EMA period (default 9)
            symbol: Optional symbol filter

        Returns:
            DataFrame with MACD columns added
        """
        try:
            if symbol:
                df = df[df['symbol'] == symbol].copy()

            df = df.sort_values('timestamp')

            results = []
            for sym in df['symbol'].unique():
                symbol_df = df[df['symbol'] == sym].copy()

                # Calculate EMAs
                ema_fast = symbol_df['price'].ewm(span=fast_period, adjust=False).mean()
                ema_slow = symbol_df['price'].ewm(span=slow_period, adjust=False).mean()

                # MACD Line
                symbol_df['macd'] = ema_fast - ema_slow

                # Signal Line
                symbol_df['macd_signal'] = symbol_df['macd'].ewm(span=signal_period, adjust=False).mean()

                # MACD Histogram
                symbol_df['macd_histogram'] = symbol_df['macd'] - symbol_df['macd_signal']

                # MACD crossover signals
                symbol_df['macd_bullish_cross'] = (symbol_df['macd'] > symbol_df['macd_signal']) & \
                                                  (symbol_df['macd'].shift(1) <= symbol_df['macd_signal'].shift(1))
                symbol_df['macd_bearish_cross'] = (symbol_df['macd'] < symbol_df['macd_signal']) & \
                                                  (symbol_df['macd'].shift(1) >= symbol_df['macd_signal'].shift(1))

                results.append(symbol_df)

            result_df = pd.concat(results, ignore_index=True)
            logger.info(f"Calculated MACD for {len(result_df['symbol'].unique())} symbols")

            return result_df

        except Exception as e:
            logger.error(f"Failed to calculate MACD: {e}")
            return df

    # ========================================
    # TREND DETECTION
    # ========================================

    def detect_trends(self, df: pd.DataFrame,
                      lookback_period: int = 20,
                      symbol: str = None) -> pd.DataFrame:
        """
        Detect price trends using multiple indicators

        Trend detection based on:
        - Price vs MA20, MA50
        - RSI levels
        - MACD signals
        - Price momentum

        Args:
            df: DataFrame with technical indicators
            lookback_period: Period for trend analysis
            symbol: Optional symbol filter

        Returns:
            DataFrame with trend indicators
        """
        try:
            if symbol:
                df = df[df['symbol'] == symbol].copy()

            df = df.sort_values('timestamp')

            results = []
            for sym in df['symbol'].unique():
                symbol_df = df[df['symbol'] == sym].copy()

                # Price momentum
                symbol_df['price_change_pct'] = symbol_df['price'].pct_change(periods=lookback_period) * 100

                # Trend strength (based on MA alignment)
                symbol_df['trend_strength'] = 0
                if 'ma20' in symbol_df.columns and 'ma50' in symbol_df.columns:
                    # Bullish: price > MA20 > MA50
                    bullish = (symbol_df['price'] > symbol_df['ma20']) & \
                             (symbol_df['ma20'] > symbol_df['ma50'])
                    # Bearish: price < MA20 < MA50
                    bearish = (symbol_df['price'] < symbol_df['ma20']) & \
                             (symbol_df['ma20'] < symbol_df['ma50'])

                    symbol_df.loc[bullish, 'trend_strength'] = 1  # Bullish
                    symbol_df.loc[bearish, 'trend_strength'] = -1  # Bearish

                # Trend classification
                symbol_df['trend'] = 'neutral'
                symbol_df.loc[symbol_df['trend_strength'] > 0, 'trend'] = 'bullish'
                symbol_df.loc[symbol_df['trend_strength'] < 0, 'trend'] = 'bearish'

                results.append(symbol_df)

            result_df = pd.concat(results, ignore_index=True)
            logger.info(f"Detected trends for {len(result_df['symbol'].unique())} symbols")

            return result_df

        except Exception as e:
            logger.error(f"Failed to detect trends: {e}")
            return df

    # ========================================
    # BREAKOUT DETECTION
    # ========================================

    def detect_breakouts(self, df: pd.DataFrame,
                        resistance_period: int = 20,
                        volume_threshold: float = 1.5,
                        symbol: str = None) -> pd.DataFrame:
        """
        Detect price breakouts above resistance or below support

        Breakout signals:
        - Price breaks above recent high with volume confirmation
        - Price breaks below recent low with volume confirmation

        Args:
            df: DataFrame with price and volume data
            resistance_period: Period for resistance/support calculation
            volume_threshold: Volume multiplier for confirmation
            symbol: Optional symbol filter

        Returns:
            DataFrame with breakout signals
        """
        try:
            if symbol:
                df = df[df['symbol'] == symbol].copy()

            df = df.sort_values('timestamp')

            results = []
            for sym in df['symbol'].unique():
                symbol_df = df[df['symbol'] == sym].copy()

                # Calculate resistance and support levels
                symbol_df['resistance'] = symbol_df['price'].rolling(window=resistance_period, min_periods=1).max()
                symbol_df['support'] = symbol_df['price'].rolling(window=resistance_period, min_periods=1).min()

                # Volume confirmation (if volume column exists)
                if 'volume_24h' in symbol_df.columns:
                    avg_volume = symbol_df['volume_24h'].rolling(window=resistance_period, min_periods=1).mean()
                    symbol_df['high_volume'] = symbol_df['volume_24h'] > (avg_volume * volume_threshold)
                else:
                    symbol_df['high_volume'] = False

                # Breakout signals
                symbol_df['breakout_up'] = (symbol_df['price'] > symbol_df['resistance'].shift(1)) & \
                                          (symbol_df['high_volume'])
                symbol_df['breakout_down'] = (symbol_df['price'] < symbol_df['support'].shift(1)) & \
                                            (symbol_df['high_volume'])

                results.append(symbol_df)

            result_df = pd.concat(results, ignore_index=True)
            breakouts_up = result_df['breakout_up'].sum()
            breakouts_down = result_df['breakout_down'].sum()
            logger.info(f"Detected breakouts: {breakouts_up} up, {breakouts_down} down")

            return result_df

        except Exception as e:
            logger.error(f"Failed to detect breakouts: {e}")
            return df

    # ========================================
    # CRYPTO CORRELATIONS
    # ========================================

    def calculate_correlations(self, df: pd.DataFrame,
                               method: str = 'pearson',
                               min_periods: int = 30) -> pd.DataFrame:
        """
        Calculate correlations between cryptocurrencies

        Args:
            df: DataFrame with columns [symbol, timestamp, price]
            method: Correlation method ('pearson', 'kendall', 'spearman')
            min_periods: Minimum number of observations required

        Returns:
            DataFrame with correlation matrix
        """
        try:
            # Pivot data to have symbols as columns
            price_matrix = df.pivot_table(
                index='timestamp',
                columns='symbol',
                values='price',
                aggfunc='last'
            )

            # Calculate correlation matrix
            correlation_matrix = price_matrix.corr(method=method, min_periods=min_periods)

            # Convert to long format for easier analysis
            correlations = []
            symbols = correlation_matrix.columns
            for i, sym1 in enumerate(symbols):
                for sym2 in symbols[i+1:]:  # Only upper triangle to avoid duplicates
                    corr_value = correlation_matrix.loc[sym1, sym2]
                    if not pd.isna(corr_value):
                        correlations.append({
                            'symbol1': sym1,
                            'symbol2': sym2,
                            'correlation': round(corr_value, 4),
                            'correlation_strength': self._classify_correlation(corr_value),
                            'timestamp': datetime.now().isoformat()
                        })

            result_df = pd.DataFrame(correlations)
            logger.info(f"Calculated {len(result_df)} correlation pairs using {method} method")

            return result_df

        except Exception as e:
            logger.error(f"Failed to calculate correlations: {e}")
            return pd.DataFrame()

    def _classify_correlation(self, corr: float) -> str:
        """Classify correlation strength"""
        abs_corr = abs(corr)
        if abs_corr >= 0.8:
            return 'very_strong'
        elif abs_corr >= 0.6:
            return 'strong'
        elif abs_corr >= 0.4:
            return 'moderate'
        elif abs_corr >= 0.2:
            return 'weak'
        else:
            return 'very_weak'

    # ========================================
    # COMPLETE METRICS CALCULATION
    # ========================================

    def calculate_all_metrics(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Calculate all technical indicators for crypto data

        Args:
            df: DataFrame with columns [symbol, timestamp, price, volume_24h]

        Returns:
            Dictionary with all calculated metrics
        """
        try:
            logger.info(f"Calculating all metrics for {len(df)} price records")

            # Calculate all indicators
            df_with_ma = self.calculate_moving_averages(df)
            df_with_rsi = self.calculate_rsi(df_with_ma)
            df_with_macd = self.calculate_macd(df_with_rsi)
            df_with_trends = self.detect_trends(df_with_macd)
            df_with_breakouts = self.detect_breakouts(df_with_trends)

            # Calculate correlations
            correlations = self.calculate_correlations(df)

            results = {
                'metrics': df_with_breakouts,
                'correlations': correlations
            }

            logger.info(f"✓ Calculated all metrics for {len(df_with_breakouts['symbol'].unique())} symbols")

            return results

        except Exception as e:
            logger.error(f"Failed to calculate all metrics: {e}")
            return {'metrics': df, 'correlations': pd.DataFrame()}

    # ========================================
    # KAFKA PUBLISHING
    # ========================================

    def publish_to_kafka(self, metrics: Dict[str, pd.DataFrame],
                        topic_prefix: str = 'crypto') -> Dict[str, int]:
        """
        Publish calculated metrics to Kafka

        Args:
            metrics: Dictionary with metrics and correlations DataFrames
            topic_prefix: Prefix for Kafka topics

        Returns:
            Dictionary with counts of published messages per topic
        """
        try:
            producer = self._get_kafka_producer()
            published_counts = {}

            # Publish metrics
            if 'metrics' in metrics and not metrics['metrics'].empty:
                df_metrics = metrics['metrics']

                # Get latest metrics per symbol
                latest_metrics = df_metrics.sort_values('timestamp').groupby('symbol').tail(1)

                for _, row in latest_metrics.iterrows():
                    message = {
                        'symbol': row['symbol'],
                        'timestamp': row['timestamp'].isoformat() if pd.notna(row['timestamp']) else None,
                        'price': float(row['price']) if pd.notna(row['price']) else None,
                        'ma20': float(row['ma20']) if 'ma20' in row and pd.notna(row['ma20']) else None,
                        'ma50': float(row['ma50']) if 'ma50' in row and pd.notna(row['ma50']) else None,
                        'ma200': float(row['ma200']) if 'ma200' in row and pd.notna(row['ma200']) else None,
                        'rsi': float(row['rsi']) if 'rsi' in row and pd.notna(row['rsi']) else None,
                        'rsi_oversold': bool(row['rsi_oversold']) if 'rsi_oversold' in row else False,
                        'rsi_overbought': bool(row['rsi_overbought']) if 'rsi_overbought' in row else False,
                        'macd': float(row['macd']) if 'macd' in row and pd.notna(row['macd']) else None,
                        'macd_signal': float(row['macd_signal']) if 'macd_signal' in row and pd.notna(row['macd_signal']) else None,
                        'macd_histogram': float(row['macd_histogram']) if 'macd_histogram' in row and pd.notna(row['macd_histogram']) else None,
                        'trend': str(row['trend']) if 'trend' in row else 'neutral',
                        'trend_strength': int(row['trend_strength']) if 'trend_strength' in row else 0,
                        'breakout_up': bool(row['breakout_up']) if 'breakout_up' in row else False,
                        'breakout_down': bool(row['breakout_down']) if 'breakout_down' in row else False
                    }

                    producer.send(f'{topic_prefix}-metrics', value=message)

                published_counts[f'{topic_prefix}-metrics'] = len(latest_metrics)
                logger.info(f"Published {len(latest_metrics)} metrics to {topic_prefix}-metrics")

            # Publish correlations
            if 'correlations' in metrics and not metrics['correlations'].empty:
                df_corr = metrics['correlations']

                for _, row in df_corr.iterrows():
                    message = {
                        'symbol1': row['symbol1'],
                        'symbol2': row['symbol2'],
                        'correlation': float(row['correlation']),
                        'correlation_strength': row['correlation_strength'],
                        'timestamp': row['timestamp']
                    }

                    producer.send(f'{topic_prefix}-correlations', value=message)

                published_counts[f'{topic_prefix}-correlations'] = len(df_corr)
                logger.info(f"Published {len(df_corr)} correlations to {topic_prefix}-correlations")

            producer.flush()

            return published_counts

        except Exception as e:
            logger.error(f"Failed to publish to Kafka: {e}")
            return {}

    # ========================================
    # MOMENTUM SCORING
    # ========================================

    def calculate_momentum_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate custom momentum score combining multiple indicators

        Momentum components:
        - RSI score (0-100 normalized)
        - MACD score (signal strength)
        - Volume score (relative to average)
        - Trend score (from moving averages)

        Args:
            df: DataFrame with calculated indicators (RSI, MACD, MA, volume)

        Returns:
            DataFrame with momentum scores added
        """
        try:
            # Ensure required columns exist
            required_cols = ['rsi', 'macd_histogram', 'volume_24h', 'ma20', 'ma50', 'ma200']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"Missing columns for momentum calculation: {missing_cols}")
                return df

            results = []
            for symbol in df['symbol'].unique():
                symbol_df = df[df['symbol'] == symbol].copy().sort_values('timestamp')

                # Skip if not enough data
                if len(symbol_df) < 50:
                    continue

                # 1. RSI Score (0-25 points)
                # Oversold (0-30): score 5-10, Neutral (30-70): score 10-20, Overbought (70-100): score 15-25
                symbol_df['rsi_score'] = symbol_df['rsi'].apply(lambda x:
                    5 + (x / 30 * 5) if x <= 30 else  # Oversold
                    (10 + ((x - 30) / 40 * 10)) if x <= 70 else  # Neutral
                    (15 + ((x - 70) / 30 * 10))  # Overbought
                )

                # 2. MACD Score (0-30 points)
                # Based on histogram strength and whether MACD is above/below signal
                max_histogram = symbol_df['macd_histogram'].abs().max()
                if max_histogram > 0:
                    symbol_df['macd_score'] = symbol_df['macd_histogram'].apply(lambda x:
                        15 + (x / max_histogram * 15) if x > 0 else
                        15 + (x / max_histogram * 15)
                    )
                else:
                    symbol_df['macd_score'] = 15.0

                # 3. Volume Score (0-25 points)
                # Relative volume compared to average
                avg_volume = symbol_df['volume_24h'].rolling(window=50, min_periods=1).mean()
                symbol_df['volume_ratio'] = symbol_df['volume_24h'] / avg_volume
                symbol_df['volume_score'] = symbol_df['volume_ratio'].apply(lambda x:
                    min(x * 12.5, 25.0)  # Cap at 25 points
                )

                # 4. Trend Score (0-20 points)
                # Based on moving average alignment
                symbol_df['trend_score'] = 10.0  # Default neutral
                # Bullish: MA20 > MA50 > MA200
                bullish = (symbol_df['ma20'] > symbol_df['ma50']) & (symbol_df['ma50'] > symbol_df['ma200'])
                symbol_df.loc[bullish, 'trend_score'] = 20.0
                # Bearish: MA20 < MA50 < MA200
                bearish = (symbol_df['ma20'] < symbol_df['ma50']) & (symbol_df['ma50'] < symbol_df['ma200'])
                symbol_df.loc[bearish, 'trend_score'] = 5.0
                # Mixed: partial alignment
                mixed = ~(bullish | bearish)
                symbol_df.loc[mixed, 'trend_score'] = 12.0

                # 5. Total Momentum Score (0-100)
                symbol_df['total_momentum_score'] = (
                    symbol_df['rsi_score'] * 0.25 +
                    symbol_df['macd_score'] * 0.30 +
                    symbol_df['volume_score'] * 0.25 +
                    symbol_df['trend_score'] * 0.20
                ).clip(0, 100)

                # 6. Momentum Label
                symbol_df['momentum_label'] = pd.cut(
                    symbol_df['total_momentum_score'],
                    bins=[0, 20, 40, 60, 80, 100],
                    labels=['very_bearish', 'bearish', 'neutral', 'bullish', 'very_bullish'],
                    include_lowest=True
                )

                # 7. Recommendation
                symbol_df['recommendation'] = symbol_df['total_momentum_score'].apply(lambda x:
                    'strong_sell' if x <= 20 else
                    'sell' if x <= 40 else
                    'hold' if x <= 60 else
                    'buy' if x <= 80 else
                    'strong_buy'
                )

                # 8. Confidence (based on data quality and consistency)
                # Higher confidence if all indicators align
                signal_alignment = (
                    (symbol_df['rsi_score'] > 15) == (symbol_df['macd_score'] > 15)
                ).astype(float)
                symbol_df['confidence'] = (
                    0.5 + (signal_alignment * 0.3) +
                    (symbol_df['volume_ratio'].clip(0, 2) / 2 * 0.2)
                ).clip(0, 1)

                results.append(symbol_df)

            if results:
                result_df = pd.concat(results, ignore_index=True)
                logger.info(f"✓ Calculated momentum scores for {len(result_df['symbol'].unique())} symbols")
                return result_df
            else:
                logger.warning("No momentum scores calculated")
                return df

        except Exception as e:
            logger.error(f"Failed to calculate momentum scores: {e}")
            return df

    def publish_momentum_scores_to_postgres(self, df: pd.DataFrame, postgres_writer=None) -> int:
        """
        Publish momentum scores to PostgreSQL

        Args:
            df: DataFrame with momentum scores
            postgres_writer: PostgreSQLWriter instance (optional)

        Returns:
            Number of momentum scores saved
        """
        try:
            if postgres_writer is None:
                from postgres_writer import PostgreSQLWriter
                postgres_writer = PostgreSQLWriter()

            # Get latest momentum score per symbol
            latest_momentum = df.sort_values('timestamp').groupby('symbol').tail(1)

            saved_count = 0
            for _, row in latest_momentum.iterrows():
                momentum_data = {
                    'symbol': row['symbol'],
                    'rsi_score': float(row['rsi_score']),
                    'macd_score': float(row['macd_score']),
                    'volume_score': float(row['volume_score']),
                    'trend_score': float(row['trend_score']),
                    'total_momentum_score': float(row['total_momentum_score']),
                    'momentum_label': str(row['momentum_label']),
                    'recommendation': str(row['recommendation']),
                    'confidence': float(row['confidence']),
                    'calculated_at': row['timestamp'] if isinstance(row['timestamp'], datetime) else pd.to_datetime(row['timestamp']),
                    'metadata': {
                        'rsi': float(row['rsi']),
                        'macd_histogram': float(row['macd_histogram']),
                        'volume_ratio': float(row.get('volume_ratio', 1.0)),
                        'price': float(row['price'])
                    }
                }

                if postgres_writer.write_momentum_score(momentum_data):
                    saved_count += 1

            logger.info(f"✓ Saved {saved_count} momentum scores to PostgreSQL")
            return saved_count

        except Exception as e:
            logger.error(f"Failed to publish momentum scores to PostgreSQL: {e}")
            return 0

    def close(self):
        """Close Kafka producer connection"""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")
