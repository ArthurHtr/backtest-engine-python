import random
from simple_broker.models import Candle, OrderIntent, Side
from simple_broker.broker import BacktestBroker
from simple_broker.strategy import BaseStrategy, StrategyContext
from simple_broker.engine import BacktestEngine
from market_sdk.data_provider import DataProvider
from market_sdk.exporter import Exporter
import matplotlib.pyplot as plt
from simple_broker.moving_average_strategy import AlternatingStrategy

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

    def on_end(self, context: StrategyContext):
        """
        Called at the end of the backtest to liquidate all positions.
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

# Fetch market data using DataProvider
candles = data_provider.get_candles(symbol="AAPL", start="2025-11-01", end="2025-11-30")

# Validate fetched candles
if not candles:
    raise ValueError("No candle data fetched. Please check the DataProvider or input parameters.")

# Initialiser les composants
initial_cash = 10000
fee_rate = 0.001
broker = BacktestBroker(initial_cash=initial_cash, fee_rate=fee_rate)
strategy = AlternatingStrategy()
engine = BacktestEngine(broker=broker, strategy=strategy, data_provider=data_provider)

# Lancer le backtest
snapshots = engine.run(candles)

# Export results
engine.export_results(exporter=exporter)

# Afficher les résultats
for snapshot in snapshots:
    print(snapshot)
