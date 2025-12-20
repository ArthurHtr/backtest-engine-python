from abc import ABC, abstractmethod
from .context import StrategyContext

class BaseStrategy(ABC):
    """
    Abstract base class for all strategies.
    """

    @abstractmethod
    def on_bar(self, context: StrategyContext):
        """Called on each new bar (candle) for multiple symbols."""
        pass
