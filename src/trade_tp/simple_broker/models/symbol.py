class Symbol:
    """
    Métadonnées décrivant un instrument tradable.

    Attributes
    - symbol (str): identifiant du symbole, ex. 'BTCUSD' ou 'AAPL'
    - base_asset (str): actif de base (ex: 'BTC')
    - quote_asset (str): actif de cotation (ex: 'USD')
    - price_step (float): granularité minimale du prix
    - quantity_step (float): granularité minimale de la quantité

    Ces informations servent notamment à valider/arrondir les ordres selon les
    règles du marché simulé.
    """

    def __init__(self, symbol: str, base_asset: str, quote_asset: str, price_step: float, quantity_step: float):
        self.symbol = symbol
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.price_step = price_step
        self.quantity_step = quantity_step