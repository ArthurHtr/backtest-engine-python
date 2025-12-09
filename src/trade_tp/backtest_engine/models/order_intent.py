from trade_tp.backtest_engine.models.enums import Side

class OrderIntent:
        """
        Représente une intention d'ordre provenant de la stratégie.

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

        def __init__(self, symbol: str, side: Side, quantity: float, order_type: str = "MARKET", limit_price: float = None, order_id: str = None):
                self.symbol = symbol
                self.side = side
                self.quantity = quantity
                self.order_type = order_type
                self.limit_price = limit_price
                self.order_id = order_id
