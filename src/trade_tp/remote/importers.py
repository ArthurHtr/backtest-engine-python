from typing import Dict, List
from trade_tp.backtest_engine.models.candle import Candle
from trade_tp.backtest_engine.models.symbol import Symbol
from trade_tp.remote.client import TradeTpClient

class RemoteDataProvider:
    """Récupère les données via l'API distante."""

    def __init__(self, client: TradeTpClient):
        self.client = client

    def get_symbols(self, symbols: List[str]) -> List[Symbol]:
        raw = self.client.get_symbols(symbols)
        result = []
        for entry in raw:
            try:
                result.append(
                    Symbol(
                        symbol=entry["symbol"],
                        base_asset=entry.get("base_asset", entry["symbol"]),
                        quote_asset=entry.get("quote_asset", "USD"),
                        price_step=entry.get("price_step", 0.01),
                        quantity_step=entry.get("quantity_step", 1),
                    )
                )
            except KeyError:
                continue
        return result

    def get_multiple_candles(self, symbols: List[str], start: str, end: str, timeframe: str = "1d") -> Dict[str, List[Candle]]:
        raw = self.client.get_candles(symbols=symbols, start=start, end=end, timeframe=timeframe)
        candles_by_symbol = {}
        for symbol, candle_dicts in raw.items():
            candles = []
            for c in candle_dicts:
                try:
                    candles.append(
                        Candle(
                            symbol=symbol,
                            timestamp=c["timestamp"],
                            open=c["open"],
                            high=c["high"],
                            low=c["low"],
                            close=c["close"],
                            volume=c.get("volume", 0),
                        )
                    )
                except KeyError:
                    continue
            candles_by_symbol[symbol] = candles
        return candles_by_symbol