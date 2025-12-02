from src.trade_tp.simple_broker.models.candle import Candle
from src.trade_tp.simple_broker.models.portfolio_snapshot import PortfolioSnapshot
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
        candles_logs: list[dict] = []
        self.order_details: list[dict] = []
        past_candles: dict[str, list[Candle]] = {symbol: [] for symbol in candles_by_symbol.keys()}

        candles_by_timestamp: dict[str, dict[str, Candle]] = defaultdict(dict)

        for symbol, candles in candles_by_symbol.items():
            for candle in candles:
                ts = candle.timestamp  # c'est une str, ex: "2025-11-30T12:34:00"
                candles_by_timestamp[ts][symbol] = candle

        timestamps = sorted(candles_by_timestamp.keys())

        # Boucle principale
        for ts in tqdm(timestamps):
            current_candles = candles_by_timestamp[ts]
            if not current_candles:
                continue

            for symbol in candles_by_symbol.keys():
                c = current_candles.get(symbol)
                if c is not None:
                    past_candles[symbol].append(c)

            snapshot_before = self.broker.get_snapshot(current_candles)

            context = StrategyContext(
                candles=current_candles,
                portfolio_snapshot=snapshot_before,
                past_candles=past_candles,
            )

            order_intents = self.strategy.on_bar(context)

            snapshot_after, execution_details = self.broker.process_bars(
                current_candles,
                order_intents,
            )

            snapshots.append(snapshot_after)
 
            candles_logs.append({
                "timestamp": ts,
                "candles": current_candles,
                "snapshot_before": snapshot_before,
                "snapshot_after": snapshot_after,
                "order_intents": order_intents,
                "execution_details": execution_details,
            })

        return candles_logs

