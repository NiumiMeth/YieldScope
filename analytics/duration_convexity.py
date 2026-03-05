"""Duration and convexity calculations

Implements Macaulay and modified duration and convexity for fixed
coupon bonds.
"""
from typing import List

def macaulay_duration(cashflows: List[float], ytm: float, freq: int) -> float:
	"""Compute Macaulay duration in years using `ytm` as annual effective.

	Converts `ytm` to a periodic rate r where (1+r)**freq = 1+ytm,
	computes duration in periods and returns years.
	"""
	periods = len(cashflows)
	r = (1 + ytm) ** (1 / freq) - 1
	pv_weights = [cf / ((1 + r) ** (t + 1)) * (t + 1) for t, cf in enumerate(cashflows)]
	pv_total = sum(cf / ((1 + r) ** (t + 1)) for t, cf in enumerate(cashflows))
	duration_periods = sum(pv_weights) / pv_total
	return duration_periods / freq

def modified_duration(macaulay: float, ytm: float, freq: int) -> float:
	"""Modified duration using periodic compounding. Expects `ytm` annual effective."""
	r = (1 + ytm) ** (1 / freq) - 1
	return macaulay / (1 + r)

def convexity(cashflows: List[float], ytm: float, freq: int) -> float:
	"""Return convexity in years using `ytm` as annual effective."""
	periods = len(cashflows)
	r = (1 + ytm) ** (1 / freq) - 1
	conv = sum(cf * (t + 1) * (t + 2) / ((1 + r) ** (t + 3)) for t, cf in enumerate(cashflows))
	pv = sum(cf / ((1 + r) ** (t + 1)) for t, cf in enumerate(cashflows))
	return conv / (pv * (freq ** 2))

