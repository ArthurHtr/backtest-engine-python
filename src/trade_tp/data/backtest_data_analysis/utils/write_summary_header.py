from typing import TextIO, Dict, Any
from trade_tp.data.backtest_data_analysis.utils.write_header import _write_header
from trade_tp.data.backtest_data_analysis.utils.write_key_value import _write_key_value
from trade_tp.data.backtest_data_analysis.utils.write_line import write_line

def _write_summary_header(file: TextIO, summary: Dict[str, Any]) -> None:
    _write_header(file, "Backtest Summary")

    run_id = summary.get("run_id")
    if run_id:
        _write_key_value(file, "Run ID:", run_id)

    symbols = summary.get("symbols") or []
    if symbols:
        _write_key_value(file, "Symbols:", ", ".join(symbols))

    _write_key_value(
        file,
        "Period:",
        f"{summary.get('start')} → {summary.get('end')}",
    )
    _write_key_value(file, "Timeframe:", summary.get("timeframe"))
    _write_key_value(file, "Strategy:", summary.get("strategy"))
    write_line(file)