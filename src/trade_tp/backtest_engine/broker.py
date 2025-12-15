from typing import Dict, List, Tuple

from trade_tp.backtest_engine.models.enums import PositionSide, Side
from trade_tp.backtest_engine.models.candle import Candle
from trade_tp.backtest_engine.models.trade import Trade
from trade_tp.backtest_engine.models.order_intent import OrderIntent
from trade_tp.backtest_engine.models.portfolio_snapshot import PortfolioSnapshot

from trade_tp.backtest_engine.portfolio import PortfolioState


from trade_tp.backtest_engine.models.symbol import Symbol

class BacktestBroker:
    """
    Broker simulé utilisé par le moteur de backtest.
    ...
    """

    def __init__(self, initial_cash: float, fee_rate: float, margin_requirement: float, maintenance_margin: float = 0.25, symbols_map: Dict[str, Symbol] = None):
        self.portfolio = PortfolioState(initial_cash)
        self.fee_rate = fee_rate
        self.margin_requirement = margin_requirement
        self.maintenance_margin = maintenance_margin
        self.symbols_map = symbols_map or {}

    def set_symbols_map(self, symbols_map: Dict[str, Symbol]):
        self.symbols_map = symbols_map


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

        # --- Rounding Logic ---
        sym_info = self.symbols_map.get(symbol)
        if sym_info:
            # Round quantity
            qty = sym_info.round_quantity(qty)
            # Round price (though usually we take market price, but for LIMIT orders it matters. 
            # Here we assume MARKET orders execute at market price, but maybe we should round it too?)
            # Actually, execution price is usually determined by the market, but let's assume 
            # the simulation respects price steps.
            # However, `price` here comes from `price_by_symbol` which is the candle close.
            # We shouldn't round the market price, but we should round the quantity.
            
            if qty == 0:
                 return (
                    {
                        "intent": intent,
                        "status": "rejected",
                        "reason": "Quantity too small (below min_quantity or step).",
                    },
                    None,
                )
        # ----------------------

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

    def _check_margin_call(self, candles: Dict[str, Candle], price_by_symbol: Dict[str, float], timestamp: str) -> List[Dict]:
        """
        Vérifie si la marge de maintenance est respectée pour les positions short existantes.
        Si ce n'est pas le cas, génère des trades de liquidation (achat pour fermer).
        
        AMÉLIORATION RÉALISME :
        On utilise le prix 'High' de la bougie courante pour vérifier la liquidation des Shorts.
        Si le High a touché le niveau de liquidation, on considère qu'on a été liquidé au pire moment,
        même si le Close est redescendu ensuite.
        """
        liquidation_details = []
        
        # On itère sur une copie car on peut modifier le dictionnaire des positions
        for symbol, position in list(self.portfolio.positions.items()):
            if position.side == PositionSide.SHORT:
                # 1. Déterminer le prix de référence pour le check de marge
                # Pour un short, le pire cas est le High de la bougie.
                candle = candles.get(symbol)
                check_price = candle.high if candle else price_by_symbol.get(symbol, position.entry_price)
                
                # 2. Calcul de l'equity avec ce prix "pire cas"
                # Note: Pour être très précis, il faudrait recalculer toute l'equity avec les prix High/Low
                # de tous les actifs, mais ici on fait une approximation conservatrice locale.
                current_equity = self._compute_equity({**price_by_symbol, symbol: check_price})
                
                notional = check_price * abs(position.quantity)
                required_maint = notional * self.maintenance_margin
                
                # Si l'equity est inférieure à la marge requise pour CETTE position au prix HIGH
                if current_equity < required_maint:
                    # Liquidation de la position
                    qty_to_close = abs(position.quantity) # Buy back everything
                    
                    # On liquide au prix du check (High) car c'est là que le stop-out a eu lieu
                    exec_price = check_price 
                    fee = (qty_to_close * exec_price) * self.fee_rate
                    
                    trade = Trade(
                        symbol=symbol,
                        quantity=qty_to_close, # Positive for BUY
                        price=exec_price,
                        fee=fee,
                        timestamp=timestamp
                    )
                    
                    # Force apply (check_margin=False) car c'est une liquidation forcée
                    # On met à jour le price_by_symbol pour que l'apply_trade utilise le bon prix pour ce symbole
                    self.portfolio.apply_trade(trade, {**price_by_symbol, symbol: exec_price}, self.maintenance_margin, check_margin=False)
                    
                    liquidation_details.append({
                        "intent": None,
                        "status": "liquidated",
                        "trade": trade,
                        "reason": f"Maintenance margin breach at High price {exec_price}"
                    })
                    
        return liquidation_details

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

        # 1. Vérification des appels de marge sur les positions existantes
        # On passe 'candles' pour pouvoir vérifier le High/Low
        liquidation_details = self._check_margin_call(candles, price_by_symbol, timestamp)
        execution_details.extend(liquidation_details)

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
