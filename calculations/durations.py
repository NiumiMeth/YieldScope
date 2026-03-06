def macaulay_duration(coupon, y, years, par=1000, freq=1):
    """Approximate Macaulay duration (years). coupon and y are decimals (e.g. 0.05)."""
    c = coupon * par / freq
    y_rate = y
    n = int(years * freq)
    if n <= 0:
        return 0.0
    pv_total = 0.0
    weighted = 0.0
    for t in range(1, n + 1):
        cf = c if t < n else c + par
        pv = cf / ((1 + y_rate / freq) ** t)
        pv_total += pv
        weighted += t * pv
    macaulay = weighted / pv_total / freq
    return round(macaulay, 4)
