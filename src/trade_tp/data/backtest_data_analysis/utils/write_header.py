from typing import TextIO
from trade_tp.data.backtest_data_analysis.utils.write_line import write_line

def _write_header(file: TextIO, title: str) -> None:
    write_line(file, title)
    write_line(file, "-" * len(title))