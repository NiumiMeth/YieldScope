from typing import Optional, Tuple


def compute_purchase_values(
    face_value: float,
    clean_price_pct: Optional[float] = None,
    clean_price_amount: Optional[float] = None,
    accrued_pct: Optional[float] = None,
    accrued_amount: Optional[float] = None,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Compute clean amount, accrued amount and full price (initial cost).

    Inputs can be either percentages (e.g. 89.2475) or absolute amounts. Percentages
    are interpreted as percentage of face_value (i.e. /100).

    Returns (clean_amount, accrued_amount, full_price) where values are floats or None.
    """
    if face_value is None:
        return None, None, None

    clean_amt = None
    acc_amt = None

    if clean_price_amount is not None:
        clean_amt = float(clean_price_amount)
    elif clean_price_pct is not None:
        clean_amt = float(clean_price_pct) * float(face_value) / 100.0

    if accrued_amount is not None:
        acc_amt = float(accrued_amount)
    elif accrued_pct is not None:
        acc_amt = float(accrued_pct) * float(face_value) / 100.0

    if clean_amt is None and acc_amt is None:
        return None, None, None

    # treat missing as zero for summation
    clean_amt = 0.0 if clean_amt is None else clean_amt
    acc_amt = 0.0 if acc_amt is None else acc_amt

    full = clean_amt + acc_amt
    return clean_amt, acc_amt, full
