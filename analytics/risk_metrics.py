"""Risk metrics for bond portfolios

Contains simple DV01 and approximation helpers.
"""
def dv01_from_modified(price: float, mod_duration: float) -> float:
	"""Approximate DV01 given price and modified duration.

	DV01 ≈ -modified_duration * price / 10000
	Returns change in price for 1 basis point move.
	"""
	return -mod_duration * price / 10000.0


def dv01_by_shift(price_fn, ytm_annual: float, shift_bp: float = 1.0, freq: int = 2) -> float:
	"""Numerical DV01 by shifting yield by `shift_bp` basis points.

	- `price_fn` should accept an annual effective YTM and return clean price.
	- `shift_bp` is in basis points (1 bp = 0.0001 as annual effective change in periodic rate approximation).
	The function shifts the periodic rate by `shift_bp/10000` and annualizes appropriately.
	"""
	# convert annual effective to periodic r
	r = (1 + ytm_annual) ** (1 / freq) - 1
	shift = shift_bp / 10000.0
	# shift periodic rate
	p0 = price_fn(ytm_annual)
	# build new annual effective from shifted periodic
	r_shifted = r + shift
	ytm_shifted = (1 + r_shifted) ** freq - 1
	p1 = price_fn(ytm_shifted)
	return p1 - p0

