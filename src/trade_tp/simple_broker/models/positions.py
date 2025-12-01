from __future__ import annotations
from typing import Optional, Tuple
from src.trade_tp.simple_broker.models.enums import PositionSide

class Position:
    """
    Représente une position ouverte (LONG ou SHORT) sur un symbole donné.
    Gère:
    - moyenne de prix d'entrée
    - fermeture partielle / totale / reverse
    - realized PnL au niveau de la position
    """

    def __init__(self, symbol: str, side: PositionSide, quantity: float, entry_price: float, realized_pnl: float = 0.0) -> None:
        self.symbol = symbol
        self.side = side
        self.quantity = float(quantity)
        self.entry_price = abs(float(entry_price))
        self.realized_pnl = float(realized_pnl)

    def update(self, qty: float, price: float) -> Tuple[Optional["Position"], float]:
        """
        Update la position existante.

        Paramètres
        ----------
        qty : float
            Quantité du trade (BUY > 0, SELL < 0).
        price : float
            Prix du trade.

        Retourne
        --------
        (new_position, realized_pnl_delta)
            - new_position : self modifiée, une nouvelle position, ou None si la position est totalement fermée.
            - realized_pnl_delta : PnL réalisé généré par CE trade.
        """
        if qty == 0:
            return self, 0.0

        current_qty = self.quantity
        entry_price = self.entry_price
        realized_delta = 0.0

        # ======================
        # Position LONG
        # ======================
        if self.side == PositionSide.LONG:
            if qty > 0:
                # On ajoute au long existant (moyenne du prix d'entrée)
                new_qty = current_qty + qty
                self.entry_price = (entry_price * current_qty + price * qty) / new_qty
                self.quantity = new_qty
                return self, 0.0

            # qty < 0 -> on vend du long (fermeture partielle / totale / reverse)
            sell_qty = -qty  # > 0

            if sell_qty < current_qty:
                # Fermeture partielle
                close_qty = sell_qty
                realized_delta = (price - entry_price) * close_qty
                self.realized_pnl += realized_delta

                self.quantity = current_qty - close_qty
                return self, realized_delta

            elif sell_qty == current_qty:
                # Fermeture totale
                close_qty = current_qty
                realized_delta = (price - entry_price) * close_qty
                self.realized_pnl += realized_delta

                return None, realized_delta

            else:
                # Reverse: on ferme le long et on ouvre un short
                close_qty = current_qty
                realized_delta = (price - entry_price) * close_qty
                self.realized_pnl += realized_delta

                remaining_short = sell_qty - current_qty  # > 0

                self.side = PositionSide.SHORT
                self.quantity = remaining_short
                self.entry_price = price

                return self, realized_delta

        # ======================
        # Position SHORT
        # ======================
        elif self.side == PositionSide.SHORT:
            if qty < 0:
                # On augmente le short (SELL supplémentaire)
                add_qty = -qty  # > 0
                new_qty = current_qty + add_qty
                self.entry_price = (entry_price * current_qty + price * add_qty) / new_qty
                self.quantity = new_qty
                return self, 0.0

            # qty > 0 -> BUY pour couvrir le short (fermeture partielle / totale / reverse)
            buy_qty = qty  # > 0

            if buy_qty < current_qty:
                # Couverture partielle
                close_qty = buy_qty
                realized_delta = (entry_price - price) * close_qty
                self.realized_pnl += realized_delta

                self.quantity = current_qty - close_qty
                return self, realized_delta

            elif buy_qty == current_qty:
                # Couverture totale
                close_qty = current_qty
                realized_delta = (entry_price - price) * close_qty
                self.realized_pnl += realized_delta

                return None, realized_delta

            else:
                # Reverse : on couvre le short puis on ouvre un long
                close_qty = current_qty
                realized_delta = (entry_price - price) * close_qty
                self.realized_pnl += realized_delta

                remaining_long = buy_qty - current_qty  # > 0

                self.side = PositionSide.LONG
                self.quantity = remaining_long
                self.entry_price = price

                return self, realized_delta

        # Fallback théorique
        return self, 0.0
