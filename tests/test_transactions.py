import math
import pytest
from analytics.transactions import compute_trade_pl


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
