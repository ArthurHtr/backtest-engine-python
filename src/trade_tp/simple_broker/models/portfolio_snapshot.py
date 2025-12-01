from src.trade_tp.simple_broker.models.positions import Position

class PortfolioSnapshot:
    """
    Represents a snapshot of the portfolio at a specific point in time.
    """
    def __init__(self, timestamp: str, cash: float, equity: float, positions: list[Position]):
        self.timestamp = timestamp
        self.cash = cash
        self.equity = equity
        self.positions = positions

    def summarize_positions(self):
        """
        Returns a summary of positions as a dictionary.
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

    def __repr__(self):
        positions_str = ", ".join([f"{p.symbol}: {p.quantity} @ {p.entry_price}" for p in self.positions])
        return (
            f"PortfolioSnapshot(Timestamp: {self.timestamp}, "
            f"Cash: {self.cash:.2f}, Equity: {self.equity:.2f}, "
            f"Positions: [{positions_str}])"
        )
