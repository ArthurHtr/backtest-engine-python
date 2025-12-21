# Trade TP - Backtest Engine

A lightweight and flexible Python backtesting engine designed for testing trading strategies.

## Features

- **Event-driven Architecture**: Simulates market data replay candle by candle.
- **Strategy Interface**: Easy-to-implement `BaseStrategy` class.
- **Remote & Local Execution**: Run backtests locally or connect to a remote platform.
- **Detailed Reporting**: Generates comprehensive logs and metrics (PnL, Drawdown, etc.).

## Installation

You can install the package directly from the source:

```bash
pip install -e .
```

## Usage

### Defining a Strategy

Create a new class inheriting from `BaseStrategy`:

```python
from trade_tp.backtest_engine.strategy.base import BaseStrategy
from trade_tp.backtest_engine.entities.order_intent import OrderIntent, OrderSide, OrderType

class MyStrategy(BaseStrategy):
    def on_bar(self, context):
        # Your logic here
        pass
```

### Running a Backtest

```python
from trade_tp import run_backtest
from my_strategy import MyStrategy

strategy = MyStrategy()

results = run_backtest(
    run_id="test_run",
    api_key="your_api_key",
    strategy=strategy,
    save_local=True
)
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
