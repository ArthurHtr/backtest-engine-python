from trade_tp.backtest_engine.entities.enums import Side

from dataclasses import dataclass
from typing import Optional
from trade_tp.backtest_engine.entities.enums import Side

@dataclass(frozen=True)
class OrderIntent:
    """
    Représente une intention d'ordre provenant de la stratégie.
    Immuable.

    Un OrderIntent décrit ce que la stratégie veut faire — il doit être validé
    par le broker avant d'être transformé en `Trade` exécuté.

    Attributes
    - symbol (str): symbole cible
    - side (Side): BUY ou SELL
    - quantity (float): quantité demandée (toujours positive dans l'API de la stratégie)
    - order_type (str): type d'ordre, ex. 'MARKET' (autres types non implémentés)
    - limit_price (float|None): prix limite si applicable
    - order_id (str|None): identifiant optionnel fourni par la stratégie

    Conventions
    - La stratégie passe une quantité positive; le broker décidera du signe
        (BUY -> qty positif, SELL -> qty positif converti en trade.quantity négatif).
    """
    symbol: str
    side: Side
    quantity: float
    order_type: str = "MARKET"
    limit_price: Optional[float] = None
    order_id: Optional[str] = None
