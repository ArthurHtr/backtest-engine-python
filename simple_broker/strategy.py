from abc import ABC, abstractmethod

from simple_broker.models.candle import Candle
from simple_broker.models.portfolio_snapshot import PortfolioSnapshot

class StrategyContext:
    """
    Provides context to the strategy during backtesting for multiple symbols.
    """
    def __init__(self, candles: dict[str, Candle], portfolio_snapshot: PortfolioSnapshot):
        self.candles = candles
        self.portfolio_snapshot = portfolio_snapshot

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
