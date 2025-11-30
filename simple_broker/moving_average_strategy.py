from simple_broker.models import OrderIntent, Side
from simple_broker.strategy import BaseStrategy, StrategyContext

class AlternatingStrategy(BaseStrategy):
    def __init__(self):
        self.counter = 0

    def on_bar(self, context: StrategyContext):
        """
        Alternates between buying and selling every 10 candles.
        """
        self.counter += 1

        if self.counter % 20 == 10:
            # Buy signal every 10th candle
            return [OrderIntent(symbol=context.symbol, side=Side.BUY, quantity=100)]
        elif self.counter % 20 == 0:
            # Sell signal every 20th candle
            return [OrderIntent(symbol=context.symbol, side=Side.SELL, quantity=100)]

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