from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Trade:
    """
    Représente un trade effectivement exécuté par le broker.
    Immuable.

    Attributes
    - symbol (str): symbole tradé
    - quantity (float): quantité tradée (BUY > 0, SELL < 0 selon conventions internes)
    - price (float): prix d'exécution
    - fee (float): frais facturés pour ce trade (devrait être >= 0)
    - timestamp (str): horodatage d'exécution
    - trade_id (str|None): identifiant optionnel du trade (peut être None)

    Note: la création d'un Trade n'implique pas qu'il ait déjà été appliqué au portefeuille;
    c'est un objet de transport utilisé entre le broker et l'état du portefeuille.
    """
    symbol: str
    quantity: float
    price: float
    fee: float
    timestamp: str
    trade_id: Optional[str] = None