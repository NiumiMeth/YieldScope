"""Bond pricing analytics functions

Provides a small set of helpers to compute clean price for fixed
coupon bonds.
"""
from typing import List

def price_clean(face_value: float, coupon_rate: float, ytm: float, years: float, freq: int = 2) -> float:
	"""Calculate the clean price of a fixed-rate bond.

	Args:
		face_value: Face/par value of the bond.
		coupon_rate: Annual coupon rate (e.g. 0.05 for 5%).
		ytm: Annual yield to maturity (decimal).
		years: Years to maturity.
		freq: Coupons per year (default semi-annual = 2).

	Returns:
		Clean price (present value excluding accrued interest).
	"""
	periods = int(round(years * freq))
	coupon = face_value * coupon_rate / freq
	discount_rate = ytm / freq
	pv_coupons = sum(coupon / ((1 + discount_rate) ** t) for t in range(1, periods + 1))
	pv_face = face_value / ((1 + discount_rate) ** periods)
	return pv_coupons + pv_face

def cashflows(face_value: float, coupon_rate: float, years: float, freq: int = 2) -> List[float]:
	"""Return list of cash flows (coupons and redemption)."""
	periods = int(round(years * freq))
	coupon = face_value * coupon_rate / freq
	flows = [coupon] * periods
	flows[-1] += face_value
	return flows
