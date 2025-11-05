"""
Módulo de análisis técnico con indicadores de Fibonacci,
medias móviles, RSI, MACD y análisis de patrones.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class TechnicalAnalysis:
    """Clase para realizar análisis técnico de activos."""

    def __init__(self, data: pd.DataFrame):
        """
        Inicializa el análisis técnico.

        Args:
            data: DataFrame con datos históricos (debe incluir columnas: Open, High, Low, Close, Volume)
        """
        self.data = data.copy()
        self._calculate_all_indicators()

    def _calculate_all_indicators(self):
        """Calcula todos los indicadores técnicos disponibles."""
        if self.data.empty:
            return

        self._calculate_moving_averages()
        self._calculate_rsi()
        self._calculate_macd()
        self._calculate_bollinger_bands()
        self._calculate_volatility()

    def _calculate_moving_averages(self):
        """Calcula medias móviles simples y exponenciales."""
        if 'Close' not in self.data.columns:
            return

        # Medias móviles simples (SMA)
        self.data['SMA_10'] = self.data['Close'].rolling(window=10).mean()
        self.data['SMA_20'] = self.data['Close'].rolling(window=20).mean()
        self.data['SMA_50'] = self.data['Close'].rolling(window=50).mean()

        # Medias móviles exponenciales (EMA)
        self.data['EMA_10'] = self.data['Close'].ewm(span=10, adjust=False).mean()
        self.data['EMA_20'] = self.data['Close'].ewm(span=20, adjust=False).mean()

    def _calculate_rsi(self, period: int = 14):
        """
        Calcula el Índice de Fuerza Relativa (RSI).

        Args:
            period: Período para el cálculo del RSI
        """
        if 'Close' not in self.data.columns or len(self.data) < period:
            return

        delta = self.data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        self.data['RSI'] = 100 - (100 / (1 + rs))

    def _calculate_macd(self, fast=12, slow=26, signal=9):
        """
        Calcula el MACD (Moving Average Convergence Divergence).

        Args:
            fast: Período rápido
            slow: Período lento
            signal: Período de señal
        """
        if 'Close' not in self.data.columns:
            return

        exp1 = self.data['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = self.data['Close'].ewm(span=slow, adjust=False).mean()

        self.data['MACD'] = exp1 - exp2
        self.data['MACD_Signal'] = self.data['MACD'].ewm(span=signal, adjust=False).mean()
        self.data['MACD_Hist'] = self.data['MACD'] - self.data['MACD_Signal']

    def _calculate_bollinger_bands(self, period: int = 20, std_dev: int = 2):
        """
        Calcula las Bandas de Bollinger.

        Args:
            period: Período para el cálculo
            std_dev: Número de desviaciones estándar
        """
        if 'Close' not in self.data.columns:
            return

        self.data['BB_Middle'] = self.data['Close'].rolling(window=period).mean()
        std = self.data['Close'].rolling(window=period).std()
        self.data['BB_Upper'] = self.data['BB_Middle'] + (std * std_dev)
        self.data['BB_Lower'] = self.data['BB_Middle'] - (std * std_dev)

    def _calculate_volatility(self, period: int = 20):
        """
        Calcula la volatilidad histórica.

        Args:
            period: Período para el cálculo
        """
        if 'Close' not in self.data.columns:
            return

        log_returns = np.log(self.data['Close'] / self.data['Close'].shift(1))
        self.data['Volatility'] = log_returns.rolling(window=period).std() * np.sqrt(period)

    def calculate_fibonacci_levels(self, period: str = '1mo') -> Dict[str, float]:
        """
        Calcula los niveles de retroceso de Fibonacci.

        Args:
            period: Período para calcular niveles ('1d', '1wk', '1mo', etc.)

        Returns:
            Diccionario con niveles de Fibonacci
        """
        if self.data.empty:
            return {}

        # Obtener el máximo y mínimo del período
        high = float(self.data['High'].max())
        low = float(self.data['Low'].min())
        diff = high - low

        # Niveles de Fibonacci estándar
        levels = {
            'high': high,
            'fibonacci_0.236': high - (diff * 0.236),
            'fibonacci_0.382': high - (diff * 0.382),
            'fibonacci_0.500': high - (diff * 0.500),
            'fibonacci_0.618': high - (diff * 0.618),
            'fibonacci_0.786': high - (diff * 0.786),
            'low': low,
            # Extensiones de Fibonacci
            'fibonacci_1.272': high + (diff * 0.272),
            'fibonacci_1.618': high + (diff * 0.618),
        }

        return levels

    def get_current_trend(self) -> str:
        """
        Determina la tendencia actual basada en medias móviles.

        Returns:
            'BULLISH', 'BEARISH' o 'NEUTRAL'
        """
        if self.data.empty or len(self.data) < 50:
            return 'NEUTRAL'

        try:
            last_row = self.data.iloc[-1]
            close = last_row['Close']

            # Usar múltiples medias móviles para determinar tendencia
            sma_10 = last_row.get('SMA_10', close)
            sma_20 = last_row.get('SMA_20', close)
            sma_50 = last_row.get('SMA_50', close)

            # Tendencia alcista: precio por encima de las MAs y MAs en orden ascendente
            if close > sma_10 > sma_20 > sma_50:
                return 'BULLISH'

            # Tendencia bajista: precio por debajo de las MAs y MAs en orden descendente
            if close < sma_10 < sma_20 < sma_50:
                return 'BEARISH'

            return 'NEUTRAL'

        except Exception as e:
            print(f"Error determinando tendencia: {e}")
            return 'NEUTRAL'

    def get_support_resistance(self) -> Tuple[float, float]:
        """
        Identifica niveles de soporte y resistencia.

        Returns:
            Tupla (soporte, resistencia)
        """
        if self.data.empty:
            return (0.0, 0.0)

        try:
            # Usar mínimos y máximos recientes
            recent_data = self.data.tail(50)

            support = float(recent_data['Low'].min())
            resistance = float(recent_data['High'].max())

            return (support, resistance)

        except Exception as e:
            print(f"Error calculando soporte/resistencia: {e}")
            return (0.0, 0.0)

    def get_trading_signals(self) -> Dict[str, any]:
        """
        Genera señales de trading basadas en todos los indicadores.

        Returns:
            Diccionario con señales y su justificación
        """
        if self.data.empty or len(self.data) < 2:
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reasons': ['Datos insuficientes']
            }

        signals = []
        reasons = []

        try:
            current = self.data.iloc[-1]
            previous = self.data.iloc[-2]

            # 1. Señal de Media Móvil
            if 'SMA_10' in current and 'SMA_20' in current:
                if current['SMA_10'] > current['SMA_20'] and previous['SMA_10'] <= previous['SMA_20']:
                    signals.append('BUY')
                    reasons.append('Cruce alcista de medias móviles (Golden Cross)')
                elif current['SMA_10'] < current['SMA_20'] and previous['SMA_10'] >= previous['SMA_20']:
                    signals.append('SELL')
                    reasons.append('Cruce bajista de medias móviles (Death Cross)')

            # 2. Señal de RSI
            if 'RSI' in current:
                rsi = current['RSI']
                if rsi < 30:
                    signals.append('BUY')
                    reasons.append(f'RSI en sobreventa ({rsi:.2f})')
                elif rsi > 70:
                    signals.append('SELL')
                    reasons.append(f'RSI en sobrecompra ({rsi:.2f})')

            # 3. Señal de MACD
            if 'MACD' in current and 'MACD_Signal' in current:
                if current['MACD'] > current['MACD_Signal'] and previous['MACD'] <= previous['MACD_Signal']:
                    signals.append('BUY')
                    reasons.append('Cruce alcista de MACD')
                elif current['MACD'] < current['MACD_Signal'] and previous['MACD'] >= previous['MACD_Signal']:
                    signals.append('SELL')
                    reasons.append('Cruce bajista de MACD')

            # 4. Señal de Bollinger Bands
            if 'BB_Upper' in current and 'BB_Lower' in current:
                price = current['Close']
                if price <= current['BB_Lower']:
                    signals.append('BUY')
                    reasons.append('Precio tocó banda inferior de Bollinger')
                elif price >= current['BB_Upper']:
                    signals.append('SELL')
                    reasons.append('Precio tocó banda superior de Bollinger')

            # 5. Señal de Tendencia
            trend = self.get_trend_strength()
            if trend > 0.7:
                signals.append('BUY')
                reasons.append(f'Tendencia alcista fuerte ({trend:.2%})')
            elif trend < -0.7:
                signals.append('SELL')
                reasons.append(f'Tendencia bajista fuerte ({abs(trend):.2%})')

            # Determinar acción final
            buy_signals = signals.count('BUY')
            sell_signals = signals.count('SELL')

            if buy_signals > sell_signals and buy_signals >= 2:
                action = 'BUY'
                confidence = min(100, buy_signals * 25)
            elif sell_signals > buy_signals and sell_signals >= 2:
                action = 'SELL'
                confidence = min(100, sell_signals * 25)
            else:
                action = 'HOLD'
                confidence = 50

            return {
                'action': action,
                'confidence': confidence,
                'reasons': reasons if reasons else ['Sin señales claras']
            }

        except Exception as e:
            print(f"Error generando señales: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reasons': [f'Error: {str(e)}']
            }

    def get_trend_strength(self) -> float:
        """
        Calcula la fuerza de la tendencia.

        Returns:
            Valor entre -1 (bajista fuerte) y 1 (alcista fuerte)
        """
        if self.data.empty or len(self.data) < 20:
            return 0.0

        try:
            # Usar la pendiente de la media móvil como indicador de fuerza
            sma_20 = self.data['SMA_20'].tail(20).values

            if len(sma_20) < 20 or np.any(np.isnan(sma_20)):
                return 0.0

            # Calcular la pendiente normalizada
            x = np.arange(len(sma_20))
            slope = np.polyfit(x, sma_20, 1)[0]

            # Normalizar la pendiente
            price_range = sma_20[-1] if sma_20[-1] != 0 else 1
            normalized_slope = (slope / price_range) * 100

            # Limitar entre -1 y 1
            return max(-1.0, min(1.0, normalized_slope))

        except Exception as e:
            print(f"Error calculando fuerza de tendencia: {e}")
            return 0.0

    def get_analysis_summary(self) -> Dict[str, any]:
        """
        Obtiene un resumen completo del análisis técnico.

        Returns:
            Diccionario con resumen del análisis
        """
        if self.data.empty:
            return {}

        try:
            current = self.data.iloc[-1]
            fibonacci_levels = self.calculate_fibonacci_levels()
            support, resistance = self.get_support_resistance()
            signals = self.get_trading_signals()

            summary = {
                'price': float(current['Close']),
                'trend': self.get_current_trend(),
                'trend_strength': self.get_trend_strength(),
                'rsi': float(current.get('RSI', 0)),
                'macd': float(current.get('MACD', 0)),
                'macd_signal': float(current.get('MACD_Signal', 0)),
                'volatility': float(current.get('Volatility', 0)),
                'support': support,
                'resistance': resistance,
                'fibonacci_levels': fibonacci_levels,
                'signals': signals,
            }

            return summary

        except Exception as e:
            print(f"Error generando resumen: {e}")
            return {}
