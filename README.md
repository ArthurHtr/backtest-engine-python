# backtest-engine-python

Un moteur de backtest Python léger pour prototyper et tester des stratégies
intraday sur des séries de bougies (candles). Ce README est pensé pour être
instructif : il explique les concepts principaux, fournit des exemples et des
repères pour debugger et étendre le projet.

## Vue d'ensemble

Principaux composants :
- `src/trade_tp/engine.py` : boucle de backtest (BacktestEngine).
- `src/trade_tp/simple_broker/` : broker simulé, `PortfolioState` et les
  modèles (trade, position, candle, order_intent, portfolio_snapshot).
- `src/trade_tp/sdk/` : fournisseur de données, exporteurs, utilitaires.
- `run_backtest.py` : script d'exécution et génération du rapport
  `backtest_analysis.txt`.

Objectifs design
- Simplicité et transparence : code lisible pour comprendre l'impact d'une
  stratégie sur le portefeuille.
- Séparation des responsabilités : la stratégie produit des `OrderIntent`, le
  broker valide et construit le `Trade`, le `PortfolioState` applique les
  conséquences financières.

## Concepts financiers expliqués (pour ce projet)

- Equity (Net Asset Value) :
  equity = cash + somme(market_value des positions)
  - Long : market_value = price * quantity
  - Short : market_value = - price * abs(quantity)
  Cette définition est utilisée partout (reporting et validations).

- Frais (fee_rate) : fraction du notional (price * quantity) appliquée à
  chaque trade. Par exemple fee_rate = 0.002 => frais = 0.2% du notional.

- Margin requirements :
  - `margin_requirement` (initial) : fraction du notional exigée pour
    ouvrir une position short.
  - `maintenance_margin` : fraction du notional qui doit être couverte par
    l'equity pour conserver un short. Si l'equity simulée tombe en dessous
    du niveau de maintenance pour une position short, la logique peut refuser
    l'ordre ou initier une liquidation.

Pourquoi deux étapes de validation ?
- Le broker réalise des validations pré-trade (cash, marge initiale) pour
  filtrer les ordres impossibles rapidement.
- Le `PortfolioState.apply_trade` simule le post-trade et effectue la
  validation finale de maintenance margin. Cette simulation évite d'exécuter
  puis d'annuler un trade (problème de "double frais").

## Installation rapide

Prérequis : Python 3.10+.

1. Créer et activer un virtualenv :

```bash
python -m venv venv
source venv/bin/activate
```

2. Installer les dépendances minimales (si `requirements.txt` existe) :

```bash
pip install -r requirements.txt
```

Sinon installer au minimum :

```bash
pip install tqdm
```

## Lancer un backtest (exemple)

1. Préparer vos séries de candles (format attendu = liste de `Candle` par
   symbole). Des exemples de stratégies `buy_and_hold_strategy.py` et
   `moving_average_crossover_strategy.py` sont fournis.

2. Lancer :

```bash
venv/bin/python run_backtest.py
```

3. Résultat : `backtest_analysis.txt` sera généré avec un log détaillé par
   timestamp (candles, snapshot before/after, intents, execution details).

## Exemple minimal de stratégie

La stratégie doit hériter de `BaseStrategy` et implémenter `on_bar(context)` :

```python
from src.trade_tp.simple_broker.models.order_intent import OrderIntent, Side

class MyStrategy(BaseStrategy):
    def on_bar(self, context):
        # Context contient candles, snapshot, past_candles
        # Exemple : acheter 10 actions de AAPL
        return [OrderIntent(symbol="AAPL", side=Side.BUY, quantity=10)]
```

Ordre attendu : `OrderIntent(symbol: str, side: Side, quantity: float)`.

## Référence rapide des API internes

- BacktestEngine (`src/trade_tp/engine.py`)
  - run(candles_by_symbol) -> list[dict]
    - Itère par timestamp, appelle la stratégie puis le broker, collecte les
      snapshots et exécutions.

- BacktestBroker (`src/trade_tp/simple_broker/broker.py`)
  - get_snapshot(candles) -> PortfolioSnapshot
  - process_bars(candles, order_intents) -> (snapshot_after, execution_details)
    - `_validate_and_build_trade` : validations pré-trade conservatrices
    - utilise `PortfolioState.apply_trade` pour la validation finale et le
      commit

- PortfolioState (`src/trade_tp/simple_broker/portfolio.py`)
  - apply_trade(trade, price_by_symbol, maintenance_margin) -> (accepted, reason)
  - build_snapshot(price_by_symbol, timestamp) -> PortfolioSnapshot

## Debugging & pièges courants (avec actions concrètes)

- Equity négative :
  - Vérifier que l'equity affichée est bien cash + market value.
  - Inspecter les frais facturés (fee_rate) et l'ordre d'application des
    trades (les frais diminuent le cash immédiatement).
  - Reproduire le scénario en imprimant l'entrée/sortie de
    `BacktestBroker._validate_and_build_trade` et `PortfolioState.apply_trade`.

- Orders exécutés puis annulés (double frais) :
  - Chercher des appels où l'application d'un trade est effectuée avant la
    vérification finale. La logique actuelle simule la validation finale dans
    `apply_trade` pour éviter ce cas.

- Reversals (traverser 0) :
  - Les reversals sont supportés mais il est utile de tester les cas limites
    (par ex. partial close + open short) avec de petits scénarios unitaires.

## Tests recommandés

- Ajouter des tests unitaires pour :
  - `apply_trade` : buy/sell, close partial, close full, reverse, short that
    breaches maintenance.
  - `_validate_and_build_trade` du broker : insufficient cash, insufficient
    margin, missing price.

Utilisez `pytest` et créez un dossier `tests/`.

## Configuration & paramètres

Actuellement les paramètres (fee_rate, margin_requirement,
maintenance_margin) sont passés à l'initialisation du broker. À améliorer :
- ajouter un fichier de configuration (TOML/YAML) et une CLI pour lancer
  différents scénarios.

## Contribution

- Fork -> branch -> PR. Merci d'ajouter des tests et d'expliquer les choix
  dans la description de la PR.
- Si vous modifiez la logique de marge ou d'équity, ajoutez des cas de test
  pour éviter les régressions.

## Pistes d'évolution

- Ajouter un module d'analytics (drawdown, pnl per trade, sharpe, etc.).
- Supporter exécution partielle et carnet d'ordres simulé (slippage, depth).
- Exporter les résultats en CSV/JSON + visualisations simples.

## Licence

À renseigner (ex: MIT). Si vous partagez ce dépôt, indiquez la licence souhaitée.

---

Si tu veux, j'ajoute maintenant :
- un exemple de test unitaire pour `apply_trade` ; ou
- des exemples concrets de stratégies (MA crossover complet) ; ou
- une configuration TOML et une petite CLI pour lancer des scénarios.
Dis-moi ce que tu préfères et j'attaque.
