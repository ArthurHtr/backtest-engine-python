# trade_tp — Backtest engine & broker simulator

`trade_tp` est une petite librairie Python pour prototyper et exécuter des
backtests de stratégies de trading sur des séries de bougies (candles).

## Vue d'ensemble

- Moteur de backtest multi-symboles (`BacktestEngine`).
- Broker simulé (`BacktestBroker`) qui valide les `OrderIntent` et applique
  les `Trade` au `Portfolio` (cash, positions, frais, PnL réalisé).
- Modules utilitaires pour générer des données simulées et produire des
  rapports simples.

Le code se trouve sous le package `trade_tp` (répertoire `src/trade_tp`).

## Installation

Prérequis : Python 3.10+

Installation en développement :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Installation pour utilisation :

```bash
pip install .
```

## Concepts clés et API

**StrategyContext** : fourni à la stratégie à chaque barre (bar). Champs et aides :
- `candles`: mapping `symbol -> Candle` pour le timestamp courant.
- `portfolio_snapshot`: `PortfolioSnapshot` (état du portefeuille avant exécution des intents).
- `past_candles`: mapping `symbol -> list[Candle]` (historique incluant la barre courante).
- `current_timestamp()`: retourne le timestamp courant.
- `get_history(symbol, limit=None)`: renvoie des `Candle` historiques.
- `get_series(symbol, field, limit=None)`: renvoie une liste de valeurs numériques (ex: `close`).

Les stratégies héritent de `BaseStrategy` et implémentent `on_bar(context: StrategyContext)`.

**OrderIntent** : objet retourné par la stratégie pour demander l'exécution d'un ordre.
- Champs principaux : `symbol` (str), `side` (`Side.BUY`/`Side.SELL`), `quantity` (float positive), `order_type` (ex: `MARKET`), `limit_price`.
- Convention : la stratégie fournit une quantité positive; le broker interprète `side` pour construire le `Trade`.

**PortfolioSnapshot** : vue immuable de l'état du portefeuille à un timestamp.
- Champs : `timestamp`, `cash`, `equity`, `positions` (liste de `Position`).
- `positions` contient des objets `Position` avec `symbol`, `side` (LONG/SHORT), `quantity`, `entry_price`, `realized_pnl`.

Entrées / sorties du runner
- `BacktestEngine.run(candles_by_symbol)`
  - Entrée : `candles_by_symbol` = `dict[str, list[Candle]]` (liste ordonnée par timestamp pour chaque symbole).
  - Sortie : `List[dict]` où chaque dict contient :
	- `timestamp`, `candles`, `snapshot_before`, `snapshot_after`, `order_intents`, `execution_details`.

## Exemple d'utilisation

Voici deux stratégies d'exemple et une façon simple de lancer un backtest via `run_backtest`.

```python
from typing import List

from trade_tp.backtest_engine.models.strategy import BaseStrategy, StrategyContext
from trade_tp.backtest_engine.models.order_intent import OrderIntent
from trade_tp.backtest_engine.models.enums import Side


# ------------------------------ stratégie utilisateur ------------------------------ #


class MovingAverageCrossoverStrategy(BaseStrategy):
	"""Simple MA crossover pour plusieurs symboles.

	- Golden cross -> BUY
	- Death cross  -> SELL
	- Flatten au dernier timestamp.
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

		first_symbol = next(iter(context.candles))
		timestamp = context.candles[first_symbol].timestamp

		if self.last_timestamp is not None and timestamp == self.last_timestamp:
			for symbol in context.candles.keys():
				order_intents.append(
					OrderIntent(symbol=symbol, side=Side.SELL, quantity=self.quantity)
				)
			return order_intents

		max_window = max(self.short_window, self.long_window)

		for symbol in context.candles.keys():
			closes = context.get_series(symbol, "close", limit=max_window + 1)

			if len(closes) < max_window + 1:
				continue

			short_ma_curr = sum(closes[-self.short_window:]) / self.short_window
			short_ma_prev = sum(closes[-self.short_window - 1:-1]) / self.short_window

			long_ma_curr = sum(closes[-self.long_window:]) / self.long_window
			long_ma_prev = sum(closes[-self.long_window - 1:-1]) / self.long_window

			diff_prev = short_ma_prev - long_ma_prev
			diff_curr = short_ma_curr - long_ma_curr

			if diff_prev <= 0 and diff_curr > 0:
				order_intents.append(OrderIntent(symbol=symbol, side=Side.BUY, quantity=self.quantity))
			elif diff_prev >= 0 and diff_curr < 0:
				order_intents.append(OrderIntent(symbol=symbol, side=Side.SELL, quantity=self.quantity))

		return order_intents



# ------------------------------ exécution du backtest ------------------------------ #

from trade_tp.runner import run_backtest

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

		api_key=None,
		base_url="",
        
		fee_rate=0.001,
		margin_requirement=0.5,

		save_results=True,
	)
```

Remarque : `run_backtest` retourne un dictionnaire contenant `candles_logs` et `summary`.

## Licence

Ce projet est distribué sous licence MIT. Voir le fichier `LICENSE`.