from typing import Dict, List, Optional

from trade_tp.backtest_engine.models.trade import Trade
from trade_tp.backtest_engine.models.enums import PositionSide
from trade_tp.backtest_engine.models.positions import Position
from trade_tp.backtest_engine.models.portfolio_snapshot import PortfolioSnapshot


class PortfolioState:
    """
    Représente l'état interne d'un portefeuille utilisé par le broker de
    backtest.

    Responsabilités
    - Conserver le `cash` disponible et un dictionnaire de `Position` par
      symbole.
    - Appliquer des `Trade` en vérifiant (par simulation) que la maintenance
      margin ne sera pas violée après l'exécution.
    - Construire un `PortfolioSnapshot` pour le reporting.

    Conventions importantes
    - `Trade.quantity > 0` signifie BUY, `< 0` signifie SELL.
    - `Position.quantity` est stockée comme une magnitude positive ; le côté
      (`Position.side`) indique LONG/SHORT.
    - Les reversals sont autorisés : un trade peut traverser 0 et convertir un
      long en short (ou inversement) en une seule opération.
    """

    def __init__(self, initial_cash: float):
        """Crée un nouvel état de portefeuille avec `initial_cash` disponible."""
        self.cash: float = initial_cash
        self.positions: Dict[str, Position] = {}

    def apply_trade(self, trade: Trade, price_by_symbol: Dict[str, float], maintenance_margin: float, check_margin: bool = True) -> tuple[bool, Optional[str]]:
        """
        Applique un `Trade` au portefeuille après une simulation conservatrice.

        Workflow
        1. Simuler l'état (cash et positions) immédiatement après le trade
           (sans modifier l'état réel).
        2. Calculer l'equity simulée (cash + market value des positions).
        3. Pour chaque position short simulée, vérifier que l'equity couvre la
           `maintenance_margin` requise. Si l'une des vérifications échoue,
           refuser le trade et ne pas muter l'état.
        4. Si toutes les vérifications passent, committer la simulation dans
           l'état réel (mise à jour du cash et des positions).

        Args:
            trade: instance de `Trade` contenant quantity, price et fees.
            price_by_symbol: mapping symbol -> price pour calculer les valeurs
              de marché.
            maintenance_margin: fraction (ex: 0.25) utilisée pour décider si un
              short doit être maintenu.
            check_margin: si True (défaut), vérifie la maintenance margin.
              Si False, applique le trade sans vérification (utile pour liquidation).

        Returns:
            tuple(bool, Optional[str]): (accepted, reason). Si `accepted` est
            False, `reason` explique le rejet et l'état n'a pas été modifié.
        """
        symbol = trade.symbol
        qty = float(trade.quantity)
        price = float(trade.price)
        fee = float(trade.fee)

        # --- Construire un état simulé après le trade ---
        cash_after = self.cash - qty * price - fee

        simulated_positions: Dict[str, Position] = {}
        for s, p in self.positions.items():
            simulated_positions[s] = Position(
                symbol=p.symbol,
                side=p.side,
                quantity=p.quantity,
                entry_price=p.entry_price,
            )

        pos = simulated_positions.get(symbol)
        if pos is None:
            side = PositionSide.LONG if qty > 0 else PositionSide.SHORT
            new_pos = Position(symbol=symbol, side=side, quantity=abs(qty), entry_price=price)
            simulated_positions[symbol] = new_pos
        else:
            new_position = pos.update(qty, price)
            if new_position is None:
                del simulated_positions[symbol]
            else:
                simulated_positions[symbol] = new_position

        # --- Calcul de l'equity simulée ---
        equity_after = cash_after
        for s, p in simulated_positions.items():
            p_price = price_by_symbol.get(s, p.entry_price)
            if p.side == PositionSide.LONG:
                equity_after += p_price * p.quantity
            else:
                equity_after += -p_price * abs(p.quantity)

        # --- Vérification de la maintenance margin pour les shorts ---
        if check_margin:
            for s, p in simulated_positions.items():
                if p.side == PositionSide.SHORT:
                    p_price = price_by_symbol.get(s, p.entry_price)
                    notional = p_price * abs(p.quantity)
                    required_maint = notional * maintenance_margin
                    if equity_after < required_maint:
                        return False, f"Would breach maintenance margin for {s}."

        # Commit : on remplace l'état réel par la simulation validée
        self.cash = cash_after
        self.positions = simulated_positions

        return True, None

    def build_snapshot(self, price_by_symbol: Dict[str, float], timestamp: str) -> PortfolioSnapshot:
        """
        Construit un `PortfolioSnapshot` décrivant l'état courant du portefeuille.

        Le snapshot contient : timestamp, cash, equity (cash + market value) et
        la liste des positions (copies). Le calcul de l'equity utilise les prix
        fournis dans `price_by_symbol` ; si un prix manque, la valeur stockée
        `entry_price` est utilisée comme fallback.

        Args:
            price_by_symbol: mapping symbol -> price actuel.
            timestamp: horodatage (string) de la barre.

        Returns:
            PortfolioSnapshot
        """
        equity = self.cash
        positions_snapshot: List[Position] = []

        for symbol, position in self.positions.items():
            current_price = price_by_symbol.get(symbol, position.entry_price)

            if position.side == PositionSide.LONG:
                market_value = current_price * position.quantity
            elif position.side == PositionSide.SHORT:
                market_value = -current_price * abs(position.quantity)
            else:
                market_value = 0.0

            equity += market_value

            positions_snapshot.append(
                Position(
                    symbol=position.symbol,
                    side=position.side,
                    quantity=position.quantity,
                    entry_price=position.entry_price,
                )
            )

        return PortfolioSnapshot(timestamp=timestamp, cash=self.cash, equity=equity, positions=positions_snapshot)