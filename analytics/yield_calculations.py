"""Yield calculations for bonds

Simple YTM solver and helpers.
"""
from typing import Callable
import math
from scipy.optimize import brentq


def ytm_from_price(price: float, face_value: float, coupon_rate: float, years: float, freq: int = 2) -> float:
	"""Estimate annual YTM (annual effective) given clean price.

	The solver finds the periodic rate r (per coupon period) such that
	PV(cashflows discounted by r) == price. It returns the annualized
	effective YTM as (1 + r)**freq - 1.
	"""
	coupon = face_value * coupon_rate / freq
	periods = int(round(years * freq))

	def price_from_r(r: float) -> float:
		pv_coupons = sum(coupon / ((1 + r) ** t) for t in range(1, periods + 1))
		pv_face = face_value / ((1 + r) ** periods)
		return pv_coupons + pv_face

	# bracket search on periodic rate r (per half-year for freq=2)
	try:
		root_r = brentq(lambda r: price_from_r(r) - price, 1e-12, 1.0)
	except Exception:
		return float('nan')

	# annualize: annual_effective = (1 + r)**freq - 1
	return (1 + root_r) ** freq - 1
