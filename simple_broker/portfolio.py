from simple_broker.models import Trade, PortfolioSnapshot, Position, PositionSide

class PortfolioState:
    """
    Manages the internal state of the portfolio, supporting long and short positions.
    """
    def __init__(self, initial_cash: float):
        self.cash = initial_cash
        self.positions = {}

    def apply_trade(self, trade: Trade):
        """
        Updates the portfolio state based on a trade.
        """
        if trade.symbol not in self.positions:
            side = PositionSide.LONG if trade.quantity > 0 else PositionSide.SHORT
            self.positions[trade.symbol] = Position(
                symbol=trade.symbol,
                side=side,
                quantity=0,
                entry_price=0.0
            )

        position = self.positions[trade.symbol]
        position.update(trade_price=trade.price, trade_quantity=trade.quantity)

        # Remove position if fully closed
        if position.quantity == 0:
            del self.positions[trade.symbol]

        # Update cash
        self.cash -= trade.quantity * trade.price + trade.fee

    def build_snapshot(self, price_by_symbol: dict, timestamp: str) -> PortfolioSnapshot:
        """
        Builds a snapshot of the portfolio at a specific point in time.
        """
        equity = self.cash
        positions_snapshot = []

        for symbol, position in self.positions.items():
            current_price = price_by_symbol.get(symbol)
            if current_price is None:
                continue  # Skip positions without a current price

            unrealized_pnl = (
                (current_price - position.entry_price) * position.quantity
                if position.side == PositionSide.LONG
                else (position.entry_price - current_price) * abs(position.quantity)
            )
            equity += unrealized_pnl
            positions_snapshot.append(Position(
                symbol=position.symbol,
                side=position.side,
                quantity=position.quantity,
                entry_price=position.entry_price,
                realized_pnl=position.realized_pnl
            ))

        return PortfolioSnapshot(timestamp=timestamp, cash=self.cash, equity=equity, positions=positions_snapshot)