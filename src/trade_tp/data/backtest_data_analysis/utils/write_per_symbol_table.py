from typing import TextIO, Dict, Any, List
from trade_tp.data.backtest_data_analysis.utils.write_header import _write_header
from trade_tp.data.backtest_data_analysis.utils.write_line import write_line 

def _write_per_symbol_table(file: TextIO, summary: Dict[str, Any]) -> None:
    fees_by_symbol: Dict[str, float] = summary.get("fees_by_symbol") or {}
    orders_stats: Dict[str, Dict[str, int]] = summary.get("orders_by_symbol_and_side") or {}

    if not fees_by_symbol and not orders_stats:
        return

    _write_header(file, "Per-symbol breakdown")

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