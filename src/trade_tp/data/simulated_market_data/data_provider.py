import random
import math
from datetime import datetime, timedelta
from typing import List, Dict

from trade_tp.backtest_engine.models.candle import Candle
from trade_tp.backtest_engine.models.symbol import Symbol


class DataProvider:
    """
    Générateur de données de marché simulées utilisant un Mouvement Brownien Géométrique (GBM).
    Produit des bougies OHLCV cohérentes avec des propriétés statistiques réalistes.
    """

    def __init__(
        self,
        seed: int = 42,
        base_price: float = 100.0,
        annual_drift: float = 0.05,  # 5% de rendement annuel moyen
        annual_volatility: float = 0.2,  # 20% de volatilité annuelle
        base_daily_volume: int = 1_000_000,
    ):
        self.base_price = base_price
        self.mu = annual_drift
        self.sigma = annual_volatility
        self.base_daily_volume = base_daily_volume
        
        if seed is not None:
            random.seed(seed)

    def _delta_from_timeframe(self, timeframe: str) -> timedelta:
        mapping = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1),
            "1w": timedelta(weeks=1),
        }
        if timeframe not in mapping:
            # Fallback simple parsing
            if timeframe.endswith('m'):
                try:
                    return timedelta(minutes=int(timeframe[:-1]))
                except ValueError:
                    pass
            if timeframe.endswith('h'):
                try:
                    return timedelta(hours=int(timeframe[:-1]))
                except ValueError:
                    pass
            if timeframe.endswith('d'):
                try:
                    return timedelta(days=int(timeframe[:-1]))
                except ValueError:
                    pass
            raise ValueError(f"Unsupported timeframe '{timeframe}'")
        return mapping[timeframe]

    def get_candles(self, symbol: str, start: str, end: str, timeframe: str = "1d") -> List[Candle]:
        """
        Génère une série de bougies OHLCV pour un symbole donné.
        Utilise un modèle GBM pour le prix de clôture et dérive High/Low de la volatilité.
        """
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        
        if start_dt >= end_dt:
            raise ValueError("start must be before end")

        delta = self._delta_from_timeframe(timeframe)
        dt_years = delta.total_seconds() / (365.25 * 24 * 3600) # Delta t en années
        
        candles: List[Candle] = []
        current_price = self.base_price
        current_dt = start_dt

        # Paramètres pour GBM
        # S_t = S_{t-1} * exp((mu - 0.5 * sigma^2) * dt + sigma * sqrt(dt) * Z)
        drift_term = (self.mu - 0.5 * self.sigma**2) * dt_years
        vol_term = self.sigma * math.sqrt(dt_years)

        while current_dt <= end_dt:
            # 1. Calcul du Close via GBM
            shock = random.gauss(0, 1)
            log_return = drift_term + vol_term * shock
            close_price = current_price * math.exp(log_return)
            
            # 2. Génération OHLC cohérent
            # Open est le close précédent (ou très proche)
            open_price = current_price
            
            # Pour High et Low, on simule une excursion
            # On utilise une approximation : High et Low sont des déviations de Open et Close
            # La volatilité intra-bougie est liée à sigma * sqrt(dt)
            
            # Estimation de l'amplitude de la bougie (High - Low) basée sur la volatilité
            # On utilise une distribution de Weibull pour simuler des queues épaisses (mouvements brusques)
            expected_range = open_price * self.sigma * math.sqrt(dt_years) * random.weibullvariate(1, 1.5)
            
            # On s'assure que High >= max(Open, Close) et Low <= min(Open, Close)
            mn = min(open_price, close_price)
            mx = max(open_price, close_price)
            
            # On répartit l'excédent de range (s'il y en a) autour du corps
            body_size = mx - mn
            remaining_range = max(0.0, expected_range - body_size)
            
            # Répartition aléatoire du remaining range entre haut et bas
            ratio = random.random()
            high_price = mx + remaining_range * ratio
            low_price = mn - remaining_range * (1 - ratio)
            
            # Safety checks (prix > 0)
            low_price = max(0.01, low_price)
            high_price = max(high_price, low_price + 0.01)
            close_price = max(0.01, close_price)
            open_price = max(0.01, open_price)

            # 3. Volume
            # Le volume est souvent corrélé à la volatilité (valeur absolue du rendement)
            # Plus ça bouge, plus il y a de volume
            vol_shock = random.lognormvariate(0, 0.5)
            base_vol = self.base_daily_volume * (delta.total_seconds() / 86400)
            
            # Facteur d'amplification du volume basé sur le mouvement de prix
            price_move_factor = 1 + 10 * abs(log_return) / (self.sigma * math.sqrt(dt_years))
            volume = int(base_vol * price_move_factor * vol_shock)

            candles.append(Candle(
                symbol=symbol,
                timestamp=current_dt.isoformat(),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume
            ))

            current_price = close_price
            current_dt += delta

        return candles

    def get_multiple_candles(self, symbols: List[str], start: str, end: str, timeframe: str = "1d") -> Dict[str, List[Candle]]:
        return {s: self.get_candles(s, start, end, timeframe=timeframe) for s in symbols}

    def get_symbols(self, symbols: List[str]) -> List[Symbol]:
        return [Symbol(symbol=s, base_asset=s, quote_asset="USD", price_step=0.01, quantity_step=1) for s in symbols]

    