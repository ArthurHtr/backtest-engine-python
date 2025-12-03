"""
Moving Average Crossover strategy example.

Cette stratégie calcule une SMA courte et une SMA longue sur les prix de clôture
et place un ordre BUY lorsque la SMA courte croise au-dessus de la SMA longue,
et un ordre SELL lorsque la SMA courte croise en dessous.

Elle illustre l'utilisation des helpers exposés par `StrategyContext` (get_series, sma...).
"""
from typing import List

from src.trade_tp.simple_broker.models.strategy import BaseStrategy, StrategyContext
from src.trade_tp.simple_broker.models.order_intent import OrderIntent
from src.trade_tp.simple_broker.models.enums import Side


class MovingAverageCrossoverStrategy(BaseStrategy):
    """SMA crossover strategy.

    Params
    ------
    short_window: int
        période courte pour la SMA
    long_window: int
        période longue pour la SMA (doit être > short_window)
    quantity: float
        quantité fixe à envoyer sur chaque signal
    """

    def __init__(self, short_window: int = 5, long_window: int = 20, quantity: float = 100.0):
        if short_window >= long_window:
            raise ValueError("short_window must be < long_window")
        self.short_window = short_window
        self.long_window = long_window
        self.quantity = float(quantity)

    def on_bar(self, context: StrategyContext) -> List[OrderIntent]:
        order_intents: List[OrderIntent] = []

        # iterate every symbol available at this timestamp
        for symbol in context.candles.keys():
            # retrieve close series with one extra value so we can compute prev SMA
            series_short = context.get_series(symbol, field="close", limit=self.short_window + 1)
            series_long = context.get_series(symbol, field="close", limit=self.long_window + 1)
            
            def compute_prev_curr(series: List[float], window: int):
                """Return (prev_sma, curr_sma) where prev is SMA on the window
                immediately before the current bar and curr is SMA including current bar.
                If not enough data, returns (None, None) or partial Nones.
                """
                if len(series) < window:
                    return None, None
                # current SMA: last `window` values (may be equal to window)
                curr = sum(series[-window:]) / window
                # previous SMA: the `window` values just before the current bar
                prev = None
                if len(series) >= window + 1:
                    prev = sum(series[-(window + 1):-1]) / window
                return prev, curr

            prev_short, curr_short = compute_prev_curr(series_short, self.short_window)
            prev_long, curr_long = compute_prev_curr(series_long, self.long_window)

            # need both prev and curr values to detect a cross
            if None in (prev_short, curr_short, prev_long, curr_long):
                continue

            # detect bullish cross: short crosses above long
            if prev_short <= prev_long and curr_short > curr_long:
                order_intents.append(OrderIntent(symbol=symbol, side=Side.BUY, quantity=self.quantity))

            # detect bearish cross: short crosses below long
            elif prev_short >= prev_long and curr_short < curr_long:
                order_intents.append(OrderIntent(symbol=symbol, side=Side.SELL, quantity=self.quantity))

        return order_intents
