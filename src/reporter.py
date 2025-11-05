"""
Módulo de reportes y análisis de performance.
Genera reportes por períodos (hora, día, semana, mes).
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from .account import Account, Trade


class Reporter:
    """Genera reportes y visualizaciones de performance."""

    def __init__(self, account: Account, output_dir: str = './logs'):
        """
        Inicializa el generador de reportes.

        Args:
            account: Cuenta de trading
            output_dir: Directorio para guardar reportes
        """
        self.account = account
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def get_period_trades(self, period: str) -> List[Trade]:
        """
        Obtiene operaciones de un período específico.

        Args:
            period: 'hour', 'day', 'week', 'month'

        Returns:
            Lista de operaciones del período
        """
        now = datetime.now()

        if period == 'hour':
            cutoff = now - timedelta(hours=1)
        elif period == 'day':
            cutoff = now - timedelta(days=1)
        elif period == 'week':
            cutoff = now - timedelta(weeks=1)
        elif period == 'month':
            cutoff = now - timedelta(days=30)
        else:
            return []

        return [trade for trade in self.account.trade_history
                if trade.timestamp >= cutoff]

    def calculate_period_performance(self, period: str) -> Dict[str, any]:
        """
        Calcula la performance para un período.

        Args:
            period: 'hour', 'day', 'week', 'month', 'all'

        Returns:
            Diccionario con métricas de performance
        """
        if period == 'all':
            trades = self.account.trade_history
        else:
            trades = self.get_period_trades(period)

        if not trades:
            return {
                'period': period,
                'trades': 0,
                'profit_loss': 0.0,
                'commission_paid': 0.0,
                'message': 'Sin operaciones en este período'
            }

        total_pnl = 0.0
        total_commission = 0.0
        buy_volume = 0.0
        sell_volume = 0.0
        winning = 0
        losing = 0

        # Calcular P&L de operaciones cerradas (pares BUY-SELL)
        position_tracker = {}

        for trade in trades:
            total_commission += trade.commission

            if trade.trade_type == 'BUY':
                buy_volume += trade.total
                if trade.symbol not in position_tracker:
                    position_tracker[trade.symbol] = []
                position_tracker[trade.symbol].append({
                    'amount': trade.amount,
                    'price': trade.price
                })

            elif trade.trade_type == 'SELL':
                sell_volume += trade.total
                if trade.symbol in position_tracker and position_tracker[trade.symbol]:
                    # Calcular P&L para esta venta
                    buy_position = position_tracker[trade.symbol][0]
                    pnl = (trade.price - buy_position['price']) * trade.amount
                    total_pnl += pnl

                    if pnl > 0:
                        winning += 1
                    else:
                        losing += 1

                    # Actualizar o eliminar posición
                    if trade.amount >= buy_position['amount']:
                        position_tracker[trade.symbol].pop(0)
                    else:
                        buy_position['amount'] -= trade.amount

        win_rate = (winning / (winning + losing) * 100) if (winning + losing) > 0 else 0

        performance = {
            'period': period,
            'trades': len(trades),
            'buy_trades': sum(1 for t in trades if t.trade_type == 'BUY'),
            'sell_trades': sum(1 for t in trades if t.trade_type == 'SELL'),
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'profit_loss': total_pnl,
            'commission_paid': total_commission,
            'net_profit_loss': total_pnl - total_commission,
            'winning_trades': winning,
            'losing_trades': losing,
            'win_rate': win_rate,
        }

        return performance

    def generate_period_report(self, period: str = 'day') -> str:
        """
        Genera un reporte de texto para un período.

        Args:
            period: 'hour', 'day', 'week', 'month', 'all'

        Returns:
            Reporte en formato texto
        """
        perf = self.calculate_period_performance(period)

        period_names = {
            'hour': 'ÚLTIMA HORA',
            'day': 'ÚLTIMO DÍA',
            'week': 'ÚLTIMA SEMANA',
            'month': 'ÚLTIMO MES',
            'all': 'HISTÓRICO COMPLETO'
        }

        report = f"\n{'='*70}\n"
        report += f"REPORTE DE PERFORMANCE - {period_names.get(period, period.upper())}\n"
        report += f"{'='*70}\n"
        report += f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"{'-'*70}\n"

        if perf.get('message'):
            report += f"{perf['message']}\n"
            report += f"{'='*70}\n"
            return report

        report += f"Operaciones Totales:     {perf['trades']}\n"
        report += f"  • Compras:             {perf['buy_trades']}\n"
        report += f"  • Ventas:              {perf['sell_trades']}\n"

        # Información de leverage si se usó
        leverage_trades = [t for t in self.account.trade_history if t.leverage > 1]
        if leverage_trades:
            avg_leverage = sum(t.leverage for t in leverage_trades) / len(leverage_trades)
            liquidations = sum(1 for t in self.account.trade_history if t.is_liquidation)
            report += f"  ⚡ Con Leverage:        {len(leverage_trades)}\n"
            report += f"  ⚡ Leverage Promedio:   {avg_leverage:.1f}x\n"
            if liquidations > 0:
                report += f"  ⚠️  Liquidaciones:       {liquidations}\n"

        report += f"\n"
        report += f"Volumen Operado:\n"
        report += f"  • Compras:             ${perf['buy_volume']:,.2f}\n"
        report += f"  • Ventas:              ${perf['sell_volume']:,.2f}\n"
        report += f"\n"
        report += f"Resultados:\n"

        pnl_emoji = "💰" if perf['profit_loss'] >= 0 else "📉"
        report += f"  {pnl_emoji} P&L Bruto:        ${perf['profit_loss']:+,.2f}\n"
        report += f"  💵 Comisiones:          ${perf['commission_paid']:,.2f}\n"

        net_pnl_emoji = "✅" if perf['net_profit_loss'] >= 0 else "❌"
        report += f"  {net_pnl_emoji} P&L Neto:          ${perf['net_profit_loss']:+,.2f}\n"
        report += f"\n"
        report += f"Estadísticas:\n"
        report += f"  • Operaciones Ganadoras: {perf['winning_trades']}\n"
        report += f"  • Operaciones Perdedoras: {perf['losing_trades']}\n"

        wr_emoji = "🎯" if perf['win_rate'] >= 50 else "⚠️"
        report += f"  {wr_emoji} Tasa de Éxito:      {perf['win_rate']:.2f}%\n"
        report += f"{'='*70}\n"

        return report

    def generate_comparison_report(self) -> str:
        """
        Genera un reporte comparativo de todos los períodos.

        Returns:
            Reporte comparativo en formato texto
        """
        periods = ['hour', 'day', 'week', 'month', 'all']
        performances = {p: self.calculate_period_performance(p) for p in periods}

        report = f"\n{'='*90}\n"
        report += f"REPORTE COMPARATIVO DE PERÍODOS\n"
        report += f"{'='*90}\n"
        report += f"{'Período':<15} {'Ops':>6} {'P&L Bruto':>12} {'Comisiones':>12} {'P&L Neto':>12} {'WR':>8}\n"
        report += f"{'-'*90}\n"

        period_labels = {
            'hour': 'Última Hora',
            'day': 'Último Día',
            'week': 'Última Semana',
            'month': 'Último Mes',
            'all': 'Histórico'
        }

        for period in periods:
            perf = performances[period]
            label = period_labels[period]

            report += f"{label:<15} "
            report += f"{perf['trades']:>6} "
            report += f"${perf['profit_loss']:>10,.2f} "
            report += f"${perf['commission_paid']:>10,.2f} "
            report += f"${perf['net_profit_loss']:>10,.2f} "
            report += f"{perf['win_rate']:>6.1f}%\n"

        report += f"{'='*90}\n"

        return report

    def plot_performance_chart(self, period: str = 'month', filename: str = None):
        """
        Genera un gráfico de performance.

        Args:
            period: 'day', 'week', 'month', 'all'
            filename: Nombre del archivo (opcional)
        """
        trades = self.get_period_trades(period) if period != 'all' else self.account.trade_history

        if not trades:
            print("No hay operaciones para graficar")
            return

        # Preparar datos
        df = pd.DataFrame([{
            'timestamp': t.timestamp,
            'type': t.trade_type,
            'price': t.price,
            'amount': t.amount,
            'total': t.total if t.trade_type == 'BUY' else -t.total,
            'symbol': t.symbol
        } for t in trades])

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Calcular balance acumulado
        cumulative_balance = self.account.initial_balance
        balances = []

        for _, row in df.iterrows():
            cumulative_balance += row['total']
            balances.append(cumulative_balance)

        df['balance'] = balances

        # Crear figura con subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Gráfico 1: Balance en el tiempo
        ax1.plot(df['timestamp'], df['balance'], linewidth=2, color='#2E86AB', label='Balance')
        ax1.axhline(y=self.account.initial_balance, color='gray', linestyle='--',
                   label=f'Balance Inicial: ${self.account.initial_balance:,.2f}')
        ax1.fill_between(df['timestamp'], self.account.initial_balance, df['balance'],
                        where=(df['balance'] >= self.account.initial_balance),
                        alpha=0.3, color='green', label='Ganancia')
        ax1.fill_between(df['timestamp'], self.account.initial_balance, df['balance'],
                        where=(df['balance'] < self.account.initial_balance),
                        alpha=0.3, color='red', label='Pérdida')

        ax1.set_title(f'Evolución del Balance - {period.capitalize()}', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Fecha')
        ax1.set_ylabel('Balance ($)')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)

        # Formatear eje Y con separadores de miles
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        # Gráfico 2: Operaciones
        buy_df = df[df['type'] == 'BUY']
        sell_df = df[df['type'] == 'SELL']

        if not buy_df.empty:
            ax2.scatter(buy_df['timestamp'], buy_df['price'], color='green',
                       marker='^', s=100, alpha=0.7, label='Compra', zorder=5)

        if not sell_df.empty:
            ax2.scatter(sell_df['timestamp'], sell_df['price'], color='red',
                       marker='v', s=100, alpha=0.7, label='Venta', zorder=5)

        ax2.set_title('Operaciones Ejecutadas', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Fecha')
        ax2.set_ylabel('Precio ($)')
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)

        # Ajustar layout
        plt.tight_layout()

        # Guardar o mostrar
        if filename:
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"✅ Gráfico guardado en: {filepath}")
        else:
            plt.show()

        plt.close()

    def generate_full_report(self, include_chart: bool = True, chart_filename: str = None):
        """
        Genera un reporte completo con estadísticas y gráfico.

        Args:
            include_chart: Si se debe generar gráfico
            chart_filename: Nombre del archivo para el gráfico
        """
        # Resumen de cuenta
        summary = self.account.get_account_summary()

        print("\n" + "="*70)
        print("REPORTE COMPLETO DE TRADING")
        print("="*70)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*70)
        print(f"Balance Disponible:    ${summary['balance']:,.2f}")
        print(f"Balance Inicial:       ${summary['initial_balance']:,.2f}")
        print(f"Valor Total:           ${summary['total_value']:,.2f}")
        print(f"P&L No Realizado:      ${summary['unrealized_pnl']:+,.2f}")

        total_return_emoji = "📈" if summary['total_return'] >= 0 else "📉"
        print(f"{total_return_emoji} Retorno Total:        {summary['total_return']:+.2f}%")
        print("-"*70)
        print(f"Operaciones Totales:   {summary['total_trades']}")
        print(f"  • Ganadoras:         {summary['winning_trades']}")
        print(f"  • Perdedoras:        {summary['losing_trades']}")
        print(f"Tasa de Éxito:         {summary['win_rate']:.2f}%")
        print(f"Comisiones Pagadas:    ${summary['total_commission']:,.2f}")
        print(f"Posiciones Activas:    {summary['positions']}")
        print("="*70)

        # Reporte comparativo
        print(self.generate_comparison_report())

        # Últimas operaciones
        recent_trades = self.account.get_trade_history(limit=10)
        if recent_trades:
            print("\n" + "="*70)
            print("ÚLTIMAS 10 OPERACIONES")
            print("="*70)
            for trade in reversed(recent_trades):
                print(trade)
            print("="*70)

        # Posiciones actuales
        if self.account.positions:
            print("\n" + "="*70)
            print("POSICIONES ACTIVAS")
            print("="*70)
            for symbol, position in self.account.positions.items():
                print(f"{symbol:8} | Cantidad: {position.amount:10.6f} | "
                      f"Precio Entrada: ${position.entry_price:10.2f} | "
                      f"Fecha: {position.entry_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*70)

        # Generar gráfico
        if include_chart and self.account.trade_history:
            print("\nGenerando gráfico de performance...")
            chart_file = chart_filename or f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.plot_performance_chart(period='all', filename=chart_file)

    def export_trades_csv(self, filename: str = None):
        """
        Exporta el historial de operaciones a CSV.

        Args:
            filename: Nombre del archivo (opcional)
        """
        if not self.account.trade_history:
            print("No hay operaciones para exportar")
            return

        df = pd.DataFrame([trade.to_dict() for trade in self.account.trade_history])

        if filename is None:
            filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = self.output_dir / filename
        df.to_csv(filepath, index=False)
        print(f"✅ Historial exportado a: {filepath}")
