from src.trade_tp.simple_broker.models.trade import Trade
from src.trade_tp.simple_broker.models.enums import PositionSide
from src.trade_tp.simple_broker.models.positions import Position
from src.trade_tp.simple_broker.models.portfolio_snapshot import PortfolioSnapshot

class PortfolioState:
    """
    Manages the internal state of the portfolio, supporting long and short positions.

    Conventions:
      - Trade.quantity > 0 : BUY
      - Trade.quantity < 0 : SELL
      - Position.quantity  : strictly positive magnitude
      - Position.side      : LONG or SHORT

    On autorise un trade unique à traverser 0 (reverse):
      - LONG + gros SELL -> fermeture du long puis ouverture d'un short
      - SHORT + gros BUY -> couverture du short puis ouverture d'un long
    """

    def __init__(self, initial_cash: float):
        self.cash: float = initial_cash
        self.positions: dict[str, Position] = {}

    def apply_trade(self, trade: Trade, price_by_symbol: dict, maintenance_margin: float) -> tuple[bool, str | None]:
        """
        Met à jour le portefeuille à partir d'un trade exécuté, mais effectue
        d'abord une simulation pour vérifier que la maintenance margin ne
        serait pas violée après l'exécution.

        Parameters
        - trade: Trade à appliquer (contient fee)
        - price_by_symbol: mapping des prix courants pour calculer market values
        - maintenance_margin: fraction (e.g., 0.25) utilisée pour le seuil de maintenance

        Returns (accepted: bool, reason: Optional[str])
        - If accepted is False, the portfolio is not modified and reason gives the rejection cause.
        - If accepted is True, the trade is applied and reason is None.
        """
        symbol = trade.symbol
        qty = float(trade.quantity)
        price = float(trade.price)
        fee = float(trade.fee)

        # --- Build a simulated portfolio state after the trade ---
        # shallow copy cash
        cash_after = self.cash - qty * price - fee

        # clone positions dict with new Position instances to avoid mutating real ones
        simulated_positions: dict[str, Position] = {}
        for s, p in self.positions.items():
            simulated_positions[s] = Position(
                symbol=p.symbol,
                side=p.side,
                quantity=p.quantity,
                entry_price=p.entry_price,
                realized_pnl=p.realized_pnl,
            )

        # apply the trade to the simulated position for the symbol
        pos = simulated_positions.get(symbol)
        if pos is None:
            # opening new position
            side = PositionSide.LONG if qty > 0 else PositionSide.SHORT
            new_pos = Position(
                symbol=symbol,
                side=side,
                quantity=abs(qty),
                entry_price=price,
            )
            simulated_positions[symbol] = new_pos
        else:
            new_position, _realized_delta = pos.update(qty, price)
            if new_position is None:
                # closed
                del simulated_positions[symbol]
            else:
                simulated_positions[symbol] = new_position

        # --- compute equity after the simulated trade ---
        equity_after = cash_after
        for s, p in simulated_positions.items():
            p_price = price_by_symbol.get(s, p.entry_price)
            if p.side == PositionSide.LONG:
                equity_after += p_price * p.quantity
            else:
                equity_after += -p_price * abs(p.quantity)

        # --- check maintenance margin per short position in the simulated state ---
        for s, p in simulated_positions.items():
            if p.side == PositionSide.SHORT:
                p_price = price_by_symbol.get(s, p.entry_price)
                notional = p_price * abs(p.quantity)
                required_maint = notional * maintenance_margin
                if equity_after < required_maint:
                    return False, (
                        f"Would breach maintenance margin for {s}: "
                    )

        # All good: commit the simulated state to real state
        self.cash = cash_after
        # replace positions with simulated positions (they are fresh objects)
        self.positions = simulated_positions

        return True, None

    def build_snapshot(self, price_by_symbol: dict, timestamp: str) -> PortfolioSnapshot:
        """
        Builds a snapshot of the portfolio at a specific point in time.
        """
        equity = self.cash
        positions_snapshot: list[Position] = []

        for symbol, position in self.positions.items():
            current_price = price_by_symbol.get(symbol)
            
            # Market value
            if position.side == PositionSide.LONG:
                market_value = current_price * position.quantity
            elif position.side == PositionSide.SHORT:
                market_value = -current_price * abs(position.quantity)

            equity += market_value

            positions_snapshot.append(
                Position(
                    symbol=position.symbol,
                    side=position.side,
                    quantity=position.quantity,
                    entry_price=position.entry_price,
                    realized_pnl=position.realized_pnl,
                )
            )

        return PortfolioSnapshot(
            timestamp=timestamp,
            cash=self.cash,
            equity=equity,
            positions=positions_snapshot,
        )
