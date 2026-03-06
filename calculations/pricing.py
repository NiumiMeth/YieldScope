def price_bond(coupon, y, years, par=1000, freq=1):
    c = coupon * par / freq
    n = int(years * freq)
    pv = sum([c / ((1 + y / freq) ** t) for t in range(1, n + 1)])
    pv += par / ((1 + y / freq) ** n)
    return pv
