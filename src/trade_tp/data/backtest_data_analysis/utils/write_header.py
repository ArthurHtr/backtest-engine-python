from typing import TextIO
from .write_line import write_line

def _write_header(file: TextIO, title: str) -> None:
    write_line(file, title)
    write_line(file, "-" * len(title))