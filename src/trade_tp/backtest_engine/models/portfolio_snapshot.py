from trade_tp.backtest_engine.models.positions import Position

class PortfolioSnapshot:
    """
    Snapshot immuable (vue) de l'état du portefeuille à un instant donné.

    Champs
    - timestamp (str): horodatage du snapshot
    - cash (float): liquidités disponibles
    - equity (float): valeur nette (cash + market value des positions)
    - positions (list[Position]): liste des positions au moment du snapshot

    Ce type est utilisé par les stratégies pour décider des actions (OrderIntent)
    et par la sortie d'analyse pour afficher l'état du portefeuille.
    """

    def __init__(self, timestamp: str, cash: float, equity: float, positions: list[Position]):
        self.timestamp = timestamp
        self.cash = cash
        self.equity = equity
        self.positions = positions

    def summarize_positions(self):
        """
        Retourne un dictionnaire synthétique des positions, indexé par symbole.

        Format de retour
        {
            symbol: {
                "side": "LONG"|"SHORT",
                "quantity": float,
                "entry_price": float,
                "realized_pnl": float,
            },
            ...
        }
        """
        return {
            position.symbol: {
                "side": position.side.name,
                "quantity": position.quantity,
                "entry_price": position.entry_price,
                "realized_pnl": position.realized_pnl
            }
            for position in self.positions
        }
