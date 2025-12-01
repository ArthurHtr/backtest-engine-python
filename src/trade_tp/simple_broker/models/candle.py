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