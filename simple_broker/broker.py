from simple_broker.models import Candle, OrderIntent, Trade
from simple_broker.portfolio import PortfolioState

class BacktestBroker:
    """
    Simulates a broker for backtesting.
    """
    def __init__(self, initial_cash: float, fee_rate: float):
        self.portfolio = PortfolioState(initial_cash)
        self.fee_rate = fee_rate

    def get_snapshot(self, candle: Candle):
        """
        Returns a snapshot of the portfolio before processing orders.
        """
        return self.portfolio.build_snapshot({candle.symbol: candle.close}, candle.timestamp)

    def process_bar(self, candle: Candle, order_intents: list[OrderIntent]):
        """
        Processes a single bar (candle) and executes the given order intents.
        """
        for intent in order_intents:
            if intent.order_type == "MARKET":
                price = candle.close
                fee = abs(intent.quantity * price) * self.fee_rate
                trade = Trade(
                    symbol=intent.symbol,
                    quantity=intent.quantity,
                    price=price,
                    fee=fee,
                    timestamp=candle.timestamp
                )
                self.portfolio.apply_trade(trade)

        return self.portfolio.build_snapshot({candle.symbol: candle.close}, candle.timestamp)