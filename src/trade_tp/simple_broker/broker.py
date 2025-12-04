from typing import Dict, List, Tuple

from src.trade_tp.simple_broker.models.enums import PositionSide, Side
from src.trade_tp.simple_broker.models.candle import Candle
from src.trade_tp.simple_broker.models.trade import Trade
from src.trade_tp.simple_broker.models.order_intent import OrderIntent
from src.trade_tp.simple_broker.models.portfolio_snapshot import PortfolioSnapshot

from src.trade_tp.simple_broker.portfolio import PortfolioState


class BacktestBroker:
    """
    Broker simulé utilisé par le moteur de backtest.

    Ce composant a pour rôle d'interpréter les intentions d'ordre (OrderIntent)
    provenant d'une stratégie, d'effectuer des validations préalables (cash,
    marge, disponibilité du prix, logique de reverse), de construire un objet
    `Trade` et de demander l'application du trade au `PortfolioState`.

    Comportement clé et invariants
    - L'équité (equity) utilisée pour les contrôles est toujours calculée comme
      : cash + valeur de marché des positions (concorde avec
      `PortfolioState.build_snapshot`).
    - Les validations sensibles à la marge sont effectuées en deux étapes :
      1) validations pré-trade conservatrices dans `_validate_and_build_trade`
         (ex : suffisance de cash pour achat, marge initiale requise pour
         l'ouverture d'un short, contrôle de reverse implicite) ;
      2) validation finale de maintenance margin exécutée au moment de
         l'application via `PortfolioState.apply_trade`, qui simule le post-trade
         et peut refuser sans muter l'état si la marge de maintenance est
         insuffisante. Cette séparation évite d'exécuter un trade puis de devoir
         l'annuler (double frais / incohérences).

    Paramètres d'initialisation
    - initial_cash (float) : cash initial du portefeuille.
    - fee_rate (float) : fraction appliquée au notional de l'ordre pour calculer
      les frais (ex : 0.002 = 0.2%).
    - margin_requirement (float) : fraction d'exigence initiale pour ouvrir une
      exposition (utilisée dans les validations pré-trade pour les shorts).
    - maintenance_margin (float) : fraction de maintenance utilisée pour décider
      si une position short doit être refusée/liquidée (ex : 0.25 pour 25%).

    Notes
    - Les méthodes publiques retournent des structures simples (snapshot, liste
      de détails d'exécution) utiles au moteur pour journaliser / exporter le
      résultat du bar.
    - Les messages et raisons de rejet sont conçus pour être lisibles et
      suffisants pour du débogage utilisateur lors d'un backtest.
    """

    def __init__(self, initial_cash: float, fee_rate: float, margin_requirement: float, maintenance_margin: float = 0.25):
        self.portfolio = PortfolioState(initial_cash)
        self.fee_rate = fee_rate
        self.margin_requirement = margin_requirement
        # maintenance_margin est la fraction du notionnel qui doit être couverte
        # par l'equity pour éviter la liquidation immédiate (ex: 0.25 = 25%).
        self.maintenance_margin = maintenance_margin

    def _compute_equity(self, price_by_symbol: Dict[str, float]) -> float:
        """
        Calcule l'equity (Net Asset Value) du portefeuille pour des prix
        donnés.

        equity = cash + somme(market_value des positions)

        - Pour une position LONG : market_value = price * quantity
        - Pour une position SHORT : market_value = - price * abs(quantity)

        Ce calcul correspond explicitement à `PortfolioState.build_snapshot`
        afin d'éviter toute divergence entre validation et reporting.

        Args:
            price_by_symbol: mapping symbol -> prix (float) à utiliser.

        Returns:
            float: valeur de l'equity calculée.
        """
        equity = self.portfolio.cash

        for symbol, pos in self.portfolio.positions.items():
            price = price_by_symbol.get(symbol, pos.entry_price)

            if pos.side == PositionSide.LONG:
                market_value = price * pos.quantity
            elif pos.side == PositionSide.SHORT:
                market_value = -price * abs(pos.quantity)
            else:
                market_value = 0.0

            equity += market_value

        return equity

    def _build_price_map(self, candles: Dict[str, Candle]) -> Dict[str, float]:
        """
        Retourne un mapping symbol -> close price à partir d'un dictionnaire de
        bougies (candles). Filtre les entrées `None`.
        """
        return {symbol: c.close for symbol, c in candles.items() if c is not None}

    def _validate_and_build_trade(self, intent: OrderIntent, price_by_symbol: Dict[str, float], timestamp: str) -> Tuple[Dict, Trade | None]:
        """
        Valide une intention d'ordre et construit un `Trade` si l'ordre peut
        être accepté selon des règles conservatrices.

        Comportement géré
        - Vérification de la présence d'un prix pour le symbole.
        - Calcul des frais et du notional.
        - Traitement des cas : achat (BUY), vente (SELL), couverture partielle,
          fermeture totale, reverse implicite (ex: transformer un long en
          short), ouverture/augmentation de short.
        - Vérification pré-trade de cash pour les achats et des exigences de
          marge initiale pour la partie short.
        - Vérification anticipée de la maintenance margin pour éviter
          l'exécution suivie d'une liquidation immédiate.

        Retourne une paire (detail, trade_or_none) où :
        - detail : dict décrivant le statut ('executed' ou 'rejected') et la
          raison (utile pour les logs/explanations)
        - trade_or_none : instance de `Trade` si l'ordre peut être appliqué, ou
          None en cas de rejet.

        Important:
        - Cette méthode effectue des validations préalables. La validation
          finale de maintenance est effectuée par `PortfolioState.apply_trade`
          qui simule le post-trade et peut refuser sans muter l'état.
        """
        symbol = intent.symbol

        if symbol not in price_by_symbol:
            return (
                {
                    "intent": intent,
                    "status": "rejected",
                    "reason": "No price available for symbol.",
                },
                None,
            )

        price = price_by_symbol[symbol]
        qty = intent.quantity
        notional = qty * price
        fee = abs(notional) * self.fee_rate

        position = self.portfolio.positions.get(symbol)

        # BUY
        if intent.side == Side.BUY:
            # Si on couvre un short existant, on n'applique pas de nouvelle marge
            # pour la partie couverture; si l'achat ouvre un long (reverse),
            # celui-ci est financé en cash.
            total_cost = notional + fee
            if self.portfolio.cash < total_cost:
                return (
                    {"intent": intent, "status": "rejected", "reason": "Insufficient cash."},
                    None,
                )

            trade_quantity = qty

        # SELL
        elif intent.side == Side.SELL:
            # Vente quand position LONG existante : fermeture partielle/totale
            if position is not None and position.side == PositionSide.LONG:
                current_qty = position.quantity

                if qty <= current_qty:
                    # Simple clôture partielle ou totale du long
                    trade_quantity = -qty

                else:
                    # Reverse implicite : on clôture le long puis on ouvre un
                    # short pour la quantité excédentaire -> la partie short
                    # est soumise à marge initiale/maintenance.
                    extra_short = qty - current_qty
                    extra_notional = extra_short * price
                    required_margin = abs(extra_notional) * self.margin_requirement

                    # Simule les effets immédiats de la clôture du long
                    proceeds_close = current_qty * price
                    cash_after_close = self.portfolio.cash + proceeds_close - fee

                    other_market = 0.0
                    for s, p in self.portfolio.positions.items():
                        if s == symbol:
                            continue
                        p_price = price_by_symbol.get(s, p.entry_price)
                        if p.side == PositionSide.LONG:
                            other_market += p_price * p.quantity
                        else:
                            other_market += -p_price * abs(p.quantity)

                    equity_after_close = cash_after_close + other_market

                    required_maint = abs(extra_notional) * self.maintenance_margin
                    if equity_after_close < required_maint:
                        return (
                            {"intent": intent, "status": "rejected", "reason": "Would breach maintenance margin on reverse."},
                            None,
                        )

                    if equity_after_close < required_margin:
                        return (
                            {"intent": intent, "status": "rejected", "reason": "Insufficient margin for reverse."},
                            None,
                        )

                    trade_quantity = -qty

            else:
                # Ouverture/augmentation d'un short
                required_margin = abs(notional) * self.margin_requirement

                cash_after = self.portfolio.cash + notional - fee

                other_market = 0.0
                for s, p in self.portfolio.positions.items():
                    if s == symbol:
                        continue
                    p_price = price_by_symbol.get(s, p.entry_price)
                    if p.side == PositionSide.LONG:
                        other_market += p_price * p.quantity
                    else:
                        other_market += -p_price * abs(p.quantity)

                equity_after = cash_after + other_market

                required_maint = abs(notional) * self.maintenance_margin
                if equity_after < required_maint:
                    return (
                        {"intent": intent, "status": "rejected", "reason": "Would breach maintenance margin."},
                        None,
                    )

                if equity_after < required_margin:
                    return (
                        {"intent": intent, "status": "rejected", "reason": "Insufficient margin."},
                        None,
                    )

                trade_quantity = -qty

        else:
            return (
                {"intent": intent, "status": "rejected", "reason": f"Unsupported side: {intent.side}"},
                None,
            )

        # Construction du Trade prêt à être appliqué. L'application finale
        # (commit) et la validation de maintenance sont effectuées dans
        # `PortfolioState.apply_trade`.
        trade = Trade(symbol=symbol, quantity=trade_quantity, price=price, fee=fee, timestamp=timestamp)

        return ({"intent": intent, "status": "executed", "trade": trade}, trade)

    def get_snapshot(self, candles: Dict[str, Candle]):
        """
        Retourne l'instantané (snapshot) du portefeuille à partir des candles
        fournies. Utile pour afficher l'état avant le traitement des ordres.

        Args:
            candles: mapping symbol -> Candle

        Returns:
            PortfolioSnapshot
        """
        price_by_symbol = self._build_price_map(candles)
        timestamp = next(iter(candles.values())).timestamp if candles else ""
        return self.portfolio.build_snapshot(price_by_symbol, timestamp)

    def process_bars(self, candles: Dict[str, Candle], order_intents: List[OrderIntent]) -> Tuple[PortfolioSnapshot, List[Dict]]:
        """
        Traite un ensemble d'ordres pour la barre courante.

        Pour chaque `OrderIntent` :
        - on valide et construit un `Trade` via `_validate_and_build_trade` ;
        - si un Trade est créé, on demande à `PortfolioState.apply_trade` de
          l'appliquer ; `apply_trade` effectue une simulation finale et peut
          refuser (retourne (accepted=False, reason=...)) sans muter l'état.

        L'utilisation de cette séquence évite : exécution -> rejet -> double
        frais, et garantit que la validation de maintenance est faite au plus
        juste avant le commit.

        Args:
            candles: mapping symbol -> Candle pour la barre courante.
            order_intents: liste d'OrderIntent fournie par la stratégie.

        Returns:
            Tuple[PortfolioSnapshot, List[Dict]] : snapshot après exécution et
            une liste de détails d'exécution (statut + raison/trade) pour
            chaque intent.
        """
        execution_details: List[Dict] = []

        price_by_symbol = self._build_price_map(candles)
        timestamp = next(iter(candles.values())).timestamp if candles else ""

        for intent in order_intents:
            detail, trade = self._validate_and_build_trade(intent, price_by_symbol=price_by_symbol, timestamp=timestamp)
            if trade is not None:
                # Essayer d'appliquer le trade ; PortfolioState.apply_trade
                # simule et refuse si la maintenance margin est insuffisante.
                accepted, reason = self.portfolio.apply_trade(trade, price_by_symbol, self.maintenance_margin)

                if not accepted:
                    execution_details.append({"intent": intent, "status": "rejected", "reason": reason})
                    continue

                execution_details.append({"intent": intent, "status": "executed", "trade": trade})
            else:
                execution_details.append(detail)

        snapshot = self.portfolio.build_snapshot(price_by_symbol, timestamp)

        return snapshot, execution_details
