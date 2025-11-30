# Backtest Engine Python

## Overview
Backtest Engine Python is a modular and extensible Python library for backtesting trading strategies. It provides tools to simulate trading strategies, manage portfolio states, execute trades, and analyze results. The library supports both long and short positions, making it suitable for a wide range of trading strategies.

## Features
- **Market Data Handling**: Process OHLCV (Open, High, Low, Close, Volume) data.
- **Strategy Development**: Create custom strategies by subclassing the `BaseStrategy` class.
- **Trade Execution**: Simulate trade execution with a backtesting broker.
- **Portfolio Management**: Track positions, cash, and profit/loss.
- **Visualization**: Analyze backtest results with built-in visualization tools.

## Installation
To install the library, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/ArthurHtr/backtest-engine-python.git
   ```
2. Navigate to the project directory:
   ```bash
   cd backtest-engine-python
   ```
3. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Example Workflow
1. **Define a Strategy**: Subclass the `BaseStrategy` class and implement the `on_bar` method.
2. **Prepare Market Data**: Create a list of `Candle` objects representing historical market data.
3. **Initialize Components**: Set up the `BacktestBroker`, `BaseStrategy`, and `BacktestEngine`.
4. **Run the Backtest**: Use the `engine.run(candles)` method to execute the backtest.
5. **Analyze Results**: Use portfolio snapshots or visualization tools to evaluate performance.

### Code Example
```python
from simple_broker.engine import BacktestEngine
from simple_broker.broker import BacktestBroker
from simple_broker.strategy import BaseStrategy
from models.candle import Candle

class MyStrategy(BaseStrategy):
    def on_bar(self, context):
        # Example strategy logic
        return []

# Prepare market data
candles = [Candle(symbol="AAPL", timestamp=..., open=..., high=..., low=..., close=..., volume=...)]

# Initialize components
broker = BacktestBroker(initial_cash=10000)
strategy = MyStrategy()
engine = BacktestEngine(broker=broker, strategy=strategy)

# Run backtest
engine.run(candles)
```

## Project Structure
```
backtest-engine-python/
├── market_sdk/          # Market data handling
├── simple_broker/       # Backtesting engine and broker
├── models/              # Data models (e.g., Candle, Trade, Position)
├── analyze_backtest.py  # Analysis script
├── run_backtest.py      # Example backtest runner
└── README.md            # Project documentation
```

## Contributing
Contributions are welcome! If you'd like to contribute, please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.