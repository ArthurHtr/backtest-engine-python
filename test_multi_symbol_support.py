import unittest
from simple_broker.models import Candle, PortfolioSnapshot, OrderIntent, Side
from simple_broker.broker import BacktestBroker
from simple_broker.engine import BacktestEngine
from simple_broker.strategy import BaseStrategy, MultiSymbolStrategyContext
from market_sdk.data_provider import DataProvider

class MultiSymbolTestStrategy(BaseStrategy):
    def on_bar(self, context: MultiSymbolStrategyContext):
        order_intents = []
        for symbol, candle in context.candles.items():
            if candle and candle.close < 100:
                order_intents.append(OrderIntent(symbol=symbol, side=Side.BUY, quantity=10))
        return order_intents

class TestMultiSymbolSupport(unittest.TestCase):
    def setUp(self):
        self.broker = BacktestBroker(initial_cash=10000, fee_rate=0.001)
        self.data_provider = DataProvider(api_key="test_key")
        self.strategy = MultiSymbolTestStrategy()
        self.engine = BacktestEngine(broker=self.broker, strategy=self.strategy, data_provider=self.data_provider)

    def test_multi_symbol_backtest(self):
        candles_by_symbol = {
            "AAPL": [Candle("AAPL", "2025-11-01T00:00:00", 95, 100, 90, 95, 1000)],
            "GOOG": [Candle("GOOG", "2025-11-01T00:00:00", 105, 110, 100, 105, 1000)]
        }

        snapshots = self.engine.run_multi_symbol(candles_by_symbol)

        self.assertEqual(len(snapshots), 1)
        self.assertEqual(len(self.broker.portfolio.positions), 1)
        self.assertIn("AAPL", self.broker.portfolio.positions)
        self.assertEqual(self.broker.portfolio.positions["AAPL"].quantity, 10)

if __name__ == "__main__":
    unittest.main()