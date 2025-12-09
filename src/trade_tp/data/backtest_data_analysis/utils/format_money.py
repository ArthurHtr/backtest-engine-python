from typing import Optional


def format_money(value: Optional[float]) -> str:
    """Format a number as money with 2 decimals, or 'N/A' when None."""
    if value is None:
        return "N/A"
    return f"{value:,.2f}"


def format_pct(value: Optional[float]) -> str:
    """Format a percentage value (e.g. 12.34 -> '12.34%'), or 'N/A' when None."""
    if value is None:
        return "N/A"
    return f"{value:.2f}%"
