import random
from simple_broker.models import Candle, OrderIntent, Side
from simple_broker.broker import BacktestBroker
from simple_broker.strategy import BaseStrategy, StrategyContext
from simple_broker.engine import BacktestEngine

# Exemple de stratégie améliorée avec gestion des positions longues et courtes
class MomentumStrategy(BaseStrategy):
    def __init__(self):
        self.previous_close = None

    def on_bar(self, context: StrategyContext):
        orders = []
        if self.previous_close is not None:
            # Acheter si le prix actuel est supérieur au prix précédent (momentum haussier)
            if context.candle.close > self.previous_close:
                orders.append(OrderIntent(symbol=context.symbol, side=Side.BUY, quantity=10))
            # Vendre si le prix actuel est inférieur au prix précédent (momentum baissier)
            elif context.candle.close < self.previous_close:
                orders.append(OrderIntent(symbol=context.symbol, side=Side.SELL, quantity=10))
        self.previous_close = context.candle.close
        return orders

# Générer des données de marché (OHLCV) avec du hasard
candles = []
base_price = 100
for i in range(1000):
    open_price = base_price + random.uniform(-5, 5)
    high_price = open_price + random.uniform(0, 10)
    low_price = open_price - random.uniform(0, 10)
    close_price = low_price + random.uniform(0, high_price - low_price)
    volume = 1000 + random.randint(-200, 200)
    candles.append(Candle(
        symbol="AAPL",
        timestamp=f"2025-11-29T10:{str(i).zfill(2)}:00Z",
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        volume=volume
    ))

# Initialiser les composants
initial_cash = 10000
fee_rate = 0.001
broker = BacktestBroker(initial_cash=initial_cash, fee_rate=fee_rate)
strategy = MomentumStrategy()
engine = BacktestEngine(broker=broker, strategy=strategy)

# Lancer le backtest
snapshots = engine.run(candles)

# Afficher les résultats
for snapshot in snapshots:
    print(snapshot)