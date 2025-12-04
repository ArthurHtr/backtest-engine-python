"""
Enums used by the simple broker models.

Side: BUY / SELL for order intents.
PositionSide: LONG / SHORT for stored positions.
"""

from enum import Enum


class Side(Enum):
    """Order side used by `OrderIntent` (BUY or SELL)."""
    BUY = "BUY"
    SELL = "SELL"


class PositionSide(Enum):
    """Sign of a stored position: LONG or SHORT."""
    LONG = "LONG"
    SHORT = "SHORT"
