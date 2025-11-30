import random
from simple_broker.models import Candle, OrderIntent, Side
from simple_broker.broker import BacktestBroker
from simple_broker.strategy import BaseStrategy, StrategyContext
from simple_broker.engine import BacktestEngine

# Exemple de stratégie d'achat et de conservation
class BuyAndHoldStrategy(BaseStrategy):
    def on_bar(self, context: StrategyContext):
        """
        Implémente une stratégie d'achat et de conservation : acheter une quantité fixe de l'actif sur la première bougie et la conserver.
        """
        if context.portfolio_snapshot.positions:
            # Déjà en position, aucune action supplémentaire
            return []

        # Acheter 100 unités de l'actif sur la première bougie
        return [OrderIntent(symbol=context.symbol, side=Side.BUY, quantity=100)]

# Générer des données de marché (OHLCV) avec du hasard
candles = []
base_price = 100
volatility = 2  # Simule la volatilité du marché
trend = 0.1  # Simule une légère tendance à la hausse
for i in range(1000):
    open_price = base_price + random.uniform(-volatility, volatility)
    high_price = open_price + random.uniform(0, volatility * 2)
    low_price = open_price - random.uniform(0, volatility * 2)
    close_price = low_price + random.uniform(0, high_price - low_price)
    volume = 1000 + random.randint(-200, 200)

    # Simuler les tendances du marché
    base_price += trend + random.uniform(-volatility / 2, volatility / 2)

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
initial_cash = 100000
fee_rate = 0.001
broker = BacktestBroker(initial_cash=initial_cash, fee_rate=fee_rate)
strategy = BuyAndHoldStrategy()
engine = BacktestEngine(broker=broker, strategy=strategy)

# Lancer le backtest
snapshots = engine.run(candles)

# Afficher les résultats
for snapshot in snapshots:
    print(snapshot)