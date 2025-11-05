"""
Módulo para obtener datos de precios en tiempo real usando yfinance.
Proporciona datos históricos y actuales de acciones y criptomonedas.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple
import time


class DataProvider:
    """Proveedor de datos de mercado en tiempo real."""

    def __init__(self, symbol: str):
        """
        Inicializa el proveedor de datos.

        Args:
            symbol: Símbolo del activo (ej: 'BTC-USD', 'AAPL', 'ETH-USD')
        """
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self._cache = {}
        self._cache_time = {}

    def get_current_price(self) -> float:
        """
        Obtiene el precio actual del activo.

        Returns:
            Precio actual como float
        """
        try:
            # Intentar obtener el precio en tiempo real
            data = self.ticker.info

            # Intentar diferentes campos según disponibilidad
            price = data.get('regularMarketPrice') or \
                   data.get('currentPrice') or \
                   data.get('previousClose')

            if price is None:
                # Si no hay info disponible, usar el último precio histórico
                hist = self.ticker.history(period='1d', interval='1m')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]

            return float(price) if price is not None else 0.0

        except Exception as e:
            print(f"Error obteniendo precio actual: {e}")
            # Fallback: último precio histórico
            try:
                hist = self.ticker.history(period='1d', interval='5m')
                if not hist.empty:
                    return float(hist['Close'].iloc[-1])
            except:
                pass
            return 0.0

    def get_historical_data(self, period: str = '1mo', interval: str = '1h') -> pd.DataFrame:
        """
        Obtiene datos históricos del activo.

        Args:
            period: Período de datos ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: Intervalo de datos ('1m', '5m', '15m', '1h', '1d', '1wk', '1mo')

        Returns:
            DataFrame con datos históricos (Open, High, Low, Close, Volume)
        """
        cache_key = f"{period}_{interval}"

        # Usar caché si es reciente (menos de 5 minutos)
        if cache_key in self._cache:
            cache_age = time.time() - self._cache_time[cache_key]
            if cache_age < 300:  # 5 minutos
                return self._cache[cache_key]

        try:
            data = self.ticker.history(period=period, interval=interval)
            self._cache[cache_key] = data
            self._cache_time[cache_key] = time.time()
            return data
        except Exception as e:
            print(f"Error obteniendo datos históricos: {e}")
            return pd.DataFrame()

    def get_custom_period_data(self, start_date: datetime, end_date: datetime,
                               interval: str = '1h') -> pd.DataFrame:
        """
        Obtiene datos para un período personalizado.

        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            interval: Intervalo de datos

        Returns:
            DataFrame con datos históricos
        """
        try:
            data = self.ticker.history(start=start_date, end=end_date, interval=interval)
            return data
        except Exception as e:
            print(f"Error obteniendo datos personalizados: {e}")
            return pd.DataFrame()

    def get_info(self) -> dict:
        """
        Obtiene información general del activo.

        Returns:
            Diccionario con información del activo
        """
        try:
            return self.ticker.info
        except Exception as e:
            print(f"Error obteniendo información: {e}")
            return {}

    def get_price_range(self, period: str = '1d') -> Tuple[float, float]:
        """
        Obtiene el rango de precios (mínimo, máximo) para un período.

        Args:
            period: Período a analizar

        Returns:
            Tupla (precio_mínimo, precio_máximo)
        """
        try:
            data = self.get_historical_data(period=period, interval='1h')
            if data.empty:
                return (0.0, 0.0)

            min_price = float(data['Low'].min())
            max_price = float(data['High'].max())
            return (min_price, max_price)
        except Exception as e:
            print(f"Error obteniendo rango de precios: {e}")
            return (0.0, 0.0)

    def is_market_open(self) -> bool:
        """
        Verifica si el mercado está abierto (aplicable principalmente a acciones).
        Para criptomonedas, siempre retorna True.

        Returns:
            True si el mercado está abierto
        """
        # Las criptomonedas se tradean 24/7
        if '-USD' in self.symbol or 'USDT' in self.symbol:
            return True

        try:
            info = self.get_info()
            market_state = info.get('marketState', 'CLOSED')
            return market_state == 'REGULAR' or market_state == 'OPEN'
        except:
            return False
