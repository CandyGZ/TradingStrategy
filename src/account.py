"""
Módulo de gestión de cuenta ficticia.
Maneja el balance, operaciones, historial y comisiones.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class Trade:
    """Representa una operación de trading."""

    def __init__(self, trade_type: str, symbol: str, amount: float, price: float,
                 commission: float, timestamp: datetime = None):
        """
        Inicializa una operación.

        Args:
            trade_type: Tipo de operación ('BUY' o 'SELL')
            symbol: Símbolo del activo
            amount: Cantidad operada
            price: Precio de la operación
            commission: Comisión cobrada
            timestamp: Fecha y hora de la operación
        """
        self.trade_type = trade_type
        self.symbol = symbol
        self.amount = amount
        self.price = price
        self.commission = commission
        self.timestamp = timestamp or datetime.now()
        self.total = amount * price

        if trade_type == 'BUY':
            self.total += commission
        else:
            self.total -= commission

    def to_dict(self) -> dict:
        """Convierte la operación a diccionario."""
        return {
            'trade_type': self.trade_type,
            'symbol': self.symbol,
            'amount': self.amount,
            'price': self.price,
            'commission': self.commission,
            'total': self.total,
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
            timestamp=datetime.fromisoformat(data['timestamp'])
        )
        return trade

    def __str__(self) -> str:
        return (f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"{self.trade_type:4} | {self.symbol:8} | "
                f"Amount: {self.amount:10.6f} | Price: ${self.price:10.2f} | "
                f"Total: ${self.total:12.2f} | Fee: ${self.commission:6.2f}")


class Position:
    """Representa una posición abierta."""

    def __init__(self, symbol: str, amount: float, entry_price: float,
                 entry_time: datetime = None):
        """
        Inicializa una posición.

        Args:
            symbol: Símbolo del activo
            amount: Cantidad de unidades
            entry_price: Precio promedio de entrada
            entry_time: Fecha y hora de entrada
        """
        self.symbol = symbol
        self.amount = amount
        self.entry_price = entry_price
        self.entry_time = entry_time or datetime.now()

    def get_value(self, current_price: float) -> float:
        """Calcula el valor actual de la posición."""
        return self.amount * current_price

    def get_profit_loss(self, current_price: float) -> float:
        """Calcula la ganancia/pérdida de la posición."""
        return (current_price - self.entry_price) * self.amount

    def get_profit_loss_percentage(self, current_price: float) -> float:
        """Calcula el porcentaje de ganancia/pérdida."""
        return ((current_price - self.entry_price) / self.entry_price) * 100

    def to_dict(self) -> dict:
        """Convierte la posición a diccionario."""
        return {
            'symbol': self.symbol,
            'amount': self.amount,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time.isoformat()
        }

    @staticmethod
    def from_dict(data: dict) -> 'Position':
        """Crea una posición desde un diccionario."""
        return Position(
            symbol=data['symbol'],
            amount=data['amount'],
            entry_price=data['entry_price'],
            entry_time=datetime.fromisoformat(data['entry_time'])
        )


class Account:
    """Gestiona una cuenta de trading ficticia."""

    def __init__(self, initial_balance: float = 10000.0, commission_rate: float = 0.001,
                 data_dir: str = './data'):
        """
        Inicializa la cuenta.

        Args:
            initial_balance: Balance inicial
            commission_rate: Tasa de comisión por operación (0.001 = 0.1%)
            data_dir: Directorio para guardar datos
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.commission_rate = commission_rate
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

    def buy(self, symbol: str, amount: float, price: float) -> bool:
        """
        Ejecuta una orden de compra.

        Args:
            symbol: Símbolo del activo
            amount: Cantidad a comprar
            price: Precio de compra

        Returns:
            True si la operación fue exitosa
        """
        total_cost = amount * price
        commission = total_cost * self.commission_rate
        total_with_commission = total_cost + commission

        if total_with_commission > self.balance:
            print(f"❌ Balance insuficiente. Necesitas ${total_with_commission:.2f}, tienes ${self.balance:.2f}")
            return False

        # Actualizar balance
        self.balance -= total_with_commission

        # Crear o actualizar posición
        if symbol in self.positions:
            # Promedio de precio de entrada
            old_position = self.positions[symbol]
            total_amount = old_position.amount + amount
            weighted_price = ((old_position.entry_price * old_position.amount) +
                            (price * amount)) / total_amount

            self.positions[symbol] = Position(symbol, total_amount, weighted_price)
        else:
            self.positions[symbol] = Position(symbol, amount, price)

        # Registrar operación
        trade = Trade('BUY', symbol, amount, price, commission)
        self.trade_history.append(trade)
        self.total_trades += 1
        self.total_commission_paid += commission

        print(f"✅ Compra ejecutada: {amount:.6f} {symbol} @ ${price:.2f}")
        print(f"   Total: ${total_cost:.2f} + Comisión: ${commission:.2f}")
        print(f"   Balance restante: ${self.balance:.2f}")

        self.save()
        return True

    def sell(self, symbol: str, amount: float, price: float) -> bool:
        """
        Ejecuta una orden de venta.

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

        total_revenue = amount * price
        commission = total_revenue * self.commission_rate
        total_with_commission = total_revenue - commission

        # Actualizar balance
        self.balance += total_with_commission

        # Calcular ganancia/pérdida
        profit_loss = (price - position.entry_price) * amount
        profit_loss_percentage = ((price - position.entry_price) / position.entry_price) * 100

        # Actualizar estadísticas
        if profit_loss > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        # Actualizar o eliminar posición
        if amount >= position.amount:
            del self.positions[symbol]
        else:
            self.positions[symbol].amount -= amount

        # Registrar operación
        trade = Trade('SELL', symbol, amount, price, commission)
        self.trade_history.append(trade)
        self.total_trades += 1
        self.total_commission_paid += commission

        profit_emoji = "💰" if profit_loss > 0 else "📉"
        print(f"✅ Venta ejecutada: {amount:.6f} {symbol} @ ${price:.2f}")
        print(f"   Total: ${total_revenue:.2f} - Comisión: ${commission:.2f}")
        print(f"   {profit_emoji} P&L: ${profit_loss:.2f} ({profit_loss_percentage:+.2f}%)")
        print(f"   Balance actual: ${self.balance:.2f}")

        self.save()
        return True

    def get_position(self, symbol: str) -> Optional[Position]:
        """Obtiene la posición para un símbolo."""
        return self.positions.get(symbol)

    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calcula el valor total de la cuenta (balance + posiciones).

        Args:
            current_prices: Diccionario con precios actuales por símbolo

        Returns:
            Valor total de la cuenta
        """
        total = self.balance

        for symbol, position in self.positions.items():
            if symbol in current_prices:
                total += position.get_value(current_prices[symbol])

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
        realized_pnl = total_value - self.initial_balance
        total_return = ((total_value - self.initial_balance) / self.initial_balance) * 100

        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        summary = {
            'balance': self.balance,
            'initial_balance': self.initial_balance,
            'total_value': total_value,
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': realized_pnl,
            'total_return': total_return,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_commission': self.total_commission_paid,
            'positions': len(self.positions),
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
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
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
            self.total_trades = data['total_trades']
            self.winning_trades = data['winning_trades']
            self.losing_trades = data['losing_trades']
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

            print(f"✅ Cuenta cargada: Balance ${self.balance:.2f}, {len(self.positions)} posiciones activas")
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
        self.total_commission_paid = 0.0

        if self.account_file.exists():
            self.account_file.unlink()

        print(f"✅ Cuenta reiniciada con balance de ${self.initial_balance:.2f}")

    def __str__(self) -> str:
        summary = self.get_account_summary()
        return (f"\n{'='*60}\n"
                f"RESUMEN DE CUENTA\n"
                f"{'='*60}\n"
                f"Balance Disponible: ${summary['balance']:,.2f}\n"
                f"Balance Inicial:    ${summary['initial_balance']:,.2f}\n"
                f"Valor Total:        ${summary['total_value']:,.2f}\n"
                f"P&L No Realizado:   ${summary['unrealized_pnl']:+,.2f}\n"
                f"Retorno Total:      {summary['total_return']:+.2f}%\n"
                f"{'='*60}\n"
                f"Operaciones Totales: {summary['total_trades']}\n"
                f"Operaciones Ganadoras: {summary['winning_trades']}\n"
                f"Operaciones Perdedoras: {summary['losing_trades']}\n"
                f"Tasa de Éxito: {summary['win_rate']:.2f}%\n"
                f"Comisiones Pagadas: ${summary['total_commission']:,.2f}\n"
                f"Posiciones Activas: {summary['positions']}\n"
                f"{'='*60}\n")
