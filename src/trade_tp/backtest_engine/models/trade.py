class Trade:
    """
    Représente un trade effectivement exécuté par le broker.

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

    def __init__(self, symbol: str, quantity: float, price: float, fee: float, timestamp: str, trade_id: str = None):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.fee = fee
        self.timestamp = timestamp
        self.trade_id = trade_id