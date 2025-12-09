import random
from datetime import datetime, timedelta
from math import sqrt
from typing import Dict, List

from src.trade_tp.backtest_engine.models.candle import Candle
from src.trade_tp.backtest_engine.models.symbol import Symbol


class DataProvider:
    """Générateur de données de marché simulées.

    - Prix démarrent à 100 pour chaque symbole.
    - Pas fixe contrôlé par `timeframe` ("1m", "1h", "1d").
    - Volumes simulés avec une distribution log-normale simple, ajustée au pas.
    """

    def __init__(
        self,
        seed: int | None = None,
        base_price: float = 100.0,
        drift: float = 0.1,
        volatility: float = 0.02,
        base_daily_volume: int = 1_000_000,
    ):
        self.base_price = base_price
        self.drift = drift
        self.volatility = volatility
        self.base_daily_volume = base_daily_volume

        if seed is not None:
            random.seed(seed)

    def _delta_from_timeframe(self, timeframe: str) -> timedelta:
        mapping = {
            "1m": timedelta(minutes=1),
            "1h": timedelta(hours=1),
            "1d": timedelta(days=1),
        }
        if timeframe not in mapping:
            raise ValueError(f"Unsupported timeframe '{timeframe}', use one of: {', '.join(mapping)}")
        return mapping[timeframe]

    def _volume_for_step(self, timeframe: str) -> int:
        if timeframe == "1m":
            return max(1, int(self.base_daily_volume / (24 * 60)))
        if timeframe == "1h":
            return max(1, int(self.base_daily_volume / 24))
        return self.base_daily_volume

    def get_candles(self, symbol: str, start: str, end: str, timeframe: str = "1d") -> List[Candle]:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        if start_dt >= end_dt:
            raise ValueError("start must be before end")

        step = self._delta_from_timeframe(timeframe)
        vol_per_step = self._volume_for_step(timeframe)

        price = self.base_price
        candles: List[Candle] = []

        current = start_dt
        while current <= end_dt:
            # Variation simple : drift + bruit normal proportionnel à la volatilité
            epsilon = random.gauss(0.0, 1.0)
            price_change = price * (self.drift * (step.total_seconds() / 86_400) + self.volatility * sqrt(step.total_seconds() / 86_400) * epsilon)
            new_price = max(0.01, price + price_change)

            high = max(price, new_price) * (1 + random.uniform(0.0005, 0.002))
            low = min(price, new_price) * (1 - random.uniform(0.0005, 0.002))
            volume = max(1, int(random.lognormvariate(0, 0.4) * vol_per_step))

            candles.append(
                Candle(
                    symbol=symbol,
                    timestamp=current.isoformat(),
                    open=price,
                    high=high,
                    low=low,
                    close=new_price,
                    volume=volume,
                )
            )

            price = new_price
            current += step

        return candles

    def get_multiple_candles(self, symbols: List[str], start: str, end: str, timeframe: str = "1d") -> Dict[str, List[Candle]]:
        return {s: self.get_candles(s, start, end, timeframe=timeframe) for s in symbols}

    def get_symbols(self, symbols: List[str]) -> List[Symbol]:
        return [Symbol(symbol=s, base_asset=s, quote_asset="USD", price_step=0.01, quantity_step=1) for s in symbols]

    def plot_prices(self, symbol: str, start: str, end: str, timeframe: str = "1d", show: bool = True):
        """Génère les candles puis trace la courbe des close.

        Retourne (fig, ax). Nécessite matplotlib installé.
        """
        import matplotlib.pyplot as plt  # import local pour éviter dépendance obligatoire

        candles = self.get_candles(symbol, start, end, timeframe=timeframe)
        closes = [c.close for c in candles]
        timestamps = [c.timestamp for c in candles]

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(timestamps, closes, label=f"{symbol} close")
        ax.set_title(f"Simulated prices for {symbol} ({timeframe})")
        ax.set_xlabel("Time")
        ax.set_ylabel("Price")
        ax.legend()
        fig.autofmt_xdate()

        if show:
            plt.show()

        return fig, ax
