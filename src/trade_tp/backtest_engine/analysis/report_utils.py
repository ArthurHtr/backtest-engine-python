from typing import TextIO, Any, Optional, Dict, List

def write_line(file: TextIO, text: str = "") -> None:
    """Write a line to the provided file-like object and append a newline."""
    file.write(text + "\n")

def write_header(file: TextIO, title: str) -> None:
    write_line(file, title)
    write_line(file, "-" * len(title))

def write_key_value(file: TextIO, key: str, value: Any, width: int = 20) -> None:
    file.write(f"{key:<{width}} {value}\n")

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

def write_summary_header(file: TextIO, summary: Dict[str, Any]) -> None:
    write_header(file, "Backtest Summary")

    run_id = summary.get("run_id")
    if run_id:
        write_key_value(file, "Run ID:", run_id)

    symbols = summary.get("symbols") or []
    if symbols:
        write_key_value(file, "Symbols:", ", ".join(symbols))

    write_key_value(
        file,
        "Period:",
        f"{summary.get('start')} → {summary.get('end')}",
    )
    write_key_value(file, "Timeframe:", summary.get("timeframe"))
    write_key_value(file, "Strategy:", summary.get("strategy"))
    write_line(file)

def write_global_portfolio_section(file: TextIO, summary: Dict[str, Any]) -> None:
    write_header(file, "Global Portfolio (cash / equity)")

    init_cash = summary.get("initial_cash", 0.0)
    init_eq = summary.get("initial_equity", 0.0)
    final_cash = summary.get("final_cash", 0.0)
    final_eq = summary.get("final_equity", 0.0)
    pnl_abs = summary.get("pnl_abs", final_eq - init_eq)
    if init_eq:
        pnl_pct = summary.get("pnl_pct", pnl_abs / init_eq * 100.0)
    else:
        pnl_pct = summary.get("pnl_pct", 0.0)

    write_key_value(file, "Initial cash:", format_money(init_cash))
    write_key_value(file, "Initial equity:", format_money(init_eq))
    write_key_value(file, "Final cash:", format_money(final_cash))
    write_key_value(file, "Final equity:", format_money(final_eq))
    write_key_value(
        file,
        "PnL:",
        f"{format_money(pnl_abs)} ({format_pct(pnl_pct)})",
    )
    write_line(file)

def write_per_symbol_table(file: TextIO, summary: Dict[str, Any]) -> None:
    fees_by_symbol: Dict[str, float] = summary.get("fees_by_symbol") or {}
    orders_stats: Dict[str, Dict[str, int]] = summary.get("orders_by_symbol_and_side") or {}

    if not fees_by_symbol and not orders_stats:
        return

    write_header(file, "Per-symbol breakdown")

    symbols_set = set(fees_by_symbol.keys()) | set(orders_stats.keys())
    symbols = sorted(symbols_set)

    all_sides = sorted(
        {
            side
            for sides in orders_stats.values()
            for side in sides.keys()
            if side != "TOTAL"
        }
    )

    header_cols = ["Symbol", "#Orders"] + all_sides + ["Fees"]
    rows: List[List[str]] = []

    for sym in symbols:
        sides = orders_stats.get(sym, {})
        total_orders = sides.get(
            "TOTAL",
            sum(v for k, v in sides.items() if k != "TOTAL"),
        )
        side_counts = [str(sides.get(side, 0)) for side in all_sides]
        fee_str = f"{fees_by_symbol.get(sym, 0.0):,.4f}"
        row = [sym, str(total_orders), *side_counts, fee_str]
        rows.append(row)

    col_widths: List[int] = []
    for col_idx in range(len(header_cols)):
        max_len_header = len(header_cols[col_idx])
        max_len_rows = max(len(row[col_idx]) for row in rows) if rows else 0
        col_widths.append(max(max_len_header, max_len_rows))

    def format_row(cols: List[str]) -> str:
        return "  " + "  ".join(
            f"{col:<{col_widths[idx]}}" for idx, col in enumerate(cols)
        )

    write_line(file, format_row(header_cols))
    write_line(file, "  " + "  ".join("-" * w for w in col_widths))

    for row in rows:
        write_line(file, format_row(row))

    write_line(file)
