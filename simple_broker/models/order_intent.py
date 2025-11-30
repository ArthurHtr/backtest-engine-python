from simple_broker.models.enums import Side
import uuid

class OrderIntent:
    """
    Represents an order intent from the strategy.
    """
    def __init__(self, symbol: str, side: Side, quantity: float, order_type: str = "MARKET", limit_price: float = None):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.limit_price = limit_price
        self.order_id = str(uuid.uuid4())  # Assign a unique order ID
