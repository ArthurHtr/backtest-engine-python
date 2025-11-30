from typing import Dict, List, Tuple

from simple_broker.models.enums import PositionSide, Side
from simple_broker.models.candle import Candle
from simple_broker.models.trade import Trade
from simple_broker.models.order_intent import OrderIntent
from simple_broker.models.portfolio_snapshot import PortfolioSnapshot

from simple_broker.portfolio import PortfolioState


class BacktestBroker:
    """
    Simulates a broker for backtesting, supporting long and short positions.
    """

    def __init__(self, initial_cash: float, fee_rate: float, margin_requirement: float = 0.5):
        self.portfolio = PortfolioState(initial_cash)
        self.fee_rate = fee_rate
        self.margin_requirement = margin_requirement

    def _compute_equity(self, price_by_symbol: Dict[str, float]) -> float:
        """
        Compute portfolio equity = cash + sum(unrealized PnL) given prices.
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

    def _validate_and_build_trade(self, intent: OrderIntent, price_by_symbol: Dict[str, float], timestamp: str) -> Tuple[Dict, Trade | None]:
        """
        Valide un ordre et, si accepté, construit le Trade correspondant.
        Gère :
        - long / short
        - fermeture partielle / totale
        - reverse implicite (LONG -> SHORT, SHORT -> LONG)
        - marge uniquement sur la partie short.
        """
        symbol = intent.symbol

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
        qty = intent.quantity
        notional = qty * price
        fee = abs(notional) * self.fee_rate

        position = self.portfolio.positions.get(symbol)

        # BUY
        if intent.side == Side.BUY:
            # Cas 1 : position SHORT existante
            if position is not None and position.side == PositionSide.SHORT:
                current_qty = abs(position.quantity)

                if qty <= current_qty:
                    # Couverture partielle ou totale du short : pas de nouvelle marge.
                    # On ne fait qu'acheter pour couvrir, Position fera le détail.
                    pass
                else:
                    # Reverse implicite : on couvre tout le short puis on ouvre un long
                    # sur la quantité excédentaire. Le long est "cash only", pas de marge.
                    # On n'a donc pas d'autre contrôle que le cash ci-dessous.
                    pass

            # Cas 2 : pas de position ou déjà LONG
            # Vérification du cash pour l'achat complet (cover + éventuel long)
            total_cost = notional + fee
            if self.portfolio.cash < total_cost:
                return (
                    {
                        "intent": intent,
                        "status": "rejected",
                        "reason": "Insufficient cash.",
                    },
                    None,
                )

            trade_quantity = qty

        # SELL
        elif intent.side == Side.SELL:
            # Cas 1 : position LONG existante
            if position is not None and position.side == PositionSide.LONG:
                current_qty = position.quantity

                if qty <= current_qty:
                    # Vente dans la limite du long : fermeture partielle/totale.
                    # Pas de nouvelle exposition short : pas de marge.
                    trade_quantity = -qty

                else:
                    # Reverse implicite : on vend plus que la taille du long.
                    extra_short = qty - current_qty
                    extra_notional = extra_short * price
                    required_margin = abs(extra_notional) * self.margin_requirement
                    equity = self._compute_equity(price_by_symbol)

                    if equity < required_margin:
                        return (
                            {
                                "intent": intent,
                                "status": "rejected",
                                "reason": "Insufficient margin for reverse.",
                            },
                            None,
                        )

                    # On laisse Position.apply_trade gérer
                    trade_quantity = -qty  

            else:
                # Cas 2 : pas de position ou déjà SHORT
                # SELL ouvre ou augmente un short.
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

                trade_quantity = -qty 

        else:
            return (
                {
                    "intent": intent,
                    "status": "rejected",
                    "reason": f"Unsupported side: {intent.side}",
                },
                None,
            )

        # Construction du Trade
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

    def get_snapshot(self, candles: Dict[str, Candle]):
        """
        Returns a snapshot of the portfolio before processing orders
        for multiple symbols.
        """
        price_by_symbol = self._build_price_map(candles)
        timestamp = next(iter(candles.values())).timestamp if candles else ""
        return self.portfolio.build_snapshot(price_by_symbol, timestamp)

    def process_bars(self, candles: Dict[str, Candle], order_intents: List[OrderIntent]) -> Tuple[PortfolioSnapshot, List[Dict]]:
        """
        Processes multiple bars (one per symbol) and executes the given order intents.
        Uses a single, coherent validation logic (cash, quantity, margin).
        """
        execution_details: List[Dict] = []

        price_by_symbol = self._build_price_map(candles)
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
