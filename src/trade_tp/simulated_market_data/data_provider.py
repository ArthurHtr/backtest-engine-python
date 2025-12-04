import math
import random
from datetime import datetime, timedelta

from src.trade_tp.simple_broker.models.candle import Candle
from src.trade_tp.simple_broker.models.symbol import Symbol  


class DataProvider:
    def __init__(self, api_key: str, seed: int | None = None):
        self.api_key = api_key

        # Option : seed pour rendre la simulation reproductible
        if seed is not None:
            random.seed(seed)

        # Paramètres "raisonnables" par symbole, très simples
        self.symbol_params = {
            "AAPL":  {"start_price": 190.0, "annual_mu": 0.10, "annual_sigma": 0.25},
            "GOOGL": {"start_price": 140.0, "annual_mu": 0.09, "annual_sigma": 0.23},
            "TSLA":  {"start_price": 230.0, "annual_mu": 0.15, "annual_sigma": 0.45},
            "MSFT":  {"start_price": 430.0, "annual_mu": 0.09, "annual_sigma": 0.22},
            "AMZN":  {"start_price": 180.0, "annual_mu": 0.11, "annual_sigma": 0.30},
            "NFLX":  {"start_price": 600.0, "annual_mu": 0.12, "annual_sigma": 0.35},
        }

        # Volume moyen quotidien ultra simple
        self.daily_volume = {
            "AAPL": 8_000_000,
            "GOOGL": 1_500_000,
            "TSLA": 4_000_000,
            "MSFT": 6_000_000,
            "AMZN": 5_000_000,
            "NFLX": 800_000,
        }

    def get_candles(self, symbol: str, start: str, end: str) -> list[Candle]:
        """
        Fetch candle data for a given symbol and time range.
        Simule des données avec un process simple mais réaliste.
        :param symbol: The market symbol (e.g., 'AAPL').
        :param start: Start datetime as a string, format '%Y-%m-%d'.
        :param end: End datetime as a string, format '%Y-%m-%d'.
        :return: List of Candle objects.
        """
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")

            if start_date >= end_date:
                raise ValueError("Start date must be before end date.")

            # Paramètres du symbole (fallback très basique si inconnu)
            params = self.symbol_params.get(
                symbol,
                {"start_price": 100.0, "annual_mu": 0.08, "annual_sigma": 0.30},
            )
            price = params["start_price"]
            mu = params["annual_mu"]
            sigma = params["annual_sigma"]

            # On travaille en pas de 1 minute, tout le temps (pas d'horaires de marché)
            minutes_per_year = 365 * 24 * 60
            dt = 1.0 / minutes_per_year
            sqrt_dt = math.sqrt(dt)

            # Volume moyen par minute (répartition uniforme sur la journée)
            base_daily_vol = self.daily_volume.get(symbol, 1_000_000)
            avg_minute_vol = base_daily_vol / (24 * 60)

            candles: list[Candle] = []
            current_date = start_date
            last_close = price

            while current_date <= end_date:
                # On parcourt la journée minute par minute
                for _ in range(24 * 60):
                    # Retour log-normal (mouvement brownien géométrique)
                    epsilon = random.gauss(0.0, 1.0)
                    log_return = (mu - 0.5 * sigma * sigma) * dt + sigma * sqrt_dt * epsilon
                    new_price = last_close * math.exp(log_return)

                    # Construire un OHLC simple autour de last_close -> new_price
                    open_price = last_close
                    close_price = new_price

                    # Petite "range" locale
                    base_range = new_price * random.uniform(0.0005, 0.003)  # 0.05%–0.3%
                    low_price = max(0.01, min(open_price, close_price) - base_range)
                    high_price = max(low_price + 0.001, max(open_price, close_price) + base_range)

                    # Volume : log-normal autour de avg_minute_vol
                    vol = random.lognormvariate(
                        math.log(avg_minute_vol + 1e-6) - 0.5 * 0.4 * 0.4,
                        0.4,
                    )
                    volume = int(max(1.0, vol))

                    candles.append(
                        Candle(
                            symbol=symbol,
                            timestamp=current_date.isoformat(),
                            open=open_price,
                            high=high_price,
                            low=low_price,
                            close=close_price,
                            volume=volume,
                        )
                    )

                    last_close = close_price
                    current_date += timedelta(minutes=1)

                    if current_date > end_date:
                        break

            return candles

        except Exception as e:
            print(f"Error fetching candles for {symbol}: {e}")
            return []

    def get_multiple_candles(self, symbols: list[str], start: str, end: str) -> dict[str, list[Candle]]:
        """
        Fetch candle data for multiple symbols and a given time range.
        Interface inchangée.
        """
        candles_by_symbol: dict[str, list[Candle]] = {}
        for symbol in symbols:
            candles_by_symbol[symbol] = self.get_candles(symbol, start, end)
        return candles_by_symbol

    def get_symbols(self, symbols: list[str]) -> list[Symbol]:
        """
        Fetch a list of Symbol objects based on the provided symbol names.
        Même idée que ton code initial.
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
