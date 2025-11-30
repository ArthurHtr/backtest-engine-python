class Symbol:
    """
    Represents a trading symbol.
    """
    def __init__(self, symbol: str, base_asset: str, quote_asset: str, price_step: float, quantity_step: float):
        self.symbol = symbol
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.price_step = price_step
        self.quantity_step = quantity_step
