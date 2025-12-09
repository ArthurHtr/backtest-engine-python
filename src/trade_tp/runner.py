from __future__ import annotations

from typing import Any, Dict, List, Optional

from .simulated_market_data.data_provider import DataProvider as SimDataProvider

from .backtest_engine.broker import BacktestBroker
from .engine import BacktestEngine
from .backtest_engine.models.strategy import BaseStrategy

from .remote.exporters import ResultExporter
from .remote.client import TradeTpClient


def logs_visualisation(candles_logs, filepath: str = "backtest_analysis.txt") -> None:
    """
    Analyse et export du backtest dans un fichier texte lisible.
    """
    with open(filepath, "w") as file:
        file.write("Backtest Analysis\n")
        file.write("=================\n\n")

        for step_idx, log in enumerate(candles_logs, start=1):
            candles = log.get("candles")
            snapshot_before = log["snapshot_before"]
            snapshot_after = log["snapshot_after"]
            order_intents = log["order_intents"]
            execution_details = log["execution_details"]
            timestamp = log.get("timestamp")

            # En-tête du step
            if timestamp:
                file.write(f"Step {step_idx} - Timestamp: {timestamp}\n")
            else:
                file.write(f"Step {step_idx}\n")

            file.write("-" * 80 + "\n")

            # Candles
            if candles:
                file.write("Candles:\n")
                for symbol, candle in candles.items():
                    file.write(
                        f"  {symbol}: "
                        f"O={candle.open:.2f}, "
                        f"H={candle.high:.2f}, "
                        f"L={candle.low:.2f}, "
                        f"C={candle.close:.2f}, "
                        f"V={candle.volume}\n"
                    )
            else:
                # Fallback pour un seul symbole
                candle = log["candle"]
                file.write("Candle:\n")
                file.write(
                    f"  {candle.symbol}: "
                    f"O={candle.open:.2f}, "
                    f"H={candle.high:.2f}, "
                    f"L={candle.low:.2f}, "
                    f"C={candle.close:.2f}, "
                    f"V={candle.volume}\n"
                )

            file.write("\n")

            # Portfolio avant
            file.write("Portfolio Before:\n")
            file.write(f"  Cash:   {snapshot_before.cash:,.2f}\n")
            file.write(f"  Equity: {snapshot_before.equity:,.2f}\n")

            positions_before = snapshot_before.summarize_positions()
            if positions_before:
                file.write("  Positions:\n")
                for symbol, details in positions_before.items():
                    file.write(
                        f"    {symbol}: "
                        f"Side={details['side']}, "
                        f"Qty={details['quantity']}, "
                        f"Entry={details['entry_price']:.2f}, "
                        f"Realized PnL={details['realized_pnl']:.2f}\n"
                    )
            else:
                file.write("  Positions: (none)\n")

            file.write("\n")

            # Intents
            file.write("Order Intents:\n")
            if order_intents:
                for intent in order_intents:
                    file.write(
                        "  - "
                        f"OrderID={intent.order_id}, "
                        f"Symbol={intent.symbol}, "
                        f"Side={intent.side}, "
                        f"Qty={intent.quantity}, "
                        f"Type={intent.order_type}, "
                        f"Limit={intent.limit_price}\n"
                    )
            else:
                file.write("  (none)\n")

            file.write("\n")

            # Détails d'exécution
            file.write("Execution Details:\n")
            if execution_details:
                for detail in execution_details:
                    status = detail["status"]
                    reason = detail.get("reason", "N/A")
                    trade = detail.get("trade")
                    intent = detail.get("intent")

                    if intent is not None:
                        order_id = intent.order_id
                        file.write(
                            f"  - OrderID={order_id}, "
                            f"Status={status}, "
                            f"Reason={reason}\n"
                        )
                    else:
                        # liquidation or internal event without an explicit intent
                        file.write(
                            f"  - Event: {status}, Reason={reason}\n"
                        )

                    if trade:
                        file.write(
                            f"    TradeID={getattr(trade, 'trade_id', 'N/A')}, "
                            f"Qty={trade.quantity}, "
                            f"Price={trade.price:.4f}, "
                            f"Fee={trade.fee:.4f}, "
                            f"Time={trade.timestamp}\n"
                        )
            else:
                file.write("  (none)\n")

            file.write("\n")

            # Portfolio après
            file.write("Portfolio After:\n")
            file.write(f"  Cash:   {snapshot_after.cash:,.2f}\n")
            file.write(f"  Equity: {snapshot_after.equity:,.2f}\n")

            positions_after = snapshot_after.summarize_positions()
            if positions_after:
                file.write("  Positions:\n")
                for symbol, details in positions_after.items():
                    file.write(
                        f"    {symbol}: "
                        f"Side={details['side']}, "
                        f"Qty={details['quantity']}, "
                        f"Entry={details['entry_price']:.2f}, "
                        f"Realized PnL={details['realized_pnl']:.2f}\n"
                    )
            else:
                file.write("  Positions: (none)\n")

            file.write("\n\n")

def run_backtest(
    symbols: List[str],
    start: str,
    end: str,
    timeframe: str,

    initial_cash: float,

    strategy: BaseStrategy,

    seed: Optional[int],
    api_key: Optional[str],
    base_url: str,
    run_id: Optional[str],

    fee_rate: float,
    margin_requirement: float,

    save_results: bool = True,
) -> Dict[str, Any]:
    
    """Convenience function to run a backtest as a library user would.

    Parameters:
    - symbols, start, end, timeframe: data selection
    - strategy: instance or factory for a `BaseStrategy` implementation
    - api_key/base_url: if api_key provided, use remote provider + allow export
    - export_results: if True and remote enabled, post `candles_logs` to server

    Returns a dict with keys `candles_logs`
    """

    client = TradeTpClient(
        base_url=base_url, 
        api_key=api_key
    )

    data_provider = SimDataProvider(
        seed=seed,
        base_price=100.0,
        drift=0.1,
        volatility=0.02,
        base_daily_volume=1_000_000,
    )

    candles_by_symbol = data_provider.get_multiple_candles(
        symbols=symbols,
        start=start, 
        end=end, 
        timeframe=timeframe
    )

    broker = BacktestBroker(
        initial_cash=initial_cash,
        fee_rate=fee_rate, 
        margin_requirement=margin_requirement
    )

    engine = BacktestEngine(
        broker=broker, 
        strategy=strategy, 
        data_provider=data_provider
    )

    candles_logs = engine.run(candles_by_symbol)

    if save_results:
        logs_visualisation(candles_logs, filepath="backtest_analysis.txt")

    
