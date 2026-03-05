import math
import pytest
import datetime
from analytics.transactions import compute_trade_pl, accrint, price_from_yield, last_next_coupon


def test_compute_trade_pl_example():
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
    # Basic sanity checks
    assert 'total_pl' in res
    assert isinstance(res['total_pl'], float)
    # total_pl should be finite
    assert math.isfinite(res['total_pl'])


def test_accrint_uses_182_days():
    # settlement 91 days after last coupon should give ~half of semiannual coupon
    maturity = '2026-04-01'
    coupon_rate = 0.12
    face = 1000000
    # find last coupon date and add 91 days
    last, nxt = last_next_coupon('2024-01-01', maturity, freq=2)
    settlement = (last + datetime.timedelta(days=91)).strftime('%Y-%m-%d')
    ai = accrint(settlement, maturity, coupon_rate, face=face, freq=2)
    expected_coupon = face * coupon_rate / 2
    # 91/182 -> ~half of semiannual coupon
    assert pytest.approx(ai, rel=1e-3) == expected_coupon * (91 / 182)


def test_price_from_yield_semiannual():
    # simple sanity: a zero-coupon-like bond (coupon_rate=0) priced with yld should match formula
    settlement = '2024-01-01'
    maturity = '2026-01-01'
    coupon_rate = 0.0
    face = 1000
    yld = 0.10  # 10% nominal annual semiannual compounding
    price = price_from_yield(settlement, maturity, coupon_rate, yld, face=face, freq=2)
    # periods = 4 half-years; PV = 1000/(1+0.05)^4
    expected = 1000 / ((1 + 0.05) ** 4) / face * 100 * face / face
    assert price == pytest.approx(expected, rel=1e-6)
