"""Duration and convexity calculations

Implements Macaulay and modified duration and convexity for fixed
coupon bonds.
"""
from typing import List

def macaulay_duration(cashflows: List[float], ytm: float, freq: int) -> float:
	periods = len(cashflows)
	r = ytm / freq
	pv_weights = [cf / ((1 + r) ** (t + 1)) * (t + 1) for t, cf in enumerate(cashflows)]
	pv_total = sum(cf / ((1 + r) ** (t + 1)) for t, cf in enumerate(cashflows))
	duration_periods = sum(pv_weights) / pv_total
	return duration_periods / freq

def modified_duration(macaulay: float, ytm: float) -> float:
	return macaulay / (1 + ytm)

def convexity(cashflows: List[float], ytm: float, freq: int) -> float:
	periods = len(cashflows)
	r = ytm / freq
	conv = sum(cf * (t + 1) * (t + 2) / ((1 + r) ** (t + 3)) for t, cf in enumerate(cashflows))
	pv = sum(cf / ((1 + r) ** (t + 1)) for t, cf in enumerate(cashflows))
	return conv / (pv * (freq ** 2))

