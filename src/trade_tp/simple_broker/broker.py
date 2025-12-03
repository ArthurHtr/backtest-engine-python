from typing import Dict, List, Tuple

from src.trade_tp.simple_broker.models.enums import PositionSide, Side
from src.trade_tp.simple_broker.models.candle import Candle
from src.trade_tp.simple_broker.models.trade import Trade
from src.trade_tp.simple_broker.models.order_intent import OrderIntent
from src.trade_tp.simple_broker.models.portfolio_snapshot import PortfolioSnapshot

from src.trade_tp.simple_broker.portfolio import PortfolioState


class BacktestBroker:
    """
    Simulates a broker for backtesting, supporting long and short positions.
    """

    def __init__(self, initial_cash: float, fee_rate: float, margin_requirement: float, maintenance_margin: float = 0.25):
        self.portfolio = PortfolioState(initial_cash)
        self.fee_rate = fee_rate
        self.margin_requirement = margin_requirement
        # maintenance_margin is the fraction of a position's notional that must be
        # covered by equity to avoid forced liquidation (e.g., 0.25 = 25%).
        self.maintenance_margin = maintenance_margin

    def _compute_equity(self, price_by_symbol: Dict[str, float]) -> float:
        """
        Compute portfolio equity = cash + sum(unrealized PnL) given prices.
        """
        # Equity should be calculated as cash + market value of positions
        # to remain consistent with PortfolioState.build_snapshot.
        equity = self.portfolio.cash

        for symbol, pos in self.portfolio.positions.items():
            price = price_by_symbol.get(symbol, pos.entry_price)

            if pos.side == PositionSide.LONG:
                # market value of a long position
                market_value = price * pos.quantity
            elif pos.side == PositionSide.SHORT:
                # market value of a short is negative
                market_value = -price * abs(pos.quantity)
            else:
                market_value = 0.0

            equity += market_value

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

                    # Simulate equity after closing the existing long (before opening the short):
                    # closing the long generates proceeds = current_qty * price which
                    # increase cash; then we compute market value of other symbols.
                    proceeds_close = current_qty * price
                    cash_after_close = self.portfolio.cash + proceeds_close - fee

                    other_market = 0.0
                    for s, p in self.portfolio.positions.items():
                        if s == symbol:
                            continue
                        p_price = price_by_symbol.get(s, p.entry_price)
                        if p.side == PositionSide.LONG:
                            other_market += p_price * p.quantity
                        else:
                            other_market += -p_price * abs(p.quantity)

                    equity_after_close = cash_after_close + other_market

                    # Also check maintenance margin: if executing this reverse would
                    # immediately put equity below maintenance threshold for the new
                    # short exposure, reject the intent up front to avoid execute+liquidate.
                    required_maint = abs(extra_notional) * self.maintenance_margin
                    if equity_after_close < required_maint:
                        return (
                            {
                                "intent": intent,
                                "status": "rejected",
                                "reason": "Would breach maintenance margin on reverse.",
                            },
                            None,
                        )

                    if equity_after_close < required_margin:
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

                # Simulate equity after executing the sell (opening/increasing short).
                # Selling increases cash by `notional` but also creates a short whose
                # market value is -notional, so the net effect on equity is mainly fees.
                cash_after = self.portfolio.cash + notional - fee

                other_market = 0.0
                for s, p in self.portfolio.positions.items():
                    if s == symbol:
                        continue
                    p_price = price_by_symbol.get(s, p.entry_price)
                    if p.side == PositionSide.LONG:
                        other_market += p_price * p.quantity
                    else:
                        other_market += -p_price * abs(p.quantity)

                equity_after = cash_after + other_market

                # Reject upfront if this would immediately breach maintenance margin
                # for the new short exposure (so we don't execute then forcibly close).
                required_maint = abs(notional) * self.maintenance_margin
                if equity_after < required_maint:
                    return (
                        {
                            "intent": intent,
                            "status": "rejected",
                            "reason": "Would breach maintenance margin.",
                        },
                        None,
                    )

                if equity_after < required_margin:
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

    def _enforce_maintenance_margin(self, price_by_symbol: Dict[str, float], timestamp: str) -> List[Dict]:
        """
        Enforce maintenance margin by liquidating short positions if equity
        falls below the maintenance requirement for that position.

        Returns a list of liquidation event dicts to be appended to execution details.
        """
        events: List[Dict] = []

        # Recompute equity and iterate over shorts ordered by notional (desc)
        equity = self._compute_equity(price_by_symbol)

        # Gather short positions with their current price and notional
        shorts = []
        for symbol, pos in list(self.portfolio.positions.items()):
            if pos.side == PositionSide.SHORT:
                price = price_by_symbol.get(symbol, pos.entry_price)
                notional = price * abs(pos.quantity)
                shorts.append((notional, symbol, pos, price))

        # Sort by largest notional first (liquidate largest risks first)
        shorts.sort(reverse=True, key=lambda x: x[0])

        for notional, symbol, pos, price in shorts:
            required_maint = notional * self.maintenance_margin

            # If equity is already sufficient, continue
            if equity >= required_maint:
                continue

            # Need to liquidate this short entirely (buy back quantity)
            close_qty = pos.quantity  # quantity is positive magnitude
            fee = abs(close_qty * price) * self.fee_rate

            # Build and apply buy trade to close the short
            trade = Trade(symbol=symbol, quantity=close_qty, price=price, fee=fee, timestamp=timestamp)
            self.portfolio.apply_trade(trade)

            # Recompute equity after liquidation
            equity = self._compute_equity(price_by_symbol)

            events.append({
                "intent": None,
                "status": "liquidated",
                "reason": "Maintenance margin breach - short position forcibly closed.",
                "trade": trade,
            })

            # If equity recovered above required_maint for remaining positions, continue
            # The loop will check next positions as equity has been updated.

        return events
