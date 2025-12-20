from typing import Dict, Tuple, Optional

from trade_tp.backtest_engine.entities.enums import PositionSide, Side
from trade_tp.backtest_engine.entities.trade import Trade
from trade_tp.backtest_engine.entities.order_intent import OrderIntent
from trade_tp.backtest_engine.entities.symbol import Symbol
from trade_tp.backtest_engine.portfolio import Portfolio

class OrderValidator:
    """
    Responsable de la validation des intentions d'ordres et de la construction des trades potentiels.
    """

    def __init__(self, portfolio: Portfolio, fee_rate: float, margin_requirement: float, maintenance_margin: float, symbols_map: Dict[str, Symbol]):
        self.portfolio = portfolio
        self.fee_rate = fee_rate
        self.margin_requirement = margin_requirement
        self.maintenance_margin = maintenance_margin
        self.symbols_map = symbols_map

    def validate_and_build_trade(self, intent: OrderIntent, price_by_symbol: Dict[str, float], timestamp: str) -> Tuple[Dict, Optional[Trade]]:
        """
        Valide une intention d'ordre et construit un `Trade` si l'ordre peut être accepté.
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

        # --- Rounding Logic ---
        sym_info = self.symbols_map.get(symbol)
        if sym_info:
            qty = sym_info.round_quantity(qty)
            
            if qty == 0:
                 return (
                    {
                        "intent": intent,
                        "status": "rejected",
                        "reason": "Quantity too small (below min_quantity or step).",
                    },
                    None,
                )
        # ----------------------

        notional = qty * price
        fee = abs(notional) * self.fee_rate

        position = self.portfolio.positions.get(symbol)

        # BUY
        if intent.side == Side.BUY:
            total_cost = notional + fee
            if self.portfolio.cash < total_cost:
                return (
                    {"intent": intent, "status": "rejected", "reason": "Insufficient cash."},
                    None,
                )

            trade_quantity = qty

        # SELL
        elif intent.side == Side.SELL:
            # Vente quand position LONG existante : fermeture partielle/totale
            if position is not None and position.side == PositionSide.LONG:
                current_qty = position.quantity

                if qty <= current_qty:
                    # Simple clôture partielle ou totale du long
                    trade_quantity = -qty

                else:
                    # Reverse implicite
                    extra_short = qty - current_qty
                    extra_notional = extra_short * price
                    required_margin = abs(extra_notional) * self.margin_requirement

                    # Simule les effets immédiats de la clôture du long
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

                    required_maint = abs(extra_notional) * self.maintenance_margin
                    if equity_after_close < required_maint:
                        return (
                            {"intent": intent, "status": "rejected", "reason": "Would breach maintenance margin on reverse."},
                            None,
                        )

                    if equity_after_close < required_margin:
                        return (
                            {"intent": intent, "status": "rejected", "reason": "Insufficient margin for reverse."},
                            None,
                        )

                    trade_quantity = -qty

            else:
                # Ouverture/augmentation d'un short
                required_margin = abs(notional) * self.margin_requirement

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

                required_maint = abs(notional) * self.maintenance_margin
                if equity_after < required_maint:
                    return (
                        {"intent": intent, "status": "rejected", "reason": "Would breach maintenance margin."},
                        None,
                    )

                if equity_after < required_margin:
                    return (
                        {"intent": intent, "status": "rejected", "reason": "Insufficient margin."},
                        None,
                    )

                trade_quantity = -qty

        else:
            return (
                {"intent": intent, "status": "rejected", "reason": f"Unsupported side: {intent.side}"},
                None,
            )

        trade = Trade(symbol=symbol, quantity=trade_quantity, price=price, fee=fee, timestamp=timestamp)

        return ({"intent": intent, "status": "executed", "trade": trade}, trade)
