from simple_broker.models import Candle, PortfolioSnapshot
from simple_broker.broker import BacktestBroker
from simple_broker.strategy import BaseStrategy, StrategyContext, MultiSymbolStrategyContext
from market_sdk.data_provider import DataProvider
from market_sdk.exporter import Exporter

class BacktestEngine:
    """
    Runs the backtest loop.
    """
    def __init__(self, broker: BacktestBroker, strategy: BaseStrategy, data_provider: DataProvider):
        self.broker = broker
        self.strategy = strategy
        self.data_provider = data_provider

    def run(self, candles: list[Candle]) -> list[PortfolioSnapshot]:
        """
        Executes the backtest loop.
        Tracks order intents, executions, rejections, and detailed candle-by-candle data.
        """
        snapshots = []
        self.snapshots = snapshots  # Store snapshots for export
        self.order_details = []  # Track order intents and execution details
        self.candle_logs = []  # Detailed logs for each candle

        for candle in candles:
            print(f"Processing candle: {candle}")
            snapshot_before = self.broker.get_snapshot(candle)

            context = StrategyContext(
                candle=candle,
                symbol=candle.symbol,
                portfolio_snapshot=snapshot_before
            )

            order_intents = self.strategy.on_bar(context)

            snapshot_after, execution_details = self.broker.process_bar(candle, order_intents)

            # Log detailed candle data
            self.candle_logs.append({
                "candle": candle,
                "snapshot_before": snapshot_before,
                "snapshot_after": snapshot_after,
                "order_intents": order_intents,
                "execution_details": execution_details
            })

            snapshots.append(snapshot_after)

        final_context = StrategyContext(
            candle=candles[-1],
            symbol=candles[-1].symbol,
            portfolio_snapshot=self.broker.get_snapshot(candles[-1])
        )
        final_order_intents = self.strategy.on_end(final_context)
        final_snapshot, final_execution_details = self.broker.process_bar(candles[-1], final_order_intents)
        snapshots.append(final_snapshot)

        # Log final candle data
        self.candle_logs.append({
            "candle": candles[-1],
            "snapshot_before": snapshot_before,
            "snapshot_after": final_snapshot,
            "order_intents": final_order_intents,
            "execution_details": final_execution_details
        })

        return snapshots

    def export_results(self, exporter: Exporter):
        """
        Export backtest results using the provided exporter.
        Includes detailed candle-by-candle logs.
        """
        results = {
            "snapshots": self.snapshots,
            "strategy": self.strategy.__class__.__name__,
            "orders": self.order_details,
            "candle_logs": self.candle_logs
        }
        exporter.export_to_db(results)

    def run_multi_symbol(self, candles_by_symbol: dict[str, list[Candle]]) -> list[PortfolioSnapshot]:
        """
        Executes the backtest loop for multiple symbols.
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
            # Removed print statements for cleaner console output
            current_candles = {}

            for symbol, candles in candles_by_symbol.items():
                matching_candles = [candle for candle in candles if candle.timestamp == timestamp]
                if matching_candles:
                    current_candles[symbol] = matching_candles[0]

            if not current_candles:
                continue

            snapshot_before = self.broker.get_snapshot(current_candles)

            context = MultiSymbolStrategyContext(
                candles=current_candles,
                portfolio_snapshot=snapshot_before
            )

            order_intents = self.strategy.on_bar(context)

            # Assign order IDs to each intent
            for intent in order_intents:
                intent.order_id = intent.order_id  # Ensure order_id is set

            snapshot_after, execution_details = self.broker.process_bars(current_candles, order_intents)

            # Assign trade IDs to execution details
            for detail in execution_details:
                if "trade" in detail and detail["trade"]:
                    detail["trade"].trade_id = detail["trade"].trade_id

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