from typing import Dict, List

from src.trade_tp.simple_broker.models.candle import Candle
from src.trade_tp.simple_broker.models.portfolio_snapshot import PortfolioSnapshot

from src.trade_tp.simple_broker.broker import BacktestBroker
from src.trade_tp.simple_broker.models.strategy import BaseStrategy, StrategyContext

from src.trade_tp.simulated_market_data.data_provider import DataProvider
from tqdm import tqdm
from collections import defaultdict


class BacktestEngine:
    """
    Moteur principal de backtest.

    Rôle
    - Itère les candles fournies par symbole dans l'ordre temporel.
    - Pour chaque timestamp, construit le contexte strategy (candles,
        snapshot du portefeuille, historique) et appelle la stratégie via
        `strategy.on_bar` pour obtenir des `OrderIntent`.
    - Passe ensuite les intents au `BacktestBroker` qui valide et exécute
        (ou rejette) les ordres ; le moteur collecte les snapshots et détails
        d'exécution pour chaque barre.

    Contrat public
    - `run(candles_by_symbol)` retourne une liste d'entrées (one per timestamp)
        contenant les candles courantes, le snapshot avant/après, les intents et
        les détails d'exécution. Ce format est utilisé pour l'export/logging.
    """

    def __init__(self, broker: BacktestBroker, strategy: BaseStrategy, data_provider: DataProvider):
        self.broker = broker
        self.strategy = strategy
        self.data_provider = data_provider

    def run(self, candles_by_symbol: Dict[str, List[Candle]]) -> List[dict]:
        """
        Exécute la boucle de backtest sur les séries de candles données.

        Args:
            candles_by_symbol: mapping symbol -> liste ordonnée de Candle.

        Returns:
            List[dict]: liste d'objets contenant pour chaque timestamp :
                - timestamp
                - candles (mapping symbol->Candle)
                - snapshot_before
                - snapshot_after
                - order_intents
                - execution_details
        """
        snapshots: List[PortfolioSnapshot] = []
        candles_logs: List[dict] = []
        self.order_details: List[dict] = []
        past_candles: Dict[str, List[Candle]] = {symbol: [] for symbol in candles_by_symbol.keys()}

        candles_by_timestamp: Dict[str, Dict[str, Candle]] = defaultdict(dict)

        for symbol, candles in candles_by_symbol.items():
            for candle in candles:
                ts = candle.timestamp
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

            context = StrategyContext(candles=current_candles, portfolio_snapshot=snapshot_before, past_candles=past_candles)

            order_intents = self.strategy.on_bar(context)

            snapshot_after, execution_details = self.broker.process_bars(current_candles, order_intents)

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

