#!/usr/bin/env python3
"""
Emulador de Trading con IA
Sistema de trading automático con dinero ficticio que usa análisis técnico,
Fibonacci y precios en tiempo real para tomar decisiones de compra/venta.
"""

import time
import argparse
from datetime import datetime
from src.data_provider import DataProvider
from src.account import Account
from src.trading_ai import TradingAI
from src.reporter import Reporter


class TradingEmulator:
    """Emulador principal de trading."""

    def __init__(self, symbol: str, initial_balance: float = 10000.0,
                 commission_rate: float = 0.001, risk_tolerance: float = 0.5,
                 min_confidence: int = 60, leverage: int = 1):
        """
        Inicializa el emulador.

        Args:
            symbol: Símbolo del activo (ej: 'BTC-USD', 'ETH-USD', 'AAPL')
            initial_balance: Balance inicial ficticio
            commission_rate: Tasa de comisión por operación
            risk_tolerance: Tolerancia al riesgo (0.0 a 1.0)
            min_confidence: Confianza mínima para ejecutar operaciones (0-100)
            leverage: Apalancamiento (1-100x)
        """
        self.symbol = symbol
        self.leverage = max(1, min(100, leverage))
        self.account = Account(initial_balance, commission_rate, self.leverage)
        self.ai = TradingAI(symbol, risk_tolerance, min_confidence, self.leverage)
        self.reporter = Reporter(self.account)
        self.data_provider = DataProvider(symbol)
        self.running = False

        # Intentar cargar cuenta existente
        self.account.load()

        print(f"\n{'='*70}")
        print(f"EMULADOR DE TRADING CON IA")
        print(f"{'='*70}")
        print(f"Símbolo: {symbol}")
        print(f"Balance Inicial: ${initial_balance:,.2f}")
        print(f"Comisión: {commission_rate * 100:.2f}%")
        print(f"Tolerancia al Riesgo: {risk_tolerance * 100:.0f}%")
        print(f"Confianza Mínima: {min_confidence}%")
        if self.leverage > 1:
            print(f"⚡ Apalancamiento: {self.leverage}x (ALTO RIESGO)")
        print(f"{'='*70}\n")

    def run_single_iteration(self):
        """Ejecuta una iteración del loop de trading."""
        try:
            # Obtener precio actual
            current_price = self.data_provider.get_current_price()

            if current_price <= 0:
                print("⚠️  No se pudo obtener precio actual")
                return

            print(f"\n{'='*70}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            print(f"Precio Actual {self.symbol}: ${current_price:,.2f}")

            # Mostrar información de balance y leverage
            if self.leverage > 1:
                available = self.account.get_available_balance()
                margin_used = self.account.get_total_margin_used()
                print(f"Balance Total: ${self.account.balance:,.2f}")
                print(f"Margen Usado: ${margin_used:,.2f}")
                print(f"Balance Disponible: ${available:,.2f}")
            else:
                print(f"Balance Disponible: ${self.account.balance:,.2f}")

            # VERIFICAR LIQUIDACIONES primero
            liquidated = self.account.check_liquidations({self.symbol: current_price})
            if liquidated:
                print(f"\n⚠️  Posiciones liquidadas: {', '.join(liquidated)}")
                return

            # Verificar posición actual
            position = self.account.get_position(self.symbol)
            current_position_price = position.entry_price if position else None
            position_size = position.amount if position else None

            if position:
                pnl = position.get_profit_loss(current_price)
                pnl_pct = position.get_profit_loss_percentage(current_price)
                pnl_emoji = "💰" if pnl >= 0 else "📉"
                leverage_str = f" [{position.leverage}x]" if position.leverage > 1 else ""
                print(f"{pnl_emoji} Posición Actual{leverage_str}: {position_size:.6f} unidades @ ${current_position_price:.2f}")
                print(f"   P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)")

                # Mostrar precio de liquidación si usa leverage
                if position.leverage > 1:
                    liq_price = position.get_liquidation_price()
                    distance_to_liq = ((current_price - liq_price) / current_price) * 100
                    print(f"   ⚠️  Precio Liquidación: ${liq_price:.2f} ({distance_to_liq:.1f}% de distancia)")

            # Tomar decisión de la IA
            print(f"\n🤖 Analizando mercado...")
            decision = self.ai.make_decision(
                self.account.balance,
                current_position_price,
                position_size
            )

            print(f"\n📊 Decisión de IA:")
            print(f"   Acción: {decision['action']}")
            print(f"   Confianza: {decision['confidence']}%")
            print(f"   Razones:")
            for reason in decision['reasons']:
                print(f"     • {reason}")

            # Ejecutar decisión
            if decision['action'] == 'BUY' and decision['amount'] > 0:
                investment_pct = decision.get('investment_percentage', 0)
                leverage_used = decision.get('leverage', self.leverage)
                leverage_info = f" con {leverage_used}x leverage" if leverage_used > 1 else ""
                print(f"\n💵 Ejecutando COMPRA{leverage_info} ({investment_pct:.1f}% del balance)...")
                self.account.buy(self.symbol, decision['amount'], current_price, leverage_used)

            elif decision['action'] == 'SELL' and decision['amount'] > 0:
                print(f"\n💰 Ejecutando VENTA...")
                self.account.sell(self.symbol, decision['amount'], current_price)

            else:
                print(f"\n⏸️  Manteniendo posición actual")

            # Mostrar resumen de cuenta
            summary = self.account.get_account_summary({self.symbol: current_price})
            total_return_emoji = "📈" if summary['total_return'] >= 0 else "📉"
            print(f"\n{total_return_emoji} Valor Total Cuenta: ${summary['total_value']:,.2f} "
                  f"({summary['total_return']:+.2f}%)")
            print(f"{'='*70}")

        except Exception as e:
            print(f"❌ Error en iteración: {e}")
            import traceback
            traceback.print_exc()

    def run_continuous(self, interval: int = 300):
        """
        Ejecuta el emulador en modo continuo.

        Args:
            interval: Intervalo entre iteraciones en segundos
        """
        self.running = True
        print(f"\n🚀 Iniciando emulador en modo continuo (intervalo: {interval}s)")
        print(f"   Presiona Ctrl+C para detener\n")

        iteration = 0

        try:
            while self.running:
                iteration += 1
                print(f"\n{'#'*70}")
                print(f"# ITERACIÓN {iteration}")
                print(f"{'#'*70}")

                self.run_single_iteration()

                if self.running:
                    print(f"\n⏳ Esperando {interval} segundos hasta próxima iteración...")
                    time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n\n🛑 Deteniendo emulador...")
            self.running = False

        finally:
            self.show_final_summary()

    def show_final_summary(self):
        """Muestra un resumen final al terminar."""
        print(f"\n{'='*70}")
        print(f"RESUMEN FINAL")
        print(f"{'='*70}")

        self.reporter.generate_full_report(include_chart=True)

    def show_report(self, period: str = 'day'):
        """
        Muestra un reporte de un período específico.

        Args:
            period: 'hour', 'day', 'week', 'month', 'all'
        """
        print(self.reporter.generate_period_report(period))

    def show_comparison_report(self):
        """Muestra un reporte comparativo de todos los períodos."""
        print(self.reporter.generate_comparison_report())

    def reset_account(self):
        """Reinicia la cuenta al estado inicial."""
        confirm = input("⚠️  ¿Estás seguro de reiniciar la cuenta? (s/n): ")
        if confirm.lower() == 's':
            self.account.reset()
        else:
            print("Operación cancelada")

    def show_strategy(self):
        """Muestra la descripción de la estrategia."""
        print(self.ai.get_strategy_description())


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Emulador de Trading con IA usando análisis técnico y Fibonacci'
    )

    parser.add_argument(
        '--symbol', '-s',
        type=str,
        default='BTC-USD',
        help='Símbolo del activo (ej: BTC-USD, ETH-USD, AAPL)'
    )

    parser.add_argument(
        '--balance', '-b',
        type=float,
        default=10000.0,
        help='Balance inicial ficticio (default: 10000)'
    )

    parser.add_argument(
        '--commission', '-c',
        type=float,
        default=0.001,
        help='Tasa de comisión (default: 0.001 = 0.1%%)'
    )

    parser.add_argument(
        '--risk', '-r',
        type=float,
        default=0.5,
        help='Tolerancia al riesgo 0-1 (default: 0.5)'
    )

    parser.add_argument(
        '--confidence', '-conf',
        type=int,
        default=60,
        help='Confianza mínima 0-100 (default: 60)'
    )

    parser.add_argument(
        '--leverage', '-lev',
        type=int,
        default=1,
        help='Apalancamiento 3-100x (default: 1 = sin leverage). ⚠️ ALTO RIESGO'
    )

    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=300,
        help='Intervalo entre operaciones en segundos (default: 300)'
    )

    parser.add_argument(
        '--mode', '-m',
        type=str,
        default='continuous',
        choices=['continuous', 'single', 'report', 'strategy', 'reset'],
        help='Modo de ejecución (default: continuous)'
    )

    parser.add_argument(
        '--period', '-p',
        type=str,
        default='day',
        choices=['hour', 'day', 'week', 'month', 'all'],
        help='Período para reportes (default: day)'
    )

    args = parser.parse_args()

    # Crear emulador
    emulator = TradingEmulator(
        symbol=args.symbol,
        initial_balance=args.balance,
        commission_rate=args.commission,
        risk_tolerance=args.risk,
        min_confidence=args.confidence,
        leverage=args.leverage
    )

    # Ejecutar según modo
    if args.mode == 'continuous':
        emulator.run_continuous(args.interval)

    elif args.mode == 'single':
        emulator.run_single_iteration()
        emulator.show_final_summary()

    elif args.mode == 'report':
        if args.period == 'all':
            emulator.reporter.generate_full_report(include_chart=True)
        else:
            emulator.show_report(args.period)
        emulator.show_comparison_report()

    elif args.mode == 'strategy':
        emulator.show_strategy()

    elif args.mode == 'reset':
        emulator.reset_account()


if __name__ == '__main__':
    main()
