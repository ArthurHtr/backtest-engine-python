from src.trade_tp.backtest_engine.models.strategy import BaseStrategy, StrategyContext
from src.trade_tp.backtest_engine.models.order_intent import OrderIntent
from src.trade_tp.backtest_engine.models.enums import Side
from typing import List


# ------------------------------ strategie utilisateur ------------------------------ #


class BuyAndHoldStrategy(BaseStrategy):
    """
    A simple Buy and Hold strategy that buys a fixed quantity of each symbol at the first timestamp
    and sells all positions at the last timestamp.
    """
    def __init__(self, buy_timestamp: str = "2025-11-01T00:00:00", sell_timestamp: str = "2025-11-30T00:00:00"):
        self.first_timestamp = buy_timestamp
        self.last_timestamp = sell_timestamp

    def on_bar(self, context: StrategyContext):

        order_intents = []

        timestamp = context.candles[next(iter(context.candles))].timestamp

        # Place buy orders only at the first timestamp
        if timestamp == self.first_timestamp:
            for symbol in context.candles.keys():
                order_intents.append(OrderIntent(
                    symbol=symbol,
                    side=Side.BUY,
                    quantity=100  # Fixed quantity to buy
                ))

        # Place sell orders only at the last timestamp
        if timestamp == self.last_timestamp:
            for position in context.portfolio_snapshot.positions:
                order_intents.append(OrderIntent(
                    symbol=position.symbol,
                    side=Side.SELL,
                    quantity=position.quantity  # Sell the entire position
                ))

        return order_intents
    
class MovingAverageCrossoverStrategy(BaseStrategy):
    """Simple MA crossover strategy for multiple symbols.

    - Trade uniquement sur les franchissements (crossovers) de moyenne mobile :
      * Golden cross : short MA passe de dessous à au-dessus de la long MA -> BUY
      * Death cross  : short MA passe de dessus à en-dessous de la long MA -> SELL
    - Si le timestamp courant est le dernier timestamp du backtest,
      on envoie un ordre de vente sur tous les symboles (flatten naïf).
    """

    def __init__(
        self,
        short_window: int = 2,
        long_window: int = 5,
        quantity: float = 10.0,
        last_timestamp=None,
    ):
        self.short_window = short_window
        self.long_window = long_window
        self.quantity = quantity
        self.last_timestamp = last_timestamp

    def on_bar(self, context: StrategyContext) -> List[OrderIntent]:
        order_intents: List[OrderIntent] = []

        # On récupère le timestamp du bar courant
        # (on suppose que tous les symboles du bar ont le même timestamp)
        first_symbol = next(iter(context.candles))
        timestamp = context.candles[first_symbol].timestamp

        # Si on est sur le dernier timestamp du backtest -> on vend tout
        if self.last_timestamp is not None and timestamp == self.last_timestamp:
            for symbol in context.candles.keys():
                order_intents.append(
                    OrderIntent(
                        symbol=symbol,
                        side=Side.SELL,
                        quantity=self.quantity,
                    )
                )
            return order_intents

        # Taille de fenêtre max pour récupérer assez d'historique
        max_window = max(self.short_window, self.long_window)

        # Logique MA avec détection de crossovers
        for symbol in context.candles.keys():
            # On prend une barre de plus pour pouvoir comparer "avant" / "maintenant"
            closes = context.get_series(symbol, "close", limit=max_window + 1)

            # Il faut au moins max_window + 1 points pour calculer MA_prev et MA_curr
            if len(closes) < max_window + 1:
                continue

            # Short MA actuelle (utilise les short_window dernières closes)
            short_ma_curr = sum(closes[-self.short_window:]) / self.short_window
            # Short MA précédente (décalée d'une barre)
            short_ma_prev = sum(closes[-self.short_window - 1:-1]) / self.short_window

            # Long MA actuelle
            long_ma_curr = sum(closes[-self.long_window:]) / self.long_window
            # Long MA précédente
            long_ma_prev = sum(closes[-self.long_window - 1:-1]) / self.long_window

            # Différences (short - long) avant et après
            diff_prev = short_ma_prev - long_ma_prev
            diff_curr = short_ma_curr - long_ma_curr

            # Golden cross: on passe de <= 0 à > 0 -> signal d'achat
            if diff_prev <= 0 and diff_curr > 0:
                order_intents.append(
                    OrderIntent(
                        symbol=symbol,
                        side=Side.BUY,
                        quantity=self.quantity,
                    )
                )
            # Death cross: on passe de >= 0 à < 0 -> signal de vente
            elif diff_prev >= 0 and diff_curr < 0:
                order_intents.append(
                    OrderIntent(
                        symbol=symbol,
                        side=Side.SELL,
                        quantity=self.quantity,
                    )
                )
            # Sinon, pas de signal (on ne renvoie rien pour ce symbole)

        return order_intents



# ------------------------------ exécution du backtest ------------------------------ #

from src.trade_tp.runner import run_backtest

if __name__ == "__main__":

    result = run_backtest(
        symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
        start="2025-11-01T00:00:00",
        end="2025-11-30T00:00:00",
        timeframe="5m",

        initial_cash=100_000.0,

        strategy = MovingAverageCrossoverStrategy(
            short_window=5,
            long_window=20,
            quantity=10.0,
            last_timestamp="2025-11-30T00:00:00",
        ),

        api_key="YOUR_API_KEY_HERE",
        base_url="https://api.your-backtest-platform.com",
        
        fee_rate=0.001,
        margin_requirement=0.5,

        save_results=True,
    )

    