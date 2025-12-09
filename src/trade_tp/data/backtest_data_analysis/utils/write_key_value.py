from typing import TextIO, Any

def _write_key_value(file: TextIO, key: str, value: Any, width: int = 20) -> None:
    file.write(f"{key:<{width}} {value}\n")