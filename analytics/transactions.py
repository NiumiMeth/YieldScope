"""Transaction-level helpers: parsing Excel-exported CSVs and P/L math.

Provides pragmatic implementations of PRICE, ACCRINT, funding cost and
trade P/L useful for validating CSV-based calculator outputs.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import List
import pandas as pd


def _coupon_interval_months(freq: int) -> int:
    return int(12 / freq)


def coupon_schedule(maturity: str | datetime, freq: int = 2) -> List[pd.Timestamp]:
    m = pd.to_datetime(maturity)
    months = _coupon_interval_months(freq)
    dates = [m]
    # build backward until far in past (safety limit 200 years)
    for _ in range(0, 200 * freq):
        prev = dates[-1] - pd.DateOffset(months=months)
        dates.append(prev)
        if prev.year < (m.year - 200):
            break
    return sorted(dates)


def last_next_coupon(settlement: str | datetime, maturity: str | datetime, freq: int = 2):
    settlement = pd.to_datetime(settlement)
    schedule = coupon_schedule(maturity, freq)
    prev = None
    nxt = None
    for d in schedule:
        if d <= settlement:
            prev = d
        elif d > settlement and nxt is None:
            nxt = d
    if prev is None:
        # assume first coupon is before settlement
        prev = schedule[0]
    if nxt is None:
        nxt = pd.to_datetime(maturity)
    return pd.to_datetime(prev), pd.to_datetime(nxt)


def accrint(settlement: str | datetime, maturity: str | datetime, coupon_rate: float, face: float = 100.0, freq: int = 2) -> float:
    last, nxt = last_next_coupon(settlement, maturity, freq)
    coupon = face * coupon_rate / freq
    days_elapsed = (pd.to_datetime(settlement) - last).days
    period_days = (nxt - last).days if (nxt - last).days > 0 else 1
    fraction = days_elapsed / period_days
    return coupon * fraction


def price_from_yield(settlement: str | datetime, maturity: str | datetime, coupon_rate: float, yld: float, face: float = 100.0, freq: int = 2) -> float:
    """Return clean price as percent of face (e.g. 89.2475)."""
    settlement = pd.to_datetime(settlement)
    schedule = [d for d in coupon_schedule(maturity, freq) if d > settlement]
    if not schedule:
        return 0.0
    coupon = face * coupon_rate / freq
    pv = 0.0
    for d in schedule:
        t = (d - settlement).days / 365.0
        cf = coupon
        if d == pd.to_datetime(maturity):
            cf += face
        pv += cf / ((1 + yld) ** t)
    return pv / face * 100.0


def full_price_from_clean(clean_price_percent: float, accrued_interest: float, face: float = 100.0) -> float:
    return (clean_price_percent + (accrued_interest / face * 100.0)) / 100.0 * face


def funding_cost_over_period(balance: float, funding_rate: float, days: int) -> float:
    return balance * funding_rate * (days / 365.0)


def coupons_between(purchase_date: str | datetime, sell_date: str | datetime, maturity: str | datetime, coupon_rate: float, face: float = 100.0, freq: int = 2) -> float:
    purchase = pd.to_datetime(purchase_date)
    sell = pd.to_datetime(sell_date)
    schedule = [d for d in coupon_schedule(maturity, freq) if purchase < d <= sell]
    coupon = face * coupon_rate / freq
    return coupon * len(schedule)


def compute_trade_pl(purchase: dict, sale: dict, funding_rate: float) -> dict:
    """Compute P/L components for a single trade.

    purchase and sale dicts require keys:
        - date (str or datetime)
        - maturity (str or datetime)
        - coupon_rate (decimal, e.g. 0.1075)
        - face (float)
        - yield (annual decimal)

    Returns dict with purchase_full_price, sales_full_price, coupons_received, total_funding_cost, total_pl
    """
    pur_date = pd.to_datetime(purchase['date'])
    sell_date = pd.to_datetime(sale['date'])
    maturity = purchase.get('maturity', sale.get('maturity'))
    coupon_rate = purchase['coupon_rate']
    face = purchase.get('face', 100.0)

    pur_clean = price_from_yield(pur_date, maturity, coupon_rate, purchase['yield'], face=face, freq=purchase.get('freq', 2))
    pur_ai = accrint(pur_date, maturity, coupon_rate, face=face, freq=purchase.get('freq', 2))
    pur_full = full_price_from_clean(pur_clean, pur_ai, face=face)

    sell_clean = price_from_yield(sell_date, maturity, coupon_rate, sale['yield'], face=face, freq=sale.get('freq', 2))
    sell_ai = accrint(sell_date, maturity, coupon_rate, face=face, freq=sale.get('freq', 2))
    sell_full = full_price_from_clean(sell_clean, sell_ai, face=face)

    coupons_recv = coupons_between(pur_date, sell_date, maturity, coupon_rate, face=face, freq=purchase.get('freq', 2))

    # funding cost: approximate by applying funding_rate to running balance
    balance = pur_full
    total_funding = 0.0
    # iterate coupon dates and compute funding for each interval
    schedule = [d for d in coupon_schedule(maturity, purchase.get('freq', 2)) if d > pur_date and d <= sell_date]
    prev = pur_date
    for d in schedule:
        days = (d - prev).days
        total_funding += funding_cost_over_period(balance, funding_rate, days)
        # reduce balance when coupon received
        balance -= (face * coupon_rate / purchase.get('freq', 2))
        prev = d
    # final interval to sell_date
    days = (sell_date - prev).days
    if days > 0:
        total_funding += funding_cost_over_period(balance, funding_rate, days)

    total_pl = (sell_full + coupons_recv) - (pur_full + total_funding)

    return {
        'purchase_full_price': pur_full,
        'purchase_clean': pur_clean,
        'purchase_accrued': pur_ai,
        'sales_full_price': sell_full,
        'sales_clean': sell_clean,
        'sales_accrued': sell_ai,
        'coupons_received': coupons_recv,
        'total_funding_cost': total_funding,
        'total_pl': total_pl,
    }


if __name__ == '__main__':
    # Small example using the numbers from the user's notes
    purchase = {
        'date': '2024-01-16',
        'maturity': '2028-03-15',
        'coupon_rate': 0.1075,
        'face': 1000000000,
        'yield': 0.1425,
        'freq': 2,
    }
    sale = {
        'date': '2024-10-23',
        'maturity': '2028-03-15',
        'coupon_rate': 0.1075,
        'face': 1000000000,
        'yield': 0.1165,
        'freq': 2,
    }
    res = compute_trade_pl(purchase, sale, funding_rate=0.09)
    print(res)
