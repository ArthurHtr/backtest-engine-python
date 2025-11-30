from simple_broker.broker import BacktestBroker
from simple_broker.engine import BacktestEngine
from market_sdk.data_provider import DataProvider
from market_sdk.exporter import Exporter
from my_strategies.buy_and_hold_strategy import BuyAndHoldStrategy


# Initialize SDK components
data_provider = DataProvider(api_key="your_api_key")
exporter = Exporter(db_config={"host": "localhost", "port": 5432})

# Fetch market data for multiple symbols using DataProvider
symbols = ["AAPL", "GOOG"]  # Reduced the number of symbols for faster processing
candles_by_symbol = data_provider.get_multiple_candles(symbols=symbols, start="2025-11-01", end="2025-11-30")  # Shortened the date range

# Initialize components
initial_cash = 20000
fee_rate = 0.001
broker = BacktestBroker(initial_cash=initial_cash, fee_rate=fee_rate)
strategy = BuyAndHoldStrategy()
engine = BacktestEngine(broker=broker, strategy=strategy, data_provider=data_provider)

# Run the backtest for multiple symbols
snapshots = engine.run(candles_by_symbol)

def analyze_backtest(candle_logs):
    with open("backtest_analysis.txt", "w") as file:
        file.write("Backtest Analysis\n")
        file.write("================\n\n")

        for i, log in enumerate(candle_logs):
            candles = log.get("candles")
            if candles:
                for symbol, candle in candles.items():
                    file.write(f"Step {i + 1} - Symbol: {symbol}\n")
                    file.write(f"Candle: Time={candle.timestamp}, Open={candle.open}, High={candle.high}, Low={candle.low}, Close={candle.close}, Volume={candle.volume}\n")
            else:
                candle = log["candle"]  # Fallback for single-symbol logs
                file.write(f"Step {i + 1}:\n")
                file.write(f"Candle: Symbol={candle.symbol}, Time={candle.timestamp}, Open={candle.open}, High={candle.high}, Low={candle.low}, Close={candle.close}, Volume={candle.volume}\n")

            snapshot_before = log["snapshot_before"]
            snapshot_after = log["snapshot_after"]
            order_intents = log["order_intents"]
            execution_details = log["execution_details"]

            file.write("Portfolio Before:\n")
            file.write(f"  Cash: {snapshot_before.cash:.2f}, Equity: {snapshot_before.equity:.2f}\n")
            file.write("  Positions:\n")
            for symbol, details in snapshot_before.summarize_positions().items():
                file.write(f"    {symbol}: Side={details['side']}, Quantity={details['quantity']}, Entry Price={details['entry_price']:.2f}, Realized PnL={details['realized_pnl']:.2f}\n")

            file.write("Order Intents:\n")
            for intent in order_intents:
                file.write(f"  - Order ID={intent.order_id}, Symbol={intent.symbol}, Side={intent.side}, Quantity={intent.quantity}, Type={intent.order_type}, Limit Price={intent.limit_price}\n")

            file.write("Execution Details:\n")
            for detail in execution_details:
                status = detail["status"]
                reason = detail.get("reason", "N/A")
                trade = detail.get("trade")
                order_id = detail["intent"].order_id  # Retrieve order ID
                file.write(f"  - Order ID={order_id}, Status={status}, Reason={reason}\n")
                if trade:
                    file.write(f"    Trade ID={trade.trade_id}, Quantity={trade.quantity}, Price={trade.price}, Fee={trade.fee}, Timestamp={trade.timestamp}\n")

            file.write("Portfolio After:\n")
            file.write(f"  Cash: {snapshot_after.cash:.2f}, Equity: {snapshot_after.equity:.2f}\n")
            file.write("  Positions:\n")
            for symbol, details in snapshot_after.summarize_positions().items():
                file.write(f"    {symbol}: Side={details['side']}, Quantity={details['quantity']}, Entry Price={details['entry_price']:.2f}, Realized PnL={details['realized_pnl']:.2f}\n")

            file.write("\n")

analyze_backtest(engine.candle_logs)
print("Backtest analysis written to backtest_analysis.txt")

