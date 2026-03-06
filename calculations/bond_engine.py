import numpy as np


def calculate_bond_price(face_value, coupon_rate, ytm, years_to_maturity, freq=2):
    """Calculates the Dirty Price of a bond."""
    periods = years_to_maturity * freq
    coupon = (coupon_rate * face_value) / freq
    rate_per_period = ytm / freq

    # Present Value of Coupons + Present Value of Face Value
    price = sum([coupon / (1 + rate_per_period) ** i for i in range(1, int(periods) + 1)])
    price += face_value / (1 + rate_per_period) ** periods
    return price


def calculate_metrics(face_value, coupon_rate, ytm, years_to_maturity):
    """Returns a dictionary of key risk metrics."""
    price = calculate_bond_price(face_value, coupon_rate, ytm, years_to_maturity)
    # Simplified Duration for the UI (placeholder)
    duration = (years_to_maturity * 0.9)
    mod_duration = duration / (1 + ytm)
    return {
        "market_value": price,
        "duration": duration,
        "mod_duration": mod_duration,
        "annual_income": face_value * coupon_rate,
    }
