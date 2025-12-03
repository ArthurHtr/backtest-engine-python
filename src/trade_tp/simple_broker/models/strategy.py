from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from src.trade_tp.simple_broker.models.candle import Candle
from src.trade_tp.simple_broker.models.portfolio_snapshot import PortfolioSnapshot


class StrategyContext:
    """
    Provides context to the strategy during backtesting.

    Attributes
    - candles: mapping symbol -> Candle for the current timestamp
    - portfolio_snapshot: PortfolioSnapshot before applying intents
    - past_candles: mapping symbol -> list[Candle] containing historical candles up to and including current bar

    Helpers are provided to simplify common indicator computations (get_history, get_series, sma, ema).
    """

    def __init__(self, candles: Dict[str, Candle], portfolio_snapshot: PortfolioSnapshot, past_candles: Optional[Dict[str, List[Candle]]] = None):
        self.candles: Dict[str, Candle] = candles
        self.portfolio_snapshot: PortfolioSnapshot = portfolio_snapshot
        self.past_candles: Dict[str, List[Candle]] = past_candles

        # small cache for per-context computed indicators
        self._cache = {}

    def current_timestamp(self) -> Optional[str]:
        """Return the timestamp of the current candles (assumes all current candles share the same ts)."""
        return next(iter(self.candles.values())).timestamp

    def get_history(self, symbol: str, limit: Optional[int] = None) -> List[Candle]:
        """Return historical candles for symbol up to the current bar.
        If limit is provided, returns at most the last `limit` candles.
        """
        hist = self.past_candles.get(symbol, [])
        return hist[-limit:] if limit is not None else list(hist)

    def get_series(self, symbol: str, field: str, limit: Optional[int] = None) -> List[float]:
        """Return a list of numeric values for a candle field."""
        series = [getattr(c, field) for c in self.get_history(symbol, limit)]
        return series


class BaseStrategy(ABC):
    """
    Abstract base class for all strategies.
    """

    @abstractmethod
    def on_bar(self, context: StrategyContext):
        """Called on each new bar (candle) for multiple symbols."""
        pass
