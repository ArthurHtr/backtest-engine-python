from src.trade_tp.simple_broker.models.candle import Candle
from src.trade_tp.simple_broker.models.portfolio_snapshot import PortfolioSnapshot

from src.trade_tp.simple_broker.broker import BacktestBroker
from src.trade_tp.simple_broker.models.strategy import BaseStrategy, StrategyContext

from src.trade_tp.sdk.data_provider import DataProvider
from tqdm import tqdm
from collections import defaultdict

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
        Optimised: no scan O(N) des listes de candles à chaque timestamp.
        """
        snapshots: list[PortfolioSnapshot] = []
        self.snapshots = snapshots

        self.order_details = []
        candle_logs: list[dict] = []
        self.candle_logs = candle_logs

        # 1) Pré-indexation : timestamp (str) -> {symbol -> Candle}
        candles_by_timestamp: dict[str, dict[str, Candle]] = defaultdict(dict)

        for symbol, candles in candles_by_symbol.items():
            for candle in candles:
                ts = candle.timestamp  # c'est une str, ex: "2025-11-30T12:34:00"
                candles_by_timestamp[ts][symbol] = candle

        # 2) Liste triée des timestamps (ordre lexicographique OK avec ISO-8601)
        timestamps = sorted(candles_by_timestamp.keys())

        # Micro-optimisations : alias locaux
        broker = self.broker
        strategy = self.strategy
        append_snapshot = snapshots.append
        append_log = candle_logs.append

        # 3) Boucle principale
        for ts in tqdm(timestamps):
            current_candles = candles_by_timestamp[ts]
            if not current_candles:
                continue

            snapshot_before = broker.get_snapshot(current_candles)

            context = StrategyContext(
                candles=current_candles,
                portfolio_snapshot=snapshot_before,
            )

            order_intents = strategy.on_bar(context)

            snapshot_after, execution_details = broker.process_bars(
                current_candles,
                order_intents,
            )

            append_log({
                "timestamp": ts,
                "candles": current_candles,
                "snapshot_before": snapshot_before,
                "snapshot_after": snapshot_after,
                "order_intents": order_intents,
                "execution_details": execution_details,
            })

            append_snapshot(snapshot_after)

        return snapshots

