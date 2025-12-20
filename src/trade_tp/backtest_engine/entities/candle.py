from dataclasses import dataclass

@dataclass(frozen=True)
class Candle:
    """
    Représente une bougie OHLCV (Open / High / Low / Close / Volume) pour un symbole.
    Immuable.

    Attributes
    - symbol (str): symbole tradé, ex. 'AAPL'
    - timestamp (str): horodatage associé à la bougie (ISO-8601 ou chaîne arbitraire)
    - open, high, low, close (float): prix d'ouverture, haut, bas, clôture
    - volume (float): volume échangé pendant la période
    """
    symbol: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float