import random
from simple_broker.models import Candle, OrderIntent, Side
from simple_broker.broker import BacktestBroker
from simple_broker.strategy import BaseStrategy, StrategyContext
from simple_broker.engine import BacktestEngine
from market_sdk.data_provider import DataProvider
from market_sdk.exporter import Exporter
import matplotlib.pyplot as plt

# Define a simple strategy that alternates between buying and selling for multiple symbols
class SimpleAlternatingStrategy(BaseStrategy):
    def __init__(self):
        self.last_actions = {}  # Track the last action for each symbol

    def on_bar(self, context: StrategyContext):
        """
        Alternates between buying and selling a fixed quantity for each symbol.
        """
        order_intents = []
        for symbol, candle in context.candles.items():
            last_action = self.last_actions.get(symbol)
            if last_action == "BUY":
                self.last_actions[symbol] = "SELL"
                order_intents.append(OrderIntent(symbol=symbol, side=Side.SELL, quantity=1))
            else:
                self.last_actions[symbol] = "BUY"
                order_intents.append(OrderIntent(symbol=symbol, side=Side.BUY, quantity=1))
        return order_intents

    def on_end(self, context: StrategyContext):
        """
        Liquidates all positions for all symbols at the end of the backtest.
        """
        order_intents = []
        for position in context.portfolio_snapshot.positions:
            if position.quantity > 0:
                order_intents.append(OrderIntent(
                    symbol=position.symbol,
                    side=Side.SELL,
                    quantity=position.quantity
                ))
        return order_intents

# Initialize SDK components
data_provider = DataProvider(api_key="your_api_key")
exporter = Exporter(db_config={"host": "localhost", "port": 5432})

# Fetch market data for multiple symbols using DataProvider
symbols = ["AAPL", "GOOG"]  # Reduced the number of symbols for faster processing
candles_by_symbol = data_provider.get_multiple_candles(symbols=symbols, start="2025-11-01", end="2025-11-07")  # Shortened the date range

# Validate fetched candles
if not any(candles_by_symbol.values()):
    raise ValueError("No candle data fetched for the provided symbols. Please check the DataProvider or input parameters.")

# Initialize components
initial_cash = 10000
fee_rate = 0.001
broker = BacktestBroker(initial_cash=initial_cash, fee_rate=fee_rate)
strategy = SimpleAlternatingStrategy()
engine = BacktestEngine(broker=broker, strategy=strategy, data_provider=data_provider)

# Run the backtest for multiple symbols
snapshots = engine.run_multi_symbol(candles_by_symbol)

# Export results
engine.export_results(exporter=exporter)

# Display the results
for snapshot in snapshots:
    print(snapshot)
