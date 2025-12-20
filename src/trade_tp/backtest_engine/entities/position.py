from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from trade_tp.backtest_engine.entities.enums import PositionSide

@dataclass(frozen=True)
class Position:
    """
    Représente une position ouverte (LONG ou SHORT) sur un symbole donné.

    Responsibilities
    - Maintenir la quantité et le prix d'entrée (moyenne pondérée lors d'ajouts)
    - Gérer les opérations de reverse (fermer puis ouvrir l'opposé)

    Conventions
    - Les quantités stockées dans `Position.quantity` sont des magnitudes (>= 0).
    - Le sens (LONG/SHORT) est dans `Position.side`.
    """
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float

    def update(self, qty: float, price: float) -> Optional["Position"]:
        """
        Met à jour la position à partir d'un trade et renvoie une NOUVELLE instance.
        Renvoie None si la position est fermée.
        """
        if qty == 0:
            return self

        # Déterminer si on augmente la position (même sens) ou si on réduit/reverse (sens opposé)
        is_increase = (self.side == PositionSide.LONG and qty > 0) or (self.side == PositionSide.SHORT and qty < 0)

        abs_qty = abs(qty)

        if is_increase:
            return self._increase_position(abs_qty, price)
        else:
            return self._reduce_or_reverse(abs_qty, price)

    def _increase_position(self, qty: float, price: float) -> "Position":
        """Ajoute à la position existante et met à jour le prix moyen."""
        new_qty = self.quantity + qty
        new_entry_price = (self.entry_price * self.quantity + price * qty) / new_qty
        
        return Position(
            symbol=self.symbol,
            side=self.side,
            quantity=new_qty,
            entry_price=new_entry_price
        )

    def _reduce_or_reverse(self, qty: float, price: float) -> Optional["Position"]:
        """Gère la fermeture partielle, totale ou le reverse."""
        if qty < self.quantity:
            # Fermeture partielle
            return Position(
                symbol=self.symbol,
                side=self.side,
                quantity=self.quantity - qty,
                entry_price=self.entry_price
            )

        elif qty == self.quantity:
            # Fermeture totale
            return None

        else:
            # Reverse
            remaining_qty = qty - self.quantity
            new_side = PositionSide.SHORT if self.side == PositionSide.LONG else PositionSide.LONG
            
            return Position(
                symbol=self.symbol,
                side=new_side,
                quantity=remaining_qty,
                entry_price=price
            )
