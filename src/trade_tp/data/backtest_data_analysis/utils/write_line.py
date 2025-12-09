from typing import TextIO


def write_line(file: TextIO, text: str = "") -> None:
    """Write a line to the provided file-like object and append a newline."""
    file.write(text + "\n")
