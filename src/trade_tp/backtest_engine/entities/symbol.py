from dataclasses import dataclass

@dataclass(frozen=True)
class Symbol:
    """
    Métadonnées décrivant un instrument tradable.
    Immuable.

    Attributes
    - symbol (str): identifiant du symbole, ex. 'BTCUSD' ou 'AAPL'
    - base_asset (str): actif de base (ex: 'BTC')
    - quote_asset (str): actif de cotation (ex: 'USD')
    - price_step (float): granularité minimale du prix
    - quantity_step (float): granularité minimale de la quantité
    - min_quantity (float): quantité minimale autorisée

    Ces informations servent notamment à valider/arrondir les ordres selon les
    règles du marché simulé.
    """
    symbol: str
    base_asset: str
    quote_asset: str
    price_step: float
    quantity_step: float
    min_quantity: float = 0.0

    def round_price(self, price: float) -> float:
        """Arrondit le prix au multiple de price_step le plus proche."""
        if self.price_step <= 0:
            return price
        
        steps = round(price / self.price_step)
        
        return steps * self.price_step

    def round_quantity(self, quantity: float) -> float:
        """Arrondit la quantité au multiple de quantity_step le plus proche."""
        if self.quantity_step <= 0:
            return quantity
        
        steps = int(quantity / self.quantity_step)
        rounded = steps * self.quantity_step

        return rounded if rounded >= self.min_quantity else 0.0
