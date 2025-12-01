from simple_broker.strategy import BaseStrategy
from simple_broker.models.order_intent import OrderIntent
from simple_broker.models.enums import Side
from simple_broker.models.positions import PositionSide

class SimpleBuySellStrategy(BaseStrategy):
    """
    A simple strategy that alternates between buying and selling a fixed quantity of a symbol.
    """

    def __init__(self, quantity: int = 10):
        """
        Initialize the strategy with a fixed quantity to trade.
        :param quantity: The number of units to buy or sell on each bar.
        """
        self.quantity = quantity

    def on_bar(self, context):
        """
        Called for each new bar of market data.
        :param context: Contains market data, portfolio state, etc.
        :return: List of OrderIntent objects.
        """
        order_intents = []

        positions = {pos.symbol: pos for pos in context.portfolio_snapshot.positions}

        for symbol, candle in context.candles.items():
            position = positions.get(symbol)

            # Define a simple condition based on price movement
            if position is None:
                # If no position, buy if the price is below a threshold (e.g., moving average)
                if candle.close < candle.open:  # Example condition: price is decreasing
                    order_intents.append(OrderIntent(
                        symbol=symbol,
                        side=Side.BUY,
                        quantity=self.quantity,
                        order_type='MARKET'
                    ))
            elif position.side == PositionSide.LONG:
                # If long, sell if the price has increased significantly
                if candle.close > candle.open * 1.01:  # Example condition: price increased by 1%
                    order_intents.append(OrderIntent(
                        symbol=symbol,
                        side=Side.SELL,
                        quantity=position.quantity,
                        order_type='MARKET'
                    ))
            elif position.side == PositionSide.SHORT:
                # If short, buy to cover if the price has decreased significantly
                if candle.close < candle.open * 0.99:  # Example condition: price decreased by 1%
                    order_intents.append(OrderIntent(
                        symbol=symbol,
                        side=Side.BUY,
                        quantity=position.quantity,
                        order_type='MARKET'
                    ))

        return order_intents