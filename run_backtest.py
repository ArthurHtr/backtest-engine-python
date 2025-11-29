from simple_broker.models import Candle, OrderIntent, Side
from simple_broker.broker import BacktestBroker
from simple_broker.strategy import BaseStrategy, StrategyContext
from simple_broker.engine import BacktestEngine

# Exemple de stratégie simple
class ExampleStrategy(BaseStrategy):
    def on_bar(self, context: StrategyContext):
        # Exemple : Acheter 1 unité si le prix est inférieur à 100
        if context.candle.close < 100:
            return [OrderIntent(symbol=context.symbol, side=Side.BUY, quantity=1)]
        return []

# Exemple de données de marché (OHLCV)
candles = [
    Candle(symbol="AAPL", timestamp="2025-11-29T10:00:00Z", open=95, high=105, low=90, close=100, volume=1000),
    Candle(symbol="AAPL", timestamp="2025-11-29T10:01:00Z", open=100, high=110, low=95, close=105, volume=1200),
    Candle(symbol="AAPL", timestamp="2025-11-29T10:02:00Z", open=105, high=115, low=100, close=110, volume=1300),
    Candle(symbol="AAPL", timestamp="2025-11-29T10:03:00Z", open=90, high=120, low=85, close=90, volume=1400),
    Candle(symbol="AAPL", timestamp="2025-11-29T10:04:00Z", open=115, high=125, low=110, close=120, volume=1500),
    Candle(symbol="AAPL", timestamp="2025-11-29T10:05:00Z", open=120, high=130, low=115, close=125, volume=1600),
]

# Initialiser les composants
initial_cash = 10000
fee_rate = 0.001
broker = BacktestBroker(initial_cash=initial_cash, fee_rate=fee_rate)
strategy = ExampleStrategy()
engine = BacktestEngine(broker=broker, strategy=strategy)

# Lancer le backtest
snapshots = engine.run(candles)

# Afficher les résultats
for snapshot in snapshots:
    print(snapshot)