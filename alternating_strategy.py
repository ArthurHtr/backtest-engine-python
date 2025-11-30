from simple_broker.models import OrderIntent, Side
from simple_broker.strategy import BaseStrategy, StrategyContext, MultiSymbolStrategyContext

class AlternatingStrategy(BaseStrategy):
    def __init__(self):
        self.counter = 0

    def on_bar(self, context: MultiSymbolStrategyContext):
        """
        Executes a sequence of 3 buys, followed by 6 sells, then 6 buys, and repeats.
        """
        self.counter += 1
        order_intents = []

        for symbol, candle in context.candles.items():
            sequence = self.counter % 15

            if 1 <= sequence <= 3:
                # Buy signal for the first 3 steps in the sequence
                order_intents.append(OrderIntent(symbol=symbol, side=Side.BUY, quantity=1))
            elif 4 <= sequence <= 9:
                # Sell signal for the next 6 steps in the sequence
                order_intents.append(OrderIntent(symbol=symbol, side=Side.SELL, quantity=1))
            elif 10 <= sequence <= 15:
                # Buy signal for the last 6 steps in the sequence
                order_intents.append(OrderIntent(symbol=symbol, side=Side.BUY, quantity=1))

        return order_intents

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