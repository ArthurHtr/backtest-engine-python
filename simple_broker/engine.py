from simple_broker.models.candle import Candle
from simple_broker.models.portfolio_snapshot import PortfolioSnapshot

from simple_broker.broker import BacktestBroker
from simple_broker.strategy import BaseStrategy, StrategyContext

from market_sdk.data_provider import DataProvider

class BacktestEngine:
    """
    Runs the backtest loop.
    """
    def __init__(self, broker: BacktestBroker, strategy: BaseStrategy, data_provider: DataProvider):
        self.broker = broker
        self.strategy = strategy
        self.data_provider = data_provider

    def run(self, candles_by_symbol: dict[str, list[Candle]]) -> list[PortfolioSnapshot]:
        """
        Executes the backtest loop.
        Tracks order intents, executions, rejections, and detailed candle-by-candle data.
        """
        snapshots = []
        self.snapshots = snapshots  # Store snapshots for export
        self.order_details = []  # Track order intents and execution details
        self.candle_logs = []  # Detailed logs for each candle

        # Align candles by timestamp
        all_timestamps = {c.timestamp for candles in candles_by_symbol.values() for c in candles}
        timestamps = sorted(all_timestamps)

        for timestamp in timestamps:
            
            current_candles = {}

            for symbol, candles in candles_by_symbol.items():
                matching_candles = [candle for candle in candles if candle.timestamp == timestamp]
                if matching_candles:
                    current_candles[symbol] = matching_candles[0]

            if not current_candles:
                continue

            snapshot_before = self.broker.get_snapshot(current_candles)

            context = StrategyContext(candles=current_candles, portfolio_snapshot=snapshot_before)

            order_intents = self.strategy.on_bar(context)

            snapshot_after, execution_details = self.broker.process_bars(current_candles, order_intents)

            # Log detailed candle data
            self.candle_logs.append({
                "candles": current_candles,
                "snapshot_before": snapshot_before,
                "snapshot_after": snapshot_after,
                "order_intents": order_intents,
                "execution_details": execution_details
            })

            snapshots.append(snapshot_after)

        return snapshots
    
