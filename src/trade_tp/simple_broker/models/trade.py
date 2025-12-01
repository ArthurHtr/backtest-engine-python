import uuid

class Trade:
    """
    Represents an executed trade.
    """
    def __init__(self, symbol: str, quantity: float, price: float, fee: float, timestamp: str):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.fee = fee
        self.timestamp = timestamp
        self.trade_id = str(uuid.uuid4())  # Assign a unique trade ID