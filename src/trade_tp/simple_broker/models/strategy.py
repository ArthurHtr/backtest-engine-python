from abc import ABC, abstractmethod

from src.trade_tp.simple_broker.models.candle import Candle
from src.trade_tp.simple_broker.models.portfolio_snapshot import PortfolioSnapshot

class StrategyContext:
    """
    Provides context to the strategy during backtesting.
    """
    def __init__(self, candles: dict[str, Candle], portfolio_snapshot: PortfolioSnapshot, past_candles: dict[str, list[Candle]]):
        self.candles = candles
        self.portfolio_snapshot = portfolio_snapshot
        self.past_candles = past_candles

class BaseStrategy(ABC):
    """
    Abstract base class for all strategies.
    """
    @abstractmethod
    def on_bar(self, context: StrategyContext):
        """
        Called on each new bar (candle) for multiple symbols.
        """
        pass
