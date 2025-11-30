from enum import Enum
import uuid

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class Symbol:
    """
    Represents a trading symbol.
    """
    def __init__(self, symbol: str, base_asset: str, quote_asset: str, price_step: float, quantity_step: float):
        self.symbol = symbol
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.price_step = price_step
        self.quantity_step = quantity_step

class Candle:
    """
    Represents a single OHLCV (Open, High, Low, Close, Volume) bar.
    """
    def __init__(self, symbol: str, timestamp: str, open: float, high: float, low: float, close: float, volume: float):
        self.symbol = symbol
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

class OrderIntent:
    """
    Represents an order intent from the strategy.
    """
    def __init__(self, symbol: str, side: Side, quantity: float, order_type: str = "MARKET", limit_price: float = None):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.limit_price = limit_price
        self.order_id = str(uuid.uuid4())  # Assign a unique order ID

class Trade:
    """
    Represents an executed trade.
    """
    def __init__(self, symbol: str, quantity: float, price: float, fee: float, timestamp: str):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.fee = fee
        self.timestamp = timestamp
        self.trade_id = str(uuid.uuid4())  # Assign a unique trade ID

class Position:
    """
    Represents an open position, supporting both long and short sides.
    """
    def __init__(self, symbol: str, side: PositionSide, quantity: float, entry_price: float, realized_pnl: float = 0.0):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.entry_price = abs(entry_price)  # Ensure entry_price is always positive
        self.realized_pnl = realized_pnl

    def update(self, trade_price: float, trade_quantity: float):
        """
        Updates the position based on a trade.
        """
        if self.side == PositionSide.LONG:
            if trade_quantity > 0:  # Adding to the position
                total_quantity = self.quantity + trade_quantity
                self.entry_price = (
                    (self.quantity * self.entry_price + trade_quantity * trade_price) / total_quantity
                )
                self.quantity = total_quantity
            else:  # Reducing the position
                realized = (trade_price - self.entry_price) * abs(trade_quantity)
                self.realized_pnl += realized
                self.quantity += trade_quantity

        elif self.side == PositionSide.SHORT:
            if trade_quantity < 0:  # Adding to the position
                total_quantity = self.quantity + trade_quantity
                self.entry_price = abs(
                    (self.quantity * self.entry_price + abs(trade_quantity) * trade_price) / total_quantity
                )
                self.quantity = total_quantity
            else:  # Reducing the position
                realized = (self.entry_price - trade_price) * abs(trade_quantity)
                self.realized_pnl += realized
                self.quantity += trade_quantity

    def __repr__(self):
        return (
            f"Position(Symbol: {self.symbol}, Side: {self.side}, Quantity: {self.quantity}, "
            f"Entry Price: {self.entry_price}, Realized PnL: {self.realized_pnl})"
        )

class PortfolioSnapshot:
    """
    Represents a snapshot of the portfolio at a specific point in time.
    """
    def __init__(self, timestamp: str, cash: float, equity: float, positions: list):
        self.timestamp = timestamp
        self.cash = cash
        self.equity = equity
        self.positions = positions

    def __repr__(self):
        positions_str = ", ".join([f"{p.symbol}: {p.quantity} @ {p.entry_price}" for p in self.positions])
        return (
            f"PortfolioSnapshot(Timestamp: {self.timestamp}, "
            f"Cash: {self.cash:.2f}, Equity: {self.equity:.2f}, "
            f"Positions: [{positions_str}])"
        )

class PortfolioState:
    """
    Represents the portfolio state, including cash and positions for multiple symbols.
    """
    def __init__(self, initial_cash: float):
        self.cash = initial_cash
        self.positions = {}  # Dictionary of symbol -> Position

    def apply_trade(self, trade: Trade):
        """
        Applies a trade to the portfolio, updating cash and positions.
        """
        if trade.symbol not in self.positions:
            side = PositionSide.LONG if trade.quantity > 0 else PositionSide.SHORT
            self.positions[trade.symbol] = Position(
                symbol=trade.symbol,
                side=side,
                quantity=0,
                entry_price=trade.price
            )

        position = self.positions[trade.symbol]
        position.update(trade_price=trade.price, trade_quantity=trade.quantity)

        # Update cash
        self.cash -= trade.quantity * trade.price + trade.fee

        # Remove position if quantity is zero
        if position.quantity == 0:
            del self.positions[trade.symbol]

    def build_snapshot(self, price_by_symbol: dict[str, float], timestamp: str):
        """
        Builds a snapshot of the portfolio, including unrealized PnL for all positions.
        """
        equity = self.cash
        positions = []

        for symbol, position in self.positions.items():
            current_price = price_by_symbol.get(symbol, position.entry_price)
            unrealized_pnl = (
                (current_price - position.entry_price) * position.quantity
                if position.side == PositionSide.LONG
                else (position.entry_price - current_price) * abs(position.quantity)
            )
            equity += unrealized_pnl
            positions.append(position)

        return PortfolioSnapshot(timestamp=timestamp, cash=self.cash, equity=equity, positions=positions)