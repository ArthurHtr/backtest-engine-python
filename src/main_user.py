from trade_tp.backtest_engine.models.strategy import BaseStrategy, StrategyContext
from trade_tp.backtest_engine.models.order_intent import OrderIntent
from trade_tp.backtest_engine.models.enums import Side, PositionSide
from typing import List


# ------------------------------ strategie utilisateur ------------------------------ #


class SmaCrossStrategy(BaseStrategy):
    """
    Stratégie de croisement de moyennes mobiles (SMA).
    - Si SMA courte > SMA longue : Achat (Long)
    - Si SMA courte < SMA longue : Vente (Short)
    """
    def __init__(self, short_window: int = 10, long_window: int = 30, quantity: float = 1.0):
        self.short_window = short_window
        self.long_window = long_window
        self.quantity = quantity

    def on_bar(self, context: StrategyContext) -> List[OrderIntent]:
        order_intents = []

        for symbol, candle in context.candles.items():
            # Récupération de l'historique (inclut la bougie courante)
            history = context.past_candles.get(symbol, [])
            
            if len(history) < self.long_window:
                continue

            # Calcul des SMA
            closes = [c.close for c in history]
            short_sma = sum(closes[-self.short_window:]) / self.short_window
            long_sma = sum(closes[-self.long_window:]) / self.long_window

            # Récupération de la position actuelle
            current_position = None
            for p in context.portfolio_snapshot.positions:
                if p.symbol == symbol:
                    current_position = p
                    break
            
            current_side = current_position.side if current_position else None
            current_qty = current_position.quantity if current_position else 0.0

            # Logique de trading
            if short_sma > long_sma:
                # Signal LONG
                if current_side == PositionSide.SHORT:
                    # Reverse : On ferme le short et on ouvre un long
                    # Quantité = taille du short + taille cible
                    qty_to_buy = current_qty + self.quantity
                    order_intents.append(OrderIntent(symbol, Side.BUY, qty_to_buy))
                elif current_side is None:
                    # Ouverture Long
                    order_intents.append(OrderIntent(symbol, Side.BUY, self.quantity))
            
            elif short_sma < long_sma:
                # Signal SHORT
                if current_side == PositionSide.LONG:
                    # Reverse : On ferme le long et on ouvre un short
                    # Quantité = taille du long + taille cible
                    qty_to_sell = current_qty + self.quantity
                    order_intents.append(OrderIntent(symbol, Side.SELL, qty_to_sell))
                elif current_side is None:
                    # Ouverture Short
                    order_intents.append(OrderIntent(symbol, Side.SELL, self.quantity))

        return order_intents


# ------------------------------ exécution du backtest ------------------------------ #

from trade_tp.runner import run_backtest

if __name__ == "__main__":

    result = run_backtest(
        symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
        start="2023-01-01T00:00:00",
        end="2023-06-01T00:00:00",
        timeframe="15m", # Daily timeframe for SMA strategy

        initial_cash=2_000.0,

        strategy = SmaCrossStrategy(
            short_window=10,
            long_window=30,
            quantity=10.0
        ),

        api_key="YOUR_API_KEY_HERE",
        base_url="https://api.your-backtest-platform.com",
        
        fee_rate=0,
        margin_requirement=0.5,

        save_results=True,
    )

