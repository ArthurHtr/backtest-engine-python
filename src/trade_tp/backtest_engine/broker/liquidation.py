from typing import Dict, List

from trade_tp.backtest_engine.entities.enums import PositionSide
from trade_tp.backtest_engine.entities.candle import Candle
from trade_tp.backtest_engine.entities.trade import Trade
from trade_tp.backtest_engine.portfolio import Portfolio

class LiquidationManager:
    """
    Gère la vérification des appels de marge et la liquidation des positions.
    """

    def __init__(self, portfolio: Portfolio, maintenance_margin: float, fee_rate: float):
        self.portfolio = portfolio
        self.maintenance_margin = maintenance_margin
        self.fee_rate = fee_rate

    def _compute_equity(self, price_by_symbol: Dict[str, float]) -> float:
        """Calcule l'equity du portefeuille pour des prix donnés."""
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

    def check_margin_call(self, candles: Dict[str, Candle], price_by_symbol: Dict[str, float], timestamp: str) -> List[Dict]:
        """
        Vérifie si la marge de maintenance est respectée pour les positions short existantes.
        Si ce n'est pas le cas, génère des trades de liquidation.
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
