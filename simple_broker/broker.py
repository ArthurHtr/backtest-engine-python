from typing import Dict, List, Tuple

from simple_broker.models import Candle, OrderIntent, Trade, Side, PositionSide
from simple_broker.portfolio import PortfolioState


class BacktestBroker:
    """
    Simulates a broker for backtesting, supporting long and short positions
    with a simple margin model.
    """

    def __init__(self, initial_cash: float, fee_rate: float):
        self.portfolio = PortfolioState(initial_cash)
        self.fee_rate = fee_rate
        # 50% margin requirement for short positions (notional * margin_requirement)
        self.margin_requirement = 0.5

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _compute_equity(self, price_by_symbol: Dict[str, float]) -> float:
        """
        Compute portfolio equity = cash + sum(unrealized PnL) given prices.
        If a symbol price is missing, fallback to entry_price for that symbol.
        """
        equity = self.portfolio.cash

        for symbol, pos in self.portfolio.positions.items():
            price = price_by_symbol.get(symbol, pos.entry_price)

            if pos.side == PositionSide.LONG:
                # quantity supposée positive pour LONG
                equity += (price - pos.entry_price) * pos.quantity
            elif pos.side == PositionSide.SHORT:
                # on prend abs pour être robuste même si quantity est signée
                qty = abs(pos.quantity)
                equity += (pos.entry_price - price) * qty

        return equity

    def _build_price_map(self, candles: Dict[str, Candle]) -> Dict[str, float]:
        return {symbol: c.close for symbol, c in candles.items() if c is not None}

    def _validate_and_build_trade(
        self,
        intent: OrderIntent,
        price_by_symbol: Dict[str, float],
        timestamp: str,
    ) -> Tuple[Dict, Trade | None]:
        """
        Valide un ordre et, si accepté, construit le Trade correspondant.

        Retourne:
            (execution_detail_dict, trade or None)
        """
        symbol = intent.symbol

        # Récupération du prix
        if symbol not in price_by_symbol:
            return (
                {
                    "intent": intent,
                    "status": "rejected",
                    "reason": "No price available for symbol.",
                },
                None,
            )

        price = price_by_symbol[symbol]
        notional = intent.quantity * price  # intent.quantity > 0 par convention
        fee = abs(notional) * self.fee_rate

        pos = self.portfolio.positions.get(symbol)

        # ---------------------------------------------------------------------
        # BUY
        # ---------------------------------------------------------------------
        if intent.side == Side.BUY:
            # Cas : on couvre un short
            if pos is not None and pos.side == PositionSide.SHORT:
                # On interdit pour l'instant de dépasser la taille du short
                if abs(pos.quantity) < intent.quantity:
                    return (
                        {
                            "intent": intent,
                            "status": "rejected",
                            "reason": "Insufficient short quantity to cover.",
                        },
                        None,
                    )

            # Vérification du cash
            total_cost = notional + fee  # notional >= 0 si quantity > 0
            if self.portfolio.cash < total_cost:
                return (
                    {
                        "intent": intent,
                        "status": "rejected",
                        "reason": "Insufficient cash.",
                    },
                    None,
                )

            trade_quantity = intent.quantity  # BUY = trade.quantity > 0

        # ---------------------------------------------------------------------
        # SELL
        # ---------------------------------------------------------------------
        elif intent.side == Side.SELL:
            # Si position LONG existante : on ne permet que la fermeture partielle/totale,
            # pas de reverse implicite.
            if pos is not None and pos.side == PositionSide.LONG:
                if pos.quantity < intent.quantity:
                    return (
                        {
                            "intent": intent,
                            "status": "rejected",
                            "reason": "Insufficient long quantity to sell.",
                        },
                        None,
                    )
                # Vente de long -> pas de nouvelle marge short à calculer.
                # On laisse passer si la quantité est suffisante.

            else:
                # Ici : soit pas de position, soit position SHORT.
                # SELL ouvre ou augmente un short -> vérification de marge.
                required_margin = abs(notional) * self.margin_requirement
                equity = self._compute_equity(price_by_symbol)

                if equity < required_margin:
                    return (
                        {
                            "intent": intent,
                            "status": "rejected",
                            "reason": "Insufficient margin.",
                        },
                        None,
                    )

            trade_quantity = -intent.quantity  # SELL = trade.quantity < 0

        else:
            return (
                {
                    "intent": intent,
                    "status": "rejected",
                    "reason": f"Unsupported side: {intent.side}",
                },
                None,
            )

        # ---------------------------------------------------------------------
        # Construction du Trade si tout est OK
        # ---------------------------------------------------------------------
        trade = Trade(
            symbol=symbol,
            quantity=trade_quantity,
            price=price,
            fee=fee,
            timestamp=timestamp,
        )

        return (
            {
                "intent": intent,
                "status": "executed",
                "trade": trade,
            },
            trade,
        )

    # -------------------------------------------------------------------------
    # API publique
    # -------------------------------------------------------------------------

    def get_snapshot(self, candles: Dict[str, Candle]):
        """
        Returns a snapshot of the portfolio before processing orders
        for multiple symbols.
        """
        price_by_symbol = self._build_price_map(candles)
        timestamp = next(iter(candles.values())).timestamp if candles else ""
        return self.portfolio.build_snapshot(price_by_symbol, timestamp)

    def process_bars(
        self,
        candles: Dict[str, Candle],
        order_intents: List[OrderIntent],
    ):
        """
        Processes multiple bars (one per symbol) and executes the given order intents.
        Uses a single, coherent validation logic (cash, quantity, margin).
        """
        execution_details: List[Dict] = []

        price_by_symbol = self._build_price_map(candles)
        # Choix : timestamp commun = timestamp du premier candle
        timestamp = next(iter(candles.values())).timestamp if candles else ""

        for intent in order_intents:
            detail, trade = self._validate_and_build_trade(
                intent,
                price_by_symbol=price_by_symbol,
                timestamp=timestamp,
            )

            if trade is not None:
                # On applique le trade (mise à jour cash + positions)
                self.portfolio.apply_trade(trade)

            execution_details.append(detail)

        snapshot = self.portfolio.build_snapshot(price_by_symbol, timestamp)
        return snapshot, execution_details

    def process_bar(
        self,
        candle: Candle,
        order_intents: List[OrderIntent],
    ):
        """
        Wrapper single-symbole : réutilise la même logique que process_bars.
        """
        candles = {candle.symbol: candle}
        return self.process_bars(candles, order_intents)
