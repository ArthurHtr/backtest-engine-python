import unittest
from simple_broker.portfolio import PortfolioState
from simple_broker.broker import BacktestBroker
from simple_broker.models import Position, Trade, Side, Candle, OrderIntent

class TestLongShortPositions(unittest.TestCase):

    def setUp(self):
        self.broker = BacktestBroker(initial_cash=100000, fee_rate=0.001)
        self.portfolio = self.broker.portfolio

    def test_long_position(self):
        candle = Candle(symbol="AAPL", timestamp="2023-01-01", open=150, high=155, low=145, close=150, volume=1000)
        order = OrderIntent(symbol="AAPL", side=Side.BUY, quantity=10)
        self.broker.process_bar(candle, [order])
        position = self.portfolio.positions.get("AAPL")
        self.assertIsNotNone(position)
        self.assertEqual(position.quantity, 10)
        self.assertEqual(position.entry_price, 150)

    def test_short_position(self):
        candle = Candle(symbol="AAPL", timestamp="2023-01-01", open=150, high=155, low=145, close=150, volume=1000)
        order = OrderIntent(symbol="AAPL", side=Side.SELL, quantity=10)
        self.broker.process_bar(candle, [order])
        position = self.portfolio.positions.get("AAPL")
        self.assertIsNotNone(position)
        self.assertEqual(position.quantity, -10)
        self.assertEqual(position.entry_price, 150)

    def test_realized_pnl(self):
        candle1 = Candle(symbol="AAPL", timestamp="2023-01-01", open=150, high=155, low=145, close=150, volume=1000)
        candle2 = Candle(symbol="AAPL", timestamp="2023-01-02", open=160, high=165, low=155, close=160, volume=1000)
        buy_order = OrderIntent(symbol="AAPL", side=Side.BUY, quantity=10)
        sell_order = OrderIntent(symbol="AAPL", side=Side.SELL, quantity=10)
        self.broker.process_bar(candle1, [buy_order])
        self.broker.process_bar(candle2, [sell_order])
        position = self.portfolio.positions.get("AAPL")
        self.assertIsNone(position)  # Position should be closed
        fee = (150 * 10 + 160 * 10) * 0.001  # Total fees for buy and sell
        self.assertAlmostEqual(self.portfolio.cash, 100000 + (160 - 150) * 10 - fee, places=2)  # Realized PnL added to cash

if __name__ == "__main__":
    unittest.main()