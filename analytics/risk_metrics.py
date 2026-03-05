"""Risk metrics for bond portfolios

Contains simple DV01 and approximation helpers.
"""
def dv01_from_duration(price: float, duration: float) -> float:
	"""Approximate DV01 given price and modified duration.

	DV01 ≈ -duration * price / 10000
	"""
	return -duration * price / 10000.0

def dv01_by_shift(price_fn, shift_bp: float = 1.0) -> float:
	"""Numerical DV01 by shifting yield by `shift_bp` basis points.

	`price_fn` should accept yield (decimal) and return clean price.
	"""
	base_yield = 0.01
	shift = shift_bp / 10000.0
	p0 = price_fn(base_yield)
	p1 = price_fn(base_yield + shift)
	return p1 - p0

