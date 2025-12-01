from src.trade_tp.simple_broker.broker import BacktestBroker
from src.trade_tp.engine import BacktestEngine
from src.trade_tp.sdk.data_provider import DataProvider

from buy_and_hold_strategy import BuyAndHoldStrategy


# Initialize SDK components
data_provider = DataProvider(api_key="your_api_key")

# Fetch market data for multiple symbols using DataProvider
symbols = data_provider.get_symbols(symbols=["AAPL", "GOOGL", "TSLA", "MSFT", "AMZN", "NFLX"])
candles_by_symbol = data_provider.get_multiple_candles(symbols=[s.symbol for s in symbols], start="2025-11-01", end="2025-11-30")  # Shortened the date range

# Initialize components
initial_cash = 60000
fee_rate = 0.001
broker = BacktestBroker(initial_cash=initial_cash, fee_rate=fee_rate)
strategy = BuyAndHoldStrategy(buy_timestamp="2025-11-01T00:00:00", sell_timestamp="2025-11-30T00:00:00")
engine = BacktestEngine(broker=broker, strategy=strategy, data_provider=data_provider)

# Run the backtest for multiple symbols
snapshots = engine.run(candles_by_symbol)

def analyze_backtest(candle_logs, filepath: str = "backtest_analysis.txt") -> None:
    """
    Analyse et export du backtest dans un fichier texte lisible.
    """
    with open(filepath, "w") as file:
        file.write("Backtest Analysis\n")
        file.write("=================\n\n")

        for step_idx, log in enumerate(candle_logs, start=1):
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
                    order_id = detail["intent"].order_id

                    file.write(
                        f"  - OrderID={order_id}, "
                        f"Status={status}, "
                        f"Reason={reason}\n"
                    )

                    if trade:
                        file.write(
                            f"    TradeID={trade.trade_id}, "
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


analyze_backtest(engine.candle_logs)
print("Backtest analysis written to backtest_analysis.txt")

