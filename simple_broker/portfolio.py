from simple_broker.models.trade import Trade
from simple_broker.models.enums import PositionSide
from simple_broker.models.positions import Position
from simple_broker.models.portfolio_snapshot import PortfolioSnapshot

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

    def apply_trade(self, trade: Trade) -> None:
        """
        Met à jour le portefeuille à partir d'un trade exécuté.
        """        
        symbol = trade.symbol
        qty = float(trade.quantity)
        price = float(trade.price)
        fee = float(trade.fee)

        position = self.positions.get(symbol)

        if position is None:
            # Ouverture de position pure
            side = PositionSide.LONG if qty > 0 else PositionSide.SHORT
            position = Position(
                symbol=symbol,
                side=side,
                quantity=abs(qty),
                entry_price=price,
            )
            self.positions[symbol] = position

        else:
            # Mise à jour via la logique encapsulée dans Position
            new_position, realized_pnl_delta = position.update(qty, price)

            if new_position is None:
                # Position complètement fermée
                del self.positions[symbol]
            else:
                self.positions[symbol] = new_position

        self.cash -= qty * price + fee

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

            # pour le calcul d'equity (le realized est déjà dans self.cash).
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
