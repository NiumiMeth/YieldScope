"""Helper utilities used around the project."""
from typing import Any

def safe_float(x: Any, default: float = 0.0) -> float:
	try:
		return float(x)
	except Exception:
		return default

def format_currency(x: float, places: int = 2) -> str:
	return f"{x:,.{places}f}"

