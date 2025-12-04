class Candle:
        """
        Représente une bougie OHLCV (Open / High / Low / Close / Volume) pour un symbole

        Attributes
        - symbol (str): symbole tradé, ex. 'AAPL'
        - timestamp (str): horodatage associé à la bougie (ISO-8601 ou chaîne arbitraire)
        - open, high, low, close (float): prix d'ouverture, haut, bas, clôture
        - volume (float): volume échangé pendant la période

        Usage
        - Utilisé par le moteur de backtest pour représenter les données de marché
            par bar et pour calculer les valeurs de marché / indicateurs.
        """

        def __init__(self, symbol: str, timestamp: str, open: float, high: float, low: float, close: float, volume: float):
                self.symbol = symbol
                self.timestamp = timestamp
                self.open = open
                self.high = high
                self.low = low
                self.close = close
                self.volume = volume