from typing import Dict, List, Optional, Tuple

from trade_tp.backtest_engine.entities.trade import Trade
from trade_tp.backtest_engine.entities.enums import PositionSide
from trade_tp.backtest_engine.entities.position import Position
from trade_tp.backtest_engine.entities.portfolio_snapshot import PortfolioSnapshot
from trade_tp.backtest_engine.portfolio.simulator import TradeSimulator

class Portfolio:
    """
    Représente l'état interne d'un portefeuille utilisé par le broker de backtest.
    
    Responsabilités:
    - Stocker le cash et les positions.
    - Déléguer la logique de transition d'état (application de trade) au simulateur.
    - Produire des snapshots.
    """

    def __init__(self, initial_cash: float):
        self.cash: float = initial_cash
        self.positions: Dict[str, Position] = {}
        self._simulator = TradeSimulator()

    def apply_trade(self, trade: Trade, price_by_symbol: Dict[str, float], maintenance_margin: float, check_margin: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Tente d'appliquer un trade au portefeuille.
        """
        result = self._simulator.simulate(
            current_cash=self.cash,
            current_positions=self.positions,
            trade=trade,
            price_by_symbol=price_by_symbol,
            maintenance_margin=maintenance_margin,
            check_margin=check_margin
        )

        if result.success:
            self.cash = result.new_cash
            self.positions = result.new_positions
            return True, None
        
        return False, result.reason

    def build_snapshot(self, price_by_symbol: Dict[str, float], timestamp: str) -> PortfolioSnapshot:
        """
        Construit un `PortfolioSnapshot` décrivant l'état courant du portefeuille.
        """
        equity = self.cash
        positions_snapshot: List[Position] = []

        for symbol, position in self.positions.items():
            current_price = price_by_symbol.get(symbol, position.entry_price)

            if position.side == PositionSide.LONG:
                market_value = current_price * position.quantity
            elif position.side == PositionSide.SHORT:
                market_value = -current_price * abs(position.quantity)
            else:
                market_value = 0.0

            equity += market_value
            positions_snapshot.append(position)

        return PortfolioSnapshot(timestamp=timestamp, cash=self.cash, equity=equity, positions=positions_snapshot)
