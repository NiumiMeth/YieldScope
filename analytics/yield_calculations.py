"""Yield calculations for bonds

Simple YTM solver and helpers.
"""
from typing import Callable
import math
from scipy.optimize import brentq

def ytm_from_price(price: float, face_value: float, coupon_rate: float, years: float, freq: int = 2) -> float:
	"""Estimate annual YTM given clean price using root-finding.

	Returns annual YTM as a decimal (e.g. 0.05).
	"""
	coupon = face_value * coupon_rate / freq
	periods = int(round(years * freq))

	def price_from_ytm(ytm: float) -> float:
		r = ytm / freq
		pv_coupons = sum(coupon / ((1 + r) ** t) for t in range(1, periods + 1))
		pv_face = face_value / ((1 + r) ** periods)
		return pv_coupons + pv_face

	# bracket search - yields between 0% and 100% annual
	try:
		root = brentq(lambda y: price_from_ytm(y) - price, 1e-8, 3.0)
	except Exception:
		# fallback: return NaN on failure
		return float('nan')
	return root
