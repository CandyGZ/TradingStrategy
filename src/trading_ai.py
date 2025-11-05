"""
Módulo de IA para trading automático.
Utiliza análisis técnico y patrones históricos para tomar decisiones de compra/venta.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
import random
from .technical_analysis import TechnicalAnalysis
from .data_provider import DataProvider


class TradingAI:
    """
    IA que toma decisiones de trading basadas en análisis técnico,
    Fibonacci y patrones históricos.
    """

    def __init__(self, symbol: str, risk_tolerance: float = 0.5, min_confidence: int = 60,
                 leverage: int = 1):
        """
        Inicializa la IA de trading.

        Args:
            symbol: Símbolo del activo a tradear
            risk_tolerance: Tolerancia al riesgo (0.0 a 1.0)
            min_confidence: Confianza mínima para ejecutar operaciones (0-100)
            leverage: Apalancamiento a usar (1-100x)
        """
        self.symbol = symbol
        self.risk_tolerance = risk_tolerance
        self.min_confidence = min_confidence
        self.leverage = max(1, min(100, leverage))
        self.data_provider = DataProvider(symbol)
        self.last_decision_time = None
        self.decision_cooldown = 300  # 5 minutos entre decisiones

        # Ajustar estrategia según leverage
        if self.leverage > 1:
            # Con leverage alto, ser más conservador
            self.min_confidence = max(min_confidence, 60 + (self.leverage // 10))
            # Reducir tolerancia al riesgo con leverage muy alto
            if self.leverage >= 50:
                self.risk_tolerance = min(self.risk_tolerance, 0.3)
            elif self.leverage >= 20:
                self.risk_tolerance = min(self.risk_tolerance, 0.5)

    def analyze_market(self) -> Dict[str, any]:
        """
        Analiza el mercado actual y retorna un análisis completo.

        Returns:
            Diccionario con análisis de mercado
        """
        # Obtener datos históricos
        historical_data = self.data_provider.get_historical_data(period='1mo', interval='1h')

        if historical_data.empty:
            return {
                'status': 'ERROR',
                'message': 'No se pudieron obtener datos del mercado'
            }

        # Realizar análisis técnico
        ta = TechnicalAnalysis(historical_data)
        analysis = ta.get_analysis_summary()

        # Obtener precio actual
        current_price = self.data_provider.get_current_price()

        analysis['current_price'] = current_price
        analysis['symbol'] = self.symbol
        analysis['timestamp'] = datetime.now()

        return analysis

    def make_decision(self, account_balance: float, current_position: Optional[float] = None,
                     position_size: Optional[float] = None) -> Dict[str, any]:
        """
        Toma una decisión de trading basada en el análisis de mercado.

        Args:
            account_balance: Balance disponible en la cuenta
            current_position: Precio promedio de compra de la posición actual (None si no hay posición)
            position_size: Cantidad de unidades en la posición actual

        Returns:
            Diccionario con la decisión: {action, amount, price, confidence, reasons}
        """
        # Verificar cooldown
        now = datetime.now()
        if self.last_decision_time:
            time_since_last = (now - self.last_decision_time).total_seconds()
            if time_since_last < self.decision_cooldown:
                return {
                    'action': 'HOLD',
                    'amount': 0,
                    'confidence': 0,
                    'reasons': [f'Esperando cooldown ({int(self.decision_cooldown - time_since_last)}s restantes)']
                }

        # Analizar mercado
        market_analysis = self.analyze_market()

        if market_analysis.get('status') == 'ERROR':
            return {
                'action': 'HOLD',
                'amount': 0,
                'confidence': 0,
                'reasons': [market_analysis.get('message', 'Error en análisis')]
            }

        # Obtener señales de trading
        signals = market_analysis.get('signals', {})
        action = signals.get('action', 'HOLD')
        confidence = signals.get('confidence', 0)
        reasons = signals.get('reasons', [])

        current_price = market_analysis.get('current_price', 0)

        # Verificar confianza mínima
        if confidence < self.min_confidence:
            return {
                'action': 'HOLD',
                'amount': 0,
                'price': current_price,
                'confidence': confidence,
                'reasons': [f'Confianza insuficiente ({confidence}% < {self.min_confidence}%)'] + reasons
            }

        # Calcular cantidad a operar
        decision = {
            'action': action,
            'price': current_price,
            'confidence': confidence,
            'reasons': reasons,
            'amount': 0
        }

        # Lógica de decisión según la acción
        if action == 'BUY':
            decision.update(self._calculate_buy_amount(
                account_balance, current_price, confidence, market_analysis
            ))

        elif action == 'SELL' and current_position is not None and position_size is not None:
            decision.update(self._calculate_sell_amount(
                current_position, position_size, current_price, confidence, market_analysis
            ))

        else:
            decision['action'] = 'HOLD'
            decision['reasons'].append('Sin posición para vender')

        self.last_decision_time = now
        return decision

    def _calculate_buy_amount(self, balance: float, price: float, confidence: int,
                             analysis: Dict) -> Dict[str, any]:
        """
        Calcula la cantidad a comprar basada en el balance y confianza.
        Con leverage, el cálculo considera el margen requerido.

        Args:
            balance: Balance disponible
            price: Precio actual
            confidence: Nivel de confianza (0-100)
            analysis: Análisis de mercado

        Returns:
            Diccionario con amount, leverage y justificación adicional
        """
        if balance <= 0 or price <= 0:
            return {
                'amount': 0,
                'leverage': self.leverage,
                'reasons': ['Balance o precio inválido']
            }

        # Calcular porcentaje a invertir basado en confianza y riesgo
        confidence_factor = confidence / 100.0
        investment_percentage = self.risk_tolerance * confidence_factor

        # Ajustar según volatilidad
        volatility = analysis.get('volatility', 0)
        if volatility > 0.5:  # Alta volatilidad
            investment_percentage *= 0.7  # Reducir exposición
        elif volatility < 0.2:  # Baja volatilidad
            investment_percentage *= 1.2  # Aumentar exposición

        # Con leverage alto, reducir porcentaje de inversión
        if self.leverage >= 50:
            investment_percentage *= 0.5  # Usar solo 50% con leverage muy alto
        elif self.leverage >= 20:
            investment_percentage *= 0.7  # Usar solo 70% con leverage alto

        # Limitar entre 5% y 30% del balance
        investment_percentage = max(0.05, min(0.30, investment_percentage))

        # Calcular monto a invertir (esto es el MARGEN con leverage)
        margin_to_use = balance * investment_percentage

        # Con leverage, podemos controlar más capital
        position_value = margin_to_use * self.leverage
        units_to_buy = position_value / price

        return {
            'amount': units_to_buy,
            'leverage': self.leverage,
            'investment_percentage': investment_percentage * 100,
            'margin_used': margin_to_use,
            'position_value': position_value,
        }

    def _calculate_sell_amount(self, entry_price: float, position_size: float,
                              current_price: float, confidence: int,
                              analysis: Dict) -> Dict[str, any]:
        """
        Calcula la cantidad a vender basada en la posición y condiciones.

        Args:
            entry_price: Precio de entrada de la posición
            position_size: Tamaño de la posición
            current_price: Precio actual
            confidence: Nivel de confianza (0-100)
            analysis: Análisis de mercado

        Returns:
            Diccionario con amount y justificación adicional
        """
        profit_percentage = ((current_price - entry_price) / entry_price) * 100

        # Determinar qué porcentaje vender
        sell_percentage = 1.0  # Por defecto vender todo

        # Si estamos en ganancia, considerar venta parcial
        if profit_percentage > 0:
            if confidence < 80:
                # Vender solo el 50% si la confianza no es alta
                sell_percentage = 0.5

        # Si estamos en pérdida significativa, vender todo (stop loss)
        if profit_percentage < -5:
            sell_percentage = 1.0

        units_to_sell = position_size * sell_percentage

        additional_reasons = []
        if profit_percentage > 0:
            additional_reasons.append(f'Ganancia actual: {profit_percentage:.2f}%')
        else:
            additional_reasons.append(f'Pérdida actual: {profit_percentage:.2f}%')

        if sell_percentage < 1.0:
            additional_reasons.append(f'Venta parcial: {sell_percentage * 100:.0f}% de la posición')

        return {
            'amount': units_to_sell,
            'profit_percentage': profit_percentage,
            'reasons': additional_reasons
        }

    def should_take_profit(self, entry_price: float, current_price: float,
                          target_profit: float = 10.0) -> bool:
        """
        Determina si se debe tomar ganancia.

        Args:
            entry_price: Precio de entrada
            current_price: Precio actual
            target_profit: Objetivo de ganancia en porcentaje

        Returns:
            True si se debe tomar ganancia
        """
        profit_percentage = ((current_price - entry_price) / entry_price) * 100
        return profit_percentage >= target_profit

    def should_stop_loss(self, entry_price: float, current_price: float,
                        stop_loss: float = 5.0) -> bool:
        """
        Determina si se debe activar el stop loss.

        Args:
            entry_price: Precio de entrada
            current_price: Precio actual
            stop_loss: Porcentaje de pérdida para stop loss

        Returns:
            True si se debe activar stop loss
        """
        loss_percentage = ((entry_price - current_price) / entry_price) * 100
        return loss_percentage >= stop_loss

    def evaluate_position(self, entry_price: float, current_price: float,
                         position_size: float) -> Dict[str, any]:
        """
        Evalúa una posición actual y proporciona recomendaciones.

        Args:
            entry_price: Precio de entrada
            current_price: Precio actual
            position_size: Tamaño de la posición

        Returns:
            Diccionario con evaluación y recomendaciones
        """
        profit_loss = (current_price - entry_price) * position_size
        profit_loss_percentage = ((current_price - entry_price) / entry_price) * 100

        evaluation = {
            'entry_price': entry_price,
            'current_price': current_price,
            'position_size': position_size,
            'profit_loss': profit_loss,
            'profit_loss_percentage': profit_loss_percentage,
            'recommendation': 'HOLD'
        }

        # Obtener análisis de mercado actual
        market_analysis = self.analyze_market()

        # Recomendación basada en take profit
        if self.should_take_profit(entry_price, current_price):
            evaluation['recommendation'] = 'TAKE_PROFIT'
            evaluation['reason'] = f'Objetivo de ganancia alcanzado ({profit_loss_percentage:.2f}%)'

        # Recomendación basada en stop loss
        elif self.should_stop_loss(entry_price, current_price):
            evaluation['recommendation'] = 'STOP_LOSS'
            evaluation['reason'] = f'Stop loss activado (pérdida: {profit_loss_percentage:.2f}%)'

        # Recomendación basada en señales técnicas
        elif market_analysis.get('signals', {}).get('action') == 'SELL':
            evaluation['recommendation'] = 'CONSIDER_SELL'
            evaluation['reason'] = 'Señales técnicas sugieren venta'

        else:
            evaluation['reason'] = 'Mantener posición según condiciones actuales'

        return evaluation

    def get_strategy_description(self) -> str:
        """
        Retorna una descripción de la estrategia utilizada.

        Returns:
            Descripción en texto de la estrategia
        """
        leverage_info = ""
        if self.leverage > 1:
            leverage_info = f"""
5. Apalancamiento (Leverage):
   - Leverage utilizado: {self.leverage}x
   - Amplifica ganancias y pérdidas {self.leverage}x
   - Margen requerido: 1/{self.leverage} del valor de posición
   - Estrategia ajustada para mayor conservadurismo
   - Confianza mínima aumentada con leverage alto
   - ⚠️  RIESGO DE LIQUIDACIÓN si pérdidas > 90% del margen
"""

        return f"""
Estrategia de Trading AI para {self.symbol}:

1. Análisis Técnico:
   - Medias Móviles (SMA 10, 20, 50)
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - Bandas de Bollinger
   - Niveles de Fibonacci

2. Gestión de Riesgo:
   - Tolerancia al riesgo: {self.risk_tolerance * 100:.0f}%
   - Confianza mínima: {self.min_confidence}%
   - Stop Loss: 5%
   - Take Profit: 10%
   - Inversión máxima por operación: 30% del balance

3. Criterios de Decisión:
   - Mínimo 2 señales coincidentes para operar
   - Ajuste automático según volatilidad
   - Cooldown de {self.decision_cooldown}s entre decisiones
   - Análisis de soporte y resistencia

4. Basado en Fibonacci:
   - Identificación de niveles clave
   - Zonas de reversión potencial
   - Objetivos de precio dinámicos
{leverage_info}
"""
