from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from trade_tp.backtest_engine.models.candle import Candle
from trade_tp.backtest_engine.models.portfolio_snapshot import PortfolioSnapshot
from trade_tp.backtest_engine.models.positions import Position
from trade_tp.backtest_engine.models.enums import PositionSide


class StrategyContext:
    """
    Provides context to the strategy during backtesting.

    Attributes
    - candles: mapping symbol -> Candle for the current timestamp
    - portfolio_snapshot: PortfolioSnapshot before applying intents
    - past_candles: mapping symbol -> list[Candle] containing historical candles up to and including current bar

    Helpers are provided to simplify common indicator computations (get_history, get_series).
    """

    def __init__(self, candles: Dict[str, Candle], portfolio_snapshot: PortfolioSnapshot, past_candles: Optional[Dict[str, List[Candle]]] = None):
        self.candle: Dict[str, Candle] = candles
        self.portfolio_snapshot: PortfolioSnapshot = portfolio_snapshot
        self.past_candles: Dict[str, List[Candle]] = past_candles

        # small cache for per-context computed indicators for exemple
        self._cache = {}

    def current_timestamp(self) -> Optional[str]:
        """Return the timestamp of the current candles (assumes all current candles share the same ts)."""
        return next(iter(self.candle.values())).timestamp

    def _get_history(self, symbol: str, limit: Optional[int] = None) -> List[Candle]:
        """Return historical candles for symbol up to the current bar.
        If limit is provided, returns at most the last `limit` candles.
        """
        hist = self.past_candles.get(symbol, [])
        return hist[-limit:] if limit is not None else list(hist)

    def get_series(self, symbol: str, field: str, limit: Optional[int] = None) -> List[float]:
        """Return a list of numeric values for a candle field."""
        series = [getattr(c, field) for c in self._get_history(symbol, limit)]
        return series

    @property
    def cash(self) -> float:
        """Shortcut to access available cash."""
        return self.portfolio_snapshot.cash

    @property
    def equity(self) -> float:
        """Shortcut to access portfolio equity."""
        return self.portfolio_snapshot.equity

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Return the current position for a symbol, or None if no position exists.
        """
        for p in self.portfolio_snapshot.positions:
            if p.symbol == symbol:
                return p
        return None

    def is_long(self, symbol: str) -> bool:
        """Return True if there is a LONG position on the symbol."""
        pos = self.get_position(symbol)
        return pos is not None and pos.side == PositionSide.LONG

    def is_short(self, symbol: str) -> bool:
        """Return True if there is a SHORT position on the symbol."""
        pos = self.get_position(symbol)
        return pos is not None and pos.side == PositionSide.SHORT

    def get_entry_price(self, symbol: str) -> Optional[float]:
        """Return the entry price of the position on the symbol, or None."""
        pos = self.get_position(symbol)
        return pos.entry_price if pos else None

    def get_quantity(self, symbol: str) -> float:
        """Return the quantity of the position on the symbol, or 0.0."""
        pos = self.get_position(symbol)
        return pos.quantity if pos else 0.0


class BaseStrategy(ABC):
    """
    Abstract base class for all strategies.
    """

    @abstractmethod
    def on_bar(self, context: StrategyContext):
        """Called on each new bar (candle) for multiple symbols."""
        pass
