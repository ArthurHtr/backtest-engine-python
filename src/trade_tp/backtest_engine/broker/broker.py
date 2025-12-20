from typing import Dict, List, Tuple

from trade_tp.backtest_engine.entities.candle import Candle
from trade_tp.backtest_engine.entities.order_intent import OrderIntent
from trade_tp.backtest_engine.entities.portfolio_snapshot import PortfolioSnapshot
from trade_tp.backtest_engine.entities.symbol import Symbol
from trade_tp.backtest_engine.portfolio import Portfolio

from trade_tp.backtest_engine.broker.validator import OrderValidator
from trade_tp.backtest_engine.broker.liquidation import LiquidationManager

class BacktestBroker:
    """
    Broker simulé utilisé par le moteur de backtest.
    Orchestre la validation des ordres, la liquidation et la mise à jour du portefeuille.
    """

    def __init__(self, initial_cash: float, fee_rate: float, margin_requirement: float, maintenance_margin: float = 0.25, symbols_map: Dict[str, Symbol] = None):
        self.portfolio = Portfolio(initial_cash)
        self.fee_rate = fee_rate
        self.margin_requirement = margin_requirement
        self.maintenance_margin = maintenance_margin
        self.symbols_map = symbols_map or {}
        
        self.validator = OrderValidator(self.portfolio, fee_rate, margin_requirement, maintenance_margin, self.symbols_map)
        self.liquidation_manager = LiquidationManager(self.portfolio, maintenance_margin, fee_rate)

    def set_symbols_map(self, symbols_map: Dict[str, Symbol]):
        self.symbols_map = symbols_map
        self.validator.symbols_map = symbols_map

    def _build_price_map(self, candles: Dict[str, Candle]) -> Dict[str, float]:
        """
        Retourne un mapping symbol -> close price à partir d'un dictionnaire de
        bougies (candles). Filtre les entrées `None`.
        """
        return {symbol: c.close for symbol, c in candles.items() if c is not None}

    def get_snapshot(self, candles: Dict[str, Candle]):
        """
        Retourne l'instantané (snapshot) du portefeuille à partir des candles
        fournies. Utile pour afficher l'état avant le traitement des ordres.
        """
        price_by_symbol = self._build_price_map(candles)
        timestamp = next(iter(candles.values())).timestamp if candles else ""
        return self.portfolio.build_snapshot(price_by_symbol, timestamp)

    def process_bars(self, candles: Dict[str, Candle], order_intents: List[OrderIntent]) -> Tuple[PortfolioSnapshot, List[Dict]]:
        """
        Traite un ensemble d'ordres pour la barre courante.
        """
        execution_details: List[Dict] = []

        price_by_symbol = self._build_price_map(candles)
        timestamp = next(iter(candles.values())).timestamp if candles else ""

        # 1. Vérification des appels de marge sur les positions existantes
        liquidation_details = self.liquidation_manager.check_margin_call(candles, price_by_symbol, timestamp)
        execution_details.extend(liquidation_details)

        # 2. Traitement des intentions d'ordres
        for intent in order_intents:
            detail, trade = self.validator.validate_and_build_trade(intent, price_by_symbol=price_by_symbol, timestamp=timestamp)
            
            if trade is not None:
                # Essayer d'appliquer le trade ; Portfolio.apply_trade
                # simule et refuse si la maintenance margin est insuffisante.
                accepted, reason = self.portfolio.apply_trade(trade, price_by_symbol, self.maintenance_margin)

                if not accepted:
                    execution_details.append({"intent": intent, "status": "rejected", "reason": reason})
                    continue

                execution_details.append({"intent": intent, "status": "executed", "trade": trade})
            else:
                execution_details.append(detail)

        snapshot = self.portfolio.build_snapshot(price_by_symbol, timestamp)

        return snapshot, execution_details
