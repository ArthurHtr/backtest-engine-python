from src.trade_tp.backtest_engine.models.strategy import BaseStrategy, StrategyContext
from src.trade_tp.backtest_engine.models.order_intent import OrderIntent
from src.trade_tp.backtest_engine.models.enums import Side
from typing import List


# ------------------------------ strategie utilisateur ------------------------------ #


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
                    quantity=100  # Fixed quantity to buy
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

# ------------------------------ exécution du backtest ------------------------------ #

from src.trade_tp.runner import run_backtest

if __name__ == "__main__":

    result = run_backtest(
        symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
        start="2025-11-01T00:00:00",
        end="2025-11-30T00:00:00",
        timeframe="1h",

        initial_cash=100_000.0,

        strategy = BuyAndHoldStrategy(
            buy_timestamp="2025-11-01T00:00:00",
            sell_timestamp="2025-11-30T00:00:00"
        ),

        seed=42,
        api_key="YOUR_API_KEY_HERE",
        base_url="https://api.your-backtest-platform.com",
        run_id="user_backtest_001",
        
        fee_rate=0.001,
        margin_requirement=0.5,

        save_results=True,
    )

    