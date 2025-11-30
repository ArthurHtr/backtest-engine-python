from simple_broker.models import Trade, PortfolioSnapshot, Position, PositionSide


class PortfolioState:
    """
    Manages the internal state of the portfolio, supporting long and short positions.

    Conventions:
      - Trade.quantity > 0 : BUY
      - Trade.quantity < 0 : SELL
      - Position.quantity  : strictly positive magnitude
      - Position.side      : LONG or SHORT

    On autorise un trade unique à traverser 0 (reverse):
      - LONG + gros SELL -> fermeture du long puis ouverture d'un short
      - SHORT + gros BUY -> couverture du short puis ouverture d'un long
    """

    def __init__(self, initial_cash: float):
        self.cash: float = initial_cash
        # mapping symbol -> Position
        self.positions: dict[str, Position] = {}

    # -------------------------------------------------------------------------
    # Core update logic
    # -------------------------------------------------------------------------

    def apply_trade(self, trade: Trade) -> None:
        """
        Updates the portfolio state based on a single trade:
          - met à jour position (quantity, entry_price, realized_pnl),
          - supprime la position si elle est entièrement close,
          - met à jour le cash (notional + fee).
        """
        symbol = trade.symbol
        qty = trade.quantity        # >0 BUY, <0 SELL
        price = trade.price

        position = self.positions.get(symbol, None)

        # ------------------------------------------------------------------
        # 1. Pas de position existante : ouverture directe (LONG ou SHORT)
        # ------------------------------------------------------------------
        if position is None:
            if qty == 0:
                # Trade sans quantité -> seul effet: la fee
                self.cash -= trade.fee
                return

            side = PositionSide.LONG if qty > 0 else PositionSide.SHORT
            position = Position(
                symbol=symbol,
                side=side,
                quantity=abs(qty),   # magnitude
                entry_price=price,
            )
            # S'assurer que realized_pnl existe
            if not hasattr(position, "realized_pnl"):
                position.realized_pnl = 0.0

            self.positions[symbol] = position

        else:
            # On part du principe que position.quantity > 0 (magnitude)
            current_qty = position.quantity
            entry_price = position.entry_price

            if not hasattr(position, "realized_pnl"):
                position.realized_pnl = 0.0

            # ------------------------------------------------------------------
            # 2. Position LONG
            # ------------------------------------------------------------------
            if position.side == PositionSide.LONG:
                if qty > 0:
                    # On ajoute au long existant -> moyenne pondérée du prix d'entrée
                    new_qty = current_qty + qty
                    position.entry_price = (
                        entry_price * current_qty + price * qty
                    ) / new_qty
                    position.quantity = new_qty

                elif qty < 0:
                    # On vend du long (fermeture partielle / totale / reverse)
                    sell_qty = -qty  # quantité vendue > 0

                    if sell_qty < current_qty:
                        # Fermeture partielle du long
                        close_qty = sell_qty
                        pnl = (price - entry_price) * close_qty
                        position.realized_pnl += pnl

                        remaining = current_qty - close_qty
                        position.quantity = remaining
                        # entry_price reste celui de la partie restante

                    elif sell_qty == current_qty:
                        # Fermeture totale du long
                        close_qty = current_qty
                        pnl = (price - entry_price) * close_qty
                        position.realized_pnl += pnl

                        # Position entièrement close
                        del self.positions[symbol]
                        position = None  # pour la suite

                    else:
                        # Reverse : on ferme le long puis on ouvre un short
                        close_qty = current_qty
                        pnl = (price - entry_price) * close_qty
                        position.realized_pnl += pnl

                        remaining_short = sell_qty - current_qty  # > 0

                        # On réutilise le même objet Position :
                        # nouveau short avec entry = prix du trade
                        position.side = PositionSide.SHORT
                        position.quantity = remaining_short
                        position.entry_price = price

                # qty == 0 -> rien à faire sur la position

            # ------------------------------------------------------------------
            # 3. Position SHORT
            # ------------------------------------------------------------------
            elif position.side == PositionSide.SHORT:
                if qty < 0:
                    # On augmente le short (SELL supplémentaire)
                    add_qty = -qty  # quantité supplémentaire > 0
                    new_qty = current_qty + add_qty
                    position.entry_price = (
                        entry_price * current_qty + price * add_qty
                    ) / new_qty
                    position.quantity = new_qty

                elif qty > 0:
                    # BUY pour couvrir le short (fermeture partielle / totale / reverse)
                    buy_qty = qty  # > 0

                    if buy_qty < current_qty:
                        # Couverture partielle du short
                        close_qty = buy_qty
                        pnl = (entry_price - price) * close_qty
                        position.realized_pnl += pnl

                        remaining = current_qty - close_qty
                        position.quantity = remaining
                        # entry_price reste celui de la partie restante

                    elif buy_qty == current_qty:
                        # Couverture totale du short
                        close_qty = current_qty
                        pnl = (entry_price - price) * close_qty
                        position.realized_pnl += pnl

                        del self.positions[symbol]
                        position = None  # pour la suite

                    else:
                        # Reverse : on couvre le short puis on ouvre un long
                        close_qty = current_qty
                        pnl = (entry_price - price) * close_qty
                        position.realized_pnl += pnl

                        remaining_long = buy_qty - current_qty  # > 0

                        position.side = PositionSide.LONG
                        position.quantity = remaining_long
                        position.entry_price = price

                # qty == 0 -> rien à faire sur la position

        # ----------------------------------------------------------------------
        # 4. Mise à jour du cash (notional + fee)
        # ----------------------------------------------------------------------
        # BUY (qty > 0)  : cash diminue (on paye qty * price)
        # SELL (qty < 0) : cash augmente (on reçoit |qty| * price)
        self.cash -= qty * price + trade.fee

        # Nettoyage des petits résidus numériques
        if position is not None:
            if abs(position.quantity) < 1e-10:
                del self.positions[symbol]

    # -------------------------------------------------------------------------
    # Snapshot
    # -------------------------------------------------------------------------

    def build_snapshot(self, price_by_symbol: dict, timestamp: str) -> PortfolioSnapshot:
        """
        Builds a snapshot of the portfolio at a specific point in time.
        Equity = cash + market value of positions (longs - shorts).
        """
        equity = self.cash
        positions_snapshot: list[Position] = []

        for symbol, position in self.positions.items():
            current_price = price_by_symbol.get(symbol)
            if current_price is None:
                continue  # pas de prix => on ne marque pas cette position

            # Valeur de marché
            if position.side == PositionSide.LONG:
                market_value = current_price * position.quantity
            else:  # SHORT
                market_value = -current_price * abs(position.quantity)

            equity += market_value

            # On garde entry_price et realized_pnl pour info, mais on n'en sert plus
            # pour le calcul d'equity (le realized est déjà dans self.cash).
            positions_snapshot.append(
                Position(
                    symbol=position.symbol,
                    side=position.side,
                    quantity=position.quantity,
                    entry_price=position.entry_price,
                    realized_pnl=position.realized_pnl,
                )
            )

        return PortfolioSnapshot(
            timestamp=timestamp,
            cash=self.cash,
            equity=equity,
            positions=positions_snapshot,
        )
