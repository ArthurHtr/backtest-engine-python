from src.trade_tp.simple_broker.models.strategy import BaseStrategy, StrategyContext
from src.trade_tp.simple_broker.models.order_intent import OrderIntent
from src.trade_tp.simple_broker.models.enums import Side

class BuyAndHoldStrategy(BaseStrategy):
    """
    A simple Buy and Hold strategy that buys a fixed quantity of each symbol at the first timestamp
    and sells all positions at the last timestamp.
    """
    def __init__(self, buy_timestamp: str = "2025-11-01T00:00:00", sell_timestamp: str = "2025-11-30T00:00:00"):
        self.first_timestamp = buy_timestamp
        self.last_timestamp = sell_timestamp

    def on_bar(self, context: StrategyContext):

        order_intents = []

        timestamp = context.candles[next(iter(context.candles))].timestamp

        # Place buy orders only at the first timestamp
        if timestamp == self.first_timestamp:
            for symbol in context.candles.keys():
                order_intents.append(OrderIntent(
                    symbol=symbol,
                    side=Side.BUY,
                    quantity=50  # Fixed quantity to buy
                ))

        # Place sell orders only at the last timestamp
        if timestamp == self.last_timestamp:
            for position in context.portfolio_snapshot.positions:
                order_intents.append(OrderIntent(
                    symbol=position.symbol,
                    side=Side.SELL,
                    quantity=position.quantity  # Sell the entire position
                ))

        return order_intents