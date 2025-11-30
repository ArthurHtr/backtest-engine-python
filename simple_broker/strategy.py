from abc import ABC, abstractmethod
from simple_broker.models import Candle, PortfolioSnapshot, OrderIntent, Side

class StrategyContext:
    """
    Provides context to the strategy during backtesting.
    """
    def __init__(self, candle: Candle, symbol: str, portfolio_snapshot: PortfolioSnapshot):
        self.candle = candle
        self.symbol = symbol
        self.portfolio_snapshot = portfolio_snapshot

class MultiSymbolStrategyContext:
    """
    Provides context to the strategy during backtesting for multiple symbols.
    """
    def __init__(self, candles: dict[str, Candle], portfolio_snapshot: PortfolioSnapshot):
        self.candles = candles  # Dictionary of symbol -> Candle
        self.portfolio_snapshot = portfolio_snapshot

class BaseStrategy(ABC):
    """
    Abstract base class for all strategies.
    """
    @abstractmethod
    def on_bar(self, context: MultiSymbolStrategyContext):
        """
        Called on each new bar (candle) for multiple symbols.
        """
        pass
