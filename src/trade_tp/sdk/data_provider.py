import random
from src.trade_tp.simple_broker.models.candle import Candle
from src.trade_tp.simple_broker.models.symbol import Symbol  
from datetime import datetime, timedelta

class DataProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Initialize API connection here

    def get_candles(self, symbol: str, start: str, end: str):
        """
        Fetch candle data for a given symbol and time range.
        Simulates data for demonstration purposes.
        :param symbol: The market symbol (e.g., 'BTC/USD').
        :param start: Start datetime as a string.
        :param end: End datetime as a string.
        :return: List of candles.
        """
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            
            if start_date >= end_date:
                raise ValueError("Start date must be before end date.")

            candles = []
            current_date = start_date
            base_price = 80

            while current_date <= end_date:
                # Simulate subtle upward market trend with moderate volatility
                base_price += random.uniform(-0.3, 0.5)  # Small random drift

                open_price = base_price + random.uniform(-1, 1)
                close_price = open_price + random.uniform(-1, 1)
                high_price = max(open_price, close_price) + random.uniform(0, 1)
                low_price = min(open_price, close_price) - random.uniform(0, 1)

                # Ensure prices are non-negative
                open_price = max(0, open_price)
                high_price = max(0, high_price)
                low_price = max(0, low_price)
                close_price = max(0, close_price)

                # Simplify volume generation
                volume = random.randint(1000, 5000)  # Random volume within a realistic range

                candles.append(Candle(
                    symbol=symbol,
                    timestamp=current_date.isoformat(),
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume
                ))

                current_date += timedelta(minutes=1)

            return candles
        except Exception as e:
            print(f"Error fetching candles: {e}")
            return []

    def get_multiple_candles(self, symbols: list[str], start: str, end: str):
        """
        Fetch candle data for multiple symbols and a given time range.
        Simulates data for demonstration purposes.
        :param symbols: List of market symbols (e.g., ['BTC/USD', 'ETH/USD']).
        :param start: Start datetime as a string.
        :param end: End datetime as a string.
        :return: Dictionary of symbol -> List of candles.
        """
        candles_by_symbol = {}
        for symbol in symbols:
            candles_by_symbol[symbol] = self.get_candles(symbol, start, end)
        return candles_by_symbol

    def get_symbols(self, symbols: list[str]) -> list[Symbol]:
        """
        Fetch a list of Symbol objects based on the provided symbol names.
        :param symbols: List of symbol names to fetch.
        :return: List of Symbol objects matching the provided names.
        """
        try:
            simulated_symbols = [
                Symbol(symbol="AAPL", base_asset="AAPL", quote_asset="USD", price_step=0.01, quantity_step=1),
                Symbol(symbol="GOOGL", base_asset="GOOGL", quote_asset="USD", price_step=0.01, quantity_step=1),
                Symbol(symbol="TSLA", base_asset="TSLA", quote_asset="USD", price_step=0.01, quantity_step=1),
                Symbol(symbol="MSFT", base_asset="MSFT", quote_asset="USD", price_step=0.01, quantity_step=1),
                Symbol(symbol="AMZN", base_asset="AMZN", quote_asset="USD", price_step=0.01, quantity_step=1),
                Symbol(symbol="NFLX", base_asset="NFLX", quote_asset="USD", price_step=0.01, quantity_step=1),
            ]
            return [s for s in simulated_symbols if s.symbol in symbols]
        except Exception as e:
            print(f"Error fetching symbols: {e}")
            return []
