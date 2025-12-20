from typing import Any, Dict, List, Optional
from trade_tp.remote.client import TradeTpClient
from trade_tp.backtest_engine.entities.candle import Candle
from trade_tp.backtest_engine.entities.portfolio_snapshot import PortfolioSnapshot
from trade_tp.backtest_engine.entities.position import Position
from trade_tp.backtest_engine.entities.order_intent import OrderIntent
from trade_tp.backtest_engine.entities.enums import Side, PositionSide
from trade_tp.backtest_engine.entities.trade import Trade

class ResultExporter:
    """Envoie directement les `candles_logs` (brut) vers l'API distante.

    Le serveur recevra le payload brut `{run_id, params, candles_logs}` et
    pourra effectuer son propre post-traitement/stockage.
    """

    def __init__(self, client: TradeTpClient):
        self.client = client

    def _serialize(self, obj: Any) -> Any:
        """Helper to serialize custom objects to JSON-compatible types."""
        if isinstance(obj, Candle):
            return {
                "symbol": obj.symbol,
                "timestamp": obj.timestamp,
                "open": obj.open,
                "high": obj.high,
                "low": obj.low,
                "close": obj.close,
                "volume": obj.volume
            }
        elif isinstance(obj, PortfolioSnapshot):
            # Handle positions whether it's a list or dict (just in case)
            positions_data = []
            if isinstance(obj.positions, dict):
                positions_data = [self._serialize(p) for p in obj.positions.values()]
            elif isinstance(obj.positions, list):
                positions_data = [self._serialize(p) for p in obj.positions]
            
            return {
                "timestamp": obj.timestamp,
                "cash": obj.cash,
                "equity": obj.equity,
                "positions": positions_data
            }
        elif isinstance(obj, Position):
            return {
                "symbol": obj.symbol,
                "side": obj.side.value if hasattr(obj.side, 'value') else str(obj.side),
                "quantity": obj.quantity,
                "entry_price": obj.entry_price
            }
        elif isinstance(obj, OrderIntent):
            return {
                "symbol": obj.symbol,
                "side": obj.side.value if hasattr(obj.side, 'value') else str(obj.side),
                "quantity": obj.quantity,
                "order_type": obj.order_type,
                "limit_price": obj.limit_price,
                "order_id": obj.order_id
            }
        elif isinstance(obj, Trade):
            return {
                "symbol": obj.symbol,
                "quantity": obj.quantity,
                "price": obj.price,
                "fee": obj.fee,
                "timestamp": obj.timestamp,
                "trade_id": obj.trade_id
            }
        elif isinstance(obj, (Side, PositionSide)):
            return obj.value
        elif isinstance(obj, list):
            return [self._serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        else:
            return obj

    def export(self, run_id: Optional[str], params: Dict[str, Any], candles_logs: List[dict]) -> Dict[str, Any]:
        """Envoie le payload complet contenant `candles_logs`.
        """
        # Serialize candles_logs to ensure all custom objects are converted to dicts
        serialized_logs = self._serialize(candles_logs)

        payload = {
            "run_id": run_id,
            "params": params,
            "candles_logs": serialized_logs,
        }
        if not run_id:
             raise ValueError("run_id is required for remote export")
             
        return self.client.post_results(run_id, payload)
