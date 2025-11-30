from simple_broker.broker import BacktestBroker
from simple_broker.engine import BacktestEngine
from market_sdk.data_provider import DataProvider
from market_sdk.exporter import Exporter
from alternating_strategy import AlternatingStrategy


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
strategy = AlternatingStrategy()
engine = BacktestEngine(broker=broker, strategy=strategy, data_provider=data_provider)

# Run the backtest for multiple symbols
snapshots = engine.run_multi_symbol(candles_by_symbol)

# Export results
engine.export_results(exporter=exporter)

# Display the results
for snapshot in snapshots:
    print(snapshot)
