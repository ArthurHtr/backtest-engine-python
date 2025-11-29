from simple_broker.models import Candle, PortfolioSnapshot
from simple_broker.broker import BacktestBroker
from simple_broker.strategy import BaseStrategy, StrategyContext

class BacktestEngine:
    """
    Runs the backtest loop.
    """
    def __init__(self, broker: BacktestBroker, strategy: BaseStrategy):
        self.broker = broker
        self.strategy = strategy

    def run(self, candles: list[Candle]) -> list[PortfolioSnapshot]:
        """
        Executes the backtest loop.
        """
        snapshots = []

        for candle in candles:
            # Get portfolio snapshot before strategy decision
            snapshot_before = self.broker.get_snapshot(candle)

            # Create strategy context
            context = StrategyContext(
                candle=candle,
                symbol=candle.symbol,
                portfolio_snapshot=snapshot_before
            )

            # Get order intents from strategy
            order_intents = self.strategy.on_bar(context)

            # Process orders and get portfolio snapshot after execution
            snapshot_after = self.broker.process_bar(candle, order_intents)

            # Store the snapshot
            snapshots.append(snapshot_after)

        return snapshots