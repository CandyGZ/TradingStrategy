"""
Módulo de gestión de cuenta ficticia.
Maneja el balance, operaciones, historial, comisiones y apalancamiento (leverage).
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class Trade:
    """Representa una operación de trading."""

    def __init__(self, trade_type: str, symbol: str, amount: float, price: float,
                 commission: float, leverage: int = 1, timestamp: datetime = None,
                 is_liquidation: bool = False):
        """
        Inicializa una operación.

        Args:
            trade_type: Tipo de operación ('BUY' o 'SELL')
            symbol: Símbolo del activo
            amount: Cantidad operada
            price: Precio de la operación
            commission: Comisión cobrada
            leverage: Apalancamiento usado (1-100x)
            timestamp: Fecha y hora de la operación
            is_liquidation: Si es una liquidación forzada
        """
        self.trade_type = trade_type
        self.symbol = symbol
        self.amount = amount
        self.price = price
        self.commission = commission
        self.leverage = leverage
        self.timestamp = timestamp or datetime.now()
        self.is_liquidation = is_liquidation
        self.total = amount * price
        self.margin_used = self.total / leverage if leverage > 1 else self.total

        if trade_type == 'BUY':
            self.total += commission
            self.margin_used += commission
        else:
            self.total -= commission
            if leverage > 1:
                self.margin_used += commission

    def to_dict(self) -> dict:
        """Convierte la operación a diccionario."""
        return {
            'trade_type': self.trade_type,
            'symbol': self.symbol,
            'amount': self.amount,
            'price': self.price,
            'commission': self.commission,
            'leverage': self.leverage,
            'total': self.total,
            'margin_used': self.margin_used,
            'is_liquidation': self.is_liquidation,
            'timestamp': self.timestamp.isoformat()
        }

    @staticmethod
    def from_dict(data: dict) -> 'Trade':
        """Crea una operación desde un diccionario."""
        trade = Trade(
            trade_type=data['trade_type'],
            symbol=data['symbol'],
            amount=data['amount'],
            price=data['price'],
            commission=data['commission'],
            leverage=data.get('leverage', 1),
            timestamp=datetime.fromisoformat(data['timestamp']),
            is_liquidation=data.get('is_liquidation', False)
        )
        return trade

    def __str__(self) -> str:
        liq_mark = " [LIQUIDACIÓN]" if self.is_liquidation else ""
        leverage_str = f" {self.leverage}x" if self.leverage > 1 else ""
        return (f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"{self.trade_type:4}{leverage_str:4} | {self.symbol:8} | "
                f"Amount: {self.amount:10.6f} | Price: ${self.price:10.2f} | "
                f"Total: ${self.total:12.2f} | Margin: ${self.margin_used:10.2f} | "
                f"Fee: ${self.commission:6.2f}{liq_mark}")


class Position:
    """Representa una posición abierta con soporte de apalancamiento."""

    def __init__(self, symbol: str, amount: float, entry_price: float,
                 leverage: int = 1, margin_used: float = 0, entry_time: datetime = None):
        """
        Inicializa una posición.

        Args:
            symbol: Símbolo del activo
            amount: Cantidad de unidades
            entry_price: Precio promedio de entrada
            leverage: Apalancamiento usado (1-100x)
            margin_used: Margen utilizado (capital real)
            entry_time: Fecha y hora de entrada
        """
        self.symbol = symbol
        self.amount = amount
        self.entry_price = entry_price
        self.leverage = leverage
        self.margin_used = margin_used if margin_used > 0 else (amount * entry_price) / leverage
        self.entry_time = entry_time or datetime.now()

    def get_value(self, current_price: float) -> float:
        """Calcula el valor actual de la posición."""
        return self.amount * current_price

    def get_profit_loss(self, current_price: float) -> float:
        """
        Calcula la ganancia/pérdida de la posición.
        Con leverage, el P&L es amplificado.
        """
        price_change = current_price - self.entry_price
        pnl = price_change * self.amount
        return pnl

    def get_profit_loss_percentage(self, current_price: float) -> float:
        """
        Calcula el porcentaje de ganancia/pérdida basado en el margen usado.
        Con leverage, el porcentaje se amplifica.
        """
        pnl = self.get_profit_loss(current_price)
        if self.margin_used <= 0:
            return 0.0
        return (pnl / self.margin_used) * 100

    def get_liquidation_price(self) -> float:
        """
        Calcula el precio de liquidación.
        Liquidación ocurre cuando pérdidas ≈ 90% del margen (dejando 10% para comisiones).
        """
        if self.leverage <= 1:
            return 0.0  # Sin leverage, no hay liquidación

        # Pérdida máxima antes de liquidación (90% del margen)
        max_loss = self.margin_used * 0.90

        # Calcular cambio de precio que causa esa pérdida
        price_change_for_liquidation = max_loss / self.amount

        # Precio de liquidación
        liquidation_price = self.entry_price - price_change_for_liquidation

        return max(0.0, liquidation_price)

    def is_liquidated(self, current_price: float) -> bool:
        """
        Verifica si la posición debe ser liquidada.

        Args:
            current_price: Precio actual del activo

        Returns:
            True si la posición debe ser liquidada
        """
        if self.leverage <= 1:
            return False

        liquidation_price = self.get_liquidation_price()
        return current_price <= liquidation_price

    def to_dict(self) -> dict:
        """Convierte la posición a diccionario."""
        return {
            'symbol': self.symbol,
            'amount': self.amount,
            'entry_price': self.entry_price,
            'leverage': self.leverage,
            'margin_used': self.margin_used,
            'entry_time': self.entry_time.isoformat()
        }

    @staticmethod
    def from_dict(data: dict) -> 'Position':
        """Crea una posición desde un diccionario."""
        return Position(
            symbol=data['symbol'],
            amount=data['amount'],
            entry_price=data['entry_price'],
            leverage=data.get('leverage', 1),
            margin_used=data.get('margin_used', 0),
            entry_time=datetime.fromisoformat(data['entry_time'])
        )


class Account:
    """Gestiona una cuenta de trading ficticia con soporte de apalancamiento."""

    def __init__(self, initial_balance: float = 10000.0, commission_rate: float = 0.001,
                 max_leverage: int = 100, data_dir: str = './data'):
        """
        Inicializa la cuenta.

        Args:
            initial_balance: Balance inicial
            commission_rate: Tasa de comisión por operación (0.001 = 0.1%)
            max_leverage: Apalancamiento máximo permitido (3-100x)
            data_dir: Directorio para guardar datos
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.commission_rate = commission_rate
        self.max_leverage = max(3, min(100, max_leverage))  # Entre 3x y 100x
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.account_file = self.data_dir / 'account.json'

        # Estadísticas
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_commission_paid = 0.0
        self.total_liquidations = 0

    def get_available_balance(self) -> float:
        """
        Calcula el balance disponible (balance - margen usado).

        Returns:
            Balance disponible para nuevas operaciones
        """
        margin_in_use = sum(pos.margin_used for pos in self.positions.values())
        return self.balance - margin_in_use

    def buy(self, symbol: str, amount: float, price: float, leverage: int = 1) -> bool:
        """
        Ejecuta una orden de compra con apalancamiento opcional.

        Args:
            symbol: Símbolo del activo
            amount: Cantidad a comprar
            price: Precio de compra
            leverage: Apalancamiento (1-max_leverage)

        Returns:
            True si la operación fue exitosa
        """
        # Validar leverage
        leverage = max(1, min(self.max_leverage, leverage))

        # Calcular costos
        position_value = amount * price
        margin_required = position_value / leverage if leverage > 1 else position_value
        commission = position_value * self.commission_rate
        total_required = margin_required + commission

        available = self.get_available_balance()

        if total_required > available:
            print(f"❌ Balance insuficiente. Necesitas ${total_required:.2f}, tienes ${available:.2f} disponible")
            return False

        # Crear o actualizar posición
        if symbol in self.positions:
            # Promediar precio de entrada si ya existe posición
            old_position = self.positions[symbol]

            # Solo permite misma leverage
            if old_position.leverage != leverage:
                print(f"❌ No puedes cambiar el leverage de una posición existente ({old_position.leverage}x)")
                return False

            total_amount = old_position.amount + amount
            total_margin = old_position.margin_used + margin_required
            weighted_price = ((old_position.entry_price * old_position.amount) +
                            (price * amount)) / total_amount

            self.positions[symbol] = Position(
                symbol, total_amount, weighted_price, leverage, total_margin
            )
        else:
            self.positions[symbol] = Position(
                symbol, amount, price, leverage, margin_required
            )

        # Registrar operación (el balance no se reduce con leverage, solo el margen)
        trade = Trade('BUY', symbol, amount, price, commission, leverage)
        self.trade_history.append(trade)
        self.total_trades += 1
        self.total_commission_paid += commission

        leverage_emoji = "⚡" if leverage > 1 else ""
        leverage_str = f" [{leverage}x LEVERAGE]" if leverage > 1 else ""
        print(f"✅ {leverage_emoji}Compra ejecutada{leverage_str}: {amount:.6f} {symbol} @ ${price:.2f}")
        print(f"   Valor Posición: ${position_value:.2f}")
        print(f"   Margen Usado: ${margin_required:.2f}")
        print(f"   Comisión: ${commission:.2f}")

        if leverage > 1:
            liq_price = self.positions[symbol].get_liquidation_price()
            print(f"   ⚠️  Precio Liquidación: ${liq_price:.2f}")

        print(f"   Balance Disponible: ${self.get_available_balance():.2f}")

        self.save()
        return True

    def sell(self, symbol: str, amount: float, price: float) -> bool:
        """
        Ejecuta una orden de venta (cierra posición).

        Args:
            symbol: Símbolo del activo
            amount: Cantidad a vender
            price: Precio de venta

        Returns:
            True si la operación fue exitosa
        """
        if symbol not in self.positions:
            print(f"❌ No tienes posición en {symbol}")
            return False

        position = self.positions[symbol]

        if amount > position.amount:
            print(f"❌ Cantidad insuficiente. Tienes {position.amount:.6f}, intentas vender {amount:.6f}")
            return False

        # Calcular valores
        sale_value = amount * price
        commission = sale_value * self.commission_rate

        # Calcular P&L
        profit_loss = (price - position.entry_price) * amount

        # El margen liberado es proporcional a la cantidad vendida
        margin_released = (amount / position.amount) * position.margin_used

        # Actualizar balance: devolver margen + P&L - comisión
        self.balance += margin_released + profit_loss - commission

        # Calcular porcentaje basado en margen
        profit_loss_percentage = (profit_loss / margin_released) * 100 if margin_released > 0 else 0

        # Actualizar estadísticas
        if profit_loss > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        # Actualizar o eliminar posición
        if amount >= position.amount:
            del self.positions[symbol]
        else:
            remaining_amount = position.amount - amount
            remaining_margin = position.margin_used - margin_released
            self.positions[symbol] = Position(
                symbol, remaining_amount, position.entry_price,
                position.leverage, remaining_margin, position.entry_time
            )

        # Registrar operación
        trade = Trade('SELL', symbol, amount, price, commission, position.leverage)
        self.trade_history.append(trade)
        self.total_trades += 1
        self.total_commission_paid += commission

        profit_emoji = "💰" if profit_loss > 0 else "📉"
        leverage_str = f" [{position.leverage}x]" if position.leverage > 1 else ""
        print(f"✅ Venta ejecutada{leverage_str}: {amount:.6f} {symbol} @ ${price:.2f}")
        print(f"   Valor Venta: ${sale_value:.2f}")
        print(f"   Margen Liberado: ${margin_released:.2f}")
        print(f"   Comisión: ${commission:.2f}")
        print(f"   {profit_emoji} P&L: ${profit_loss:.2f} ({profit_loss_percentage:+.2f}%)")
        print(f"   Balance Total: ${self.balance:.2f}")

        self.save()
        return True

    def check_liquidations(self, current_prices: Dict[str, float]) -> List[str]:
        """
        Verifica y ejecuta liquidaciones si es necesario.

        Args:
            current_prices: Diccionario con precios actuales por símbolo

        Returns:
            Lista de símbolos que fueron liquidados
        """
        liquidated = []

        for symbol, position in list(self.positions.items()):
            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]

            if position.is_liquidated(current_price):
                print(f"\n{'='*70}")
                print(f"⚠️  LIQUIDACIÓN FORZADA - {symbol}")
                print(f"{'='*70}")

                liq_price = position.get_liquidation_price()
                loss = position.get_profit_loss(current_price)

                print(f"Precio Entrada: ${position.entry_price:.2f}")
                print(f"Precio Liquidación: ${liq_price:.2f}")
                print(f"Precio Actual: ${current_price:.2f}")
                print(f"Leverage: {position.leverage}x")
                print(f"Pérdida: ${loss:.2f}")
                print(f"Margen Perdido: ${position.margin_used:.2f}")

                # Liquidar posición (se pierde todo el margen)
                # En liquidación, no se devuelve margen, solo se registra la pérdida
                self.balance -= position.margin_used  # Margen se pierde completamente

                # Registrar como trade de liquidación
                trade = Trade(
                    'SELL', symbol, position.amount, current_price,
                    0, position.leverage, is_liquidation=True
                )
                self.trade_history.append(trade)
                self.total_liquidations += 1
                self.losing_trades += 1

                # Eliminar posición
                del self.positions[symbol]
                liquidated.append(symbol)

                print(f"Balance Restante: ${self.balance:.2f}")
                print(f"{'='*70}\n")

                self.save()

        return liquidated

    def get_position(self, symbol: str) -> Optional[Position]:
        """Obtiene la posición para un símbolo."""
        return self.positions.get(symbol)

    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calcula el valor total de la cuenta (balance + P&L de posiciones).

        Args:
            current_prices: Diccionario con precios actuales por símbolo

        Returns:
            Valor total de la cuenta
        """
        total = self.balance

        for symbol, position in self.positions.items():
            if symbol in current_prices:
                # El valor incluye el P&L
                pnl = position.get_profit_loss(current_prices[symbol])
                total += pnl

        return total

    def get_unrealized_profit_loss(self, current_prices: Dict[str, float]) -> float:
        """
        Calcula la ganancia/pérdida no realizada.

        Args:
            current_prices: Diccionario con precios actuales

        Returns:
            Ganancia/pérdida total no realizada
        """
        total_pnl = 0.0

        for symbol, position in self.positions.items():
            if symbol in current_prices:
                total_pnl += position.get_profit_loss(current_prices[symbol])

        return total_pnl

    def get_total_margin_used(self) -> float:
        """
        Calcula el margen total utilizado.

        Returns:
            Margen total en uso
        """
        return sum(pos.margin_used for pos in self.positions.values())

    def get_account_summary(self, current_prices: Dict[str, float] = None) -> Dict[str, any]:
        """
        Obtiene un resumen de la cuenta.

        Args:
            current_prices: Diccionario con precios actuales (opcional)

        Returns:
            Diccionario con resumen de la cuenta
        """
        current_prices = current_prices or {}

        total_value = self.get_total_value(current_prices)
        unrealized_pnl = self.get_unrealized_profit_loss(current_prices)
        margin_used = self.get_total_margin_used()
        available_balance = self.get_available_balance()
        total_return = ((total_value - self.initial_balance) / self.initial_balance) * 100

        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        summary = {
            'balance': self.balance,
            'available_balance': available_balance,
            'margin_used': margin_used,
            'initial_balance': self.initial_balance,
            'total_value': total_value,
            'unrealized_pnl': unrealized_pnl,
            'total_return': total_return,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'liquidations': self.total_liquidations,
            'win_rate': win_rate,
            'total_commission': self.total_commission_paid,
            'positions': len(self.positions),
            'max_leverage': self.max_leverage,
        }

        return summary

    def get_trade_history(self, limit: int = None, symbol: str = None) -> List[Trade]:
        """
        Obtiene el historial de operaciones.

        Args:
            limit: Número máximo de operaciones a retornar
            symbol: Filtrar por símbolo (opcional)

        Returns:
            Lista de operaciones
        """
        trades = self.trade_history

        if symbol:
            trades = [t for t in trades if t.symbol == symbol]

        if limit:
            trades = trades[-limit:]

        return trades

    def save(self):
        """Guarda el estado de la cuenta en archivo JSON."""
        data = {
            'initial_balance': self.initial_balance,
            'balance': self.balance,
            'commission_rate': self.commission_rate,
            'max_leverage': self.max_leverage,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_liquidations': self.total_liquidations,
            'total_commission_paid': self.total_commission_paid,
            'positions': {symbol: pos.to_dict() for symbol, pos in self.positions.items()},
            'trade_history': [trade.to_dict() for trade in self.trade_history],
        }

        with open(self.account_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self) -> bool:
        """
        Carga el estado de la cuenta desde archivo JSON.

        Returns:
            True si se cargó exitosamente
        """
        if not self.account_file.exists():
            return False

        try:
            with open(self.account_file, 'r') as f:
                data = json.load(f)

            self.initial_balance = data['initial_balance']
            self.balance = data['balance']
            self.commission_rate = data['commission_rate']
            self.max_leverage = data.get('max_leverage', 1)
            self.total_trades = data['total_trades']
            self.winning_trades = data['winning_trades']
            self.losing_trades = data['losing_trades']
            self.total_liquidations = data.get('total_liquidations', 0)
            self.total_commission_paid = data['total_commission_paid']

            # Cargar posiciones
            self.positions = {
                symbol: Position.from_dict(pos_data)
                for symbol, pos_data in data['positions'].items()
            }

            # Cargar historial
            self.trade_history = [
                Trade.from_dict(trade_data)
                for trade_data in data['trade_history']
            ]

            leverage_info = f" (Leverage máx: {self.max_leverage}x)" if self.max_leverage > 1 else ""
            print(f"✅ Cuenta cargada: Balance ${self.balance:.2f}, {len(self.positions)} posiciones activas{leverage_info}")
            return True

        except Exception as e:
            print(f"❌ Error cargando cuenta: {e}")
            return False

    def reset(self):
        """Reinicia la cuenta al estado inicial."""
        self.balance = self.initial_balance
        self.positions = {}
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_liquidations = 0
        self.total_commission_paid = 0.0

        if self.account_file.exists():
            self.account_file.unlink()

        print(f"✅ Cuenta reiniciada con balance de ${self.initial_balance:.2f}")

    def __str__(self) -> str:
        summary = self.get_account_summary()

        leverage_info = ""
        if self.max_leverage > 1:
            leverage_info = (f"Leverage Máximo:    {summary['max_leverage']}x\n"
                           f"Margen Utilizado:   ${summary['margin_used']:,.2f}\n"
                           f"Balance Disponible: ${summary['available_balance']:,.2f}\n")

        liquidation_info = ""
        if self.total_liquidations > 0:
            liquidation_info = f"⚠️  Liquidaciones:     {summary['liquidations']}\n"

        return (f"\n{'='*60}\n"
                f"RESUMEN DE CUENTA\n"
                f"{'='*60}\n"
                f"{leverage_info}"
                f"Balance Total:      ${summary['balance']:,.2f}\n"
                f"Balance Inicial:    ${summary['initial_balance']:,.2f}\n"
                f"Valor Neto:         ${summary['total_value']:,.2f}\n"
                f"P&L No Realizado:   ${summary['unrealized_pnl']:+,.2f}\n"
                f"Retorno Total:      {summary['total_return']:+.2f}%\n"
                f"{'='*60}\n"
                f"Operaciones Totales: {summary['total_trades']}\n"
                f"Operaciones Ganadoras: {summary['winning_trades']}\n"
                f"Operaciones Perdedoras: {summary['losing_trades']}\n"
                f"{liquidation_info}"
                f"Tasa de Éxito: {summary['win_rate']:.2f}%\n"
                f"Comisiones Pagadas: ${summary['total_commission']:,.2f}\n"
                f"Posiciones Activas: {summary['positions']}\n"
                f"{'='*60}\n")
