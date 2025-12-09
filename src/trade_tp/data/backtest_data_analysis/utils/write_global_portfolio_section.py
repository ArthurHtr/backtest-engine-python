from typing import TextIO, Dict, Any
from trade_tp.data.backtest_data_analysis.utils.write_header import _write_header
from trade_tp.data.backtest_data_analysis.utils.write_key_value import _write_key_value
from trade_tp.data.backtest_data_analysis.utils.write_line import write_line
from trade_tp.data.backtest_data_analysis.utils.format_money import format_money, format_pct

def _write_global_portfolio_section(file: TextIO, summary: Dict[str, Any]) -> None:
    _write_header(file, "Global Portfolio (cash / equity)")

    init_cash = summary.get("initial_cash", 0.0)
    init_eq = summary.get("initial_equity", 0.0)
    final_cash = summary.get("final_cash", 0.0)
    final_eq = summary.get("final_equity", 0.0)
    pnl_abs = summary.get("pnl_abs", final_eq - init_eq)
    if init_eq:
        pnl_pct = summary.get("pnl_pct", pnl_abs / init_eq * 100.0)
    else:
        pnl_pct = summary.get("pnl_pct", 0.0)

    _write_key_value(file, "Initial cash:", format_money(init_cash))
    _write_key_value(file, "Initial equity:", format_money(init_eq))
    _write_key_value(file, "Final cash:", format_money(final_cash))
    _write_key_value(file, "Final equity:", format_money(final_eq))
    _write_key_value(
        file,
        "PnL:",
        f"{format_money(pnl_abs)} ({format_pct(pnl_pct)})",
    )
    write_line(file)