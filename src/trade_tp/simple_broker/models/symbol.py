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

    def round_price(self, price: float) -> float:
        """
        Rounds the price to the nearest valid price step.
        """
        return round(round(price / self.price_step) * self.price_step, 8)
    
    def round_quantity(self, quantity: float) -> float:
        """
        Rounds the quantity to the nearest valid quantity step.
        """
        return round(round(quantity / self.quantity_step) * self.quantity_step, 8)
