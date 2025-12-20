from trade_tp.backtest_engine.entities.position import Position

from dataclasses import dataclass
from typing import List
from trade_tp.backtest_engine.entities.position import Position

@dataclass(frozen=True)
class PortfolioSnapshot:
    """
    Snapshot immuable (vue) de l'état du portefeuille à un instant donné.
    Immuable.

    Champs
    - timestamp (str): horodatage du snapshot
    - cash (float): liquidités disponibles
    - equity (float): valeur nette (cash + market value des positions)
    - positions (list[Position]): liste des positions au moment du snapshot

    Ce type est utilisé par les stratégies pour décider des actions (OrderIntent)
    et par la sortie d'analyse pour afficher l'état du portefeuille.
    """
    timestamp: str
    cash: float
    equity: float
    positions: List[Position]

    def summarize_positions(self):
        """
        Retourne un dictionnaire synthétique des positions, indexé par symbole.
        """
        return {
            position.symbol: {
                "side": position.side.name,
                "quantity": position.quantity,
                "entry_price": position.entry_price,
            }
            for position in self.positions
        }
