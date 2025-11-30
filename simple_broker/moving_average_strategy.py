from simple_broker.models import OrderIntent, Side
from simple_broker.strategy import BaseStrategy, StrategyContext, MultiSymbolStrategyContext

class AlternatingStrategy(BaseStrategy):
    def __init__(self):
        self.counter = 0

    def on_bar(self, context: MultiSymbolStrategyContext):
        """
        Alternates between buying and selling every 10 candles for multiple symbols.
        """
        self.counter += 1
        order_intents = []

        for symbol, candle in context.candles.items():
            if self.counter % 20 == 10:
                # Buy signal every 10th candle
                order_intents.append(OrderIntent(symbol=symbol, side=Side.BUY, quantity=100))
            elif self.counter % 20 == 0:
                # Sell signal every 20th candle
                order_intents.append(OrderIntent(symbol=symbol, side=Side.SELL, quantity=100))

        return []

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