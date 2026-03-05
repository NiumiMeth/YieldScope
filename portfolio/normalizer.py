import pandas as pd
import re
from typing import Optional

def _parse_number(val: Optional[str]) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        try:
            if pd.isna(val):
                return None
        except Exception:
            pass
        return float(val)
    s = str(val).strip()
    if s == '':
        return None
    # remove quotes
    s = s.replace('"','')
    # remove currency tokens and commas
    s = re.sub(r'[ ,]', '', s)
    s = re.sub(r'^(LKR|Rs\.? )', '', s, flags=re.I)
    # percent
    if s.endswith('%'):
        try:
            return float(s[:-1]) / 100.0
        except Exception:
            return None
    try:
        return float(s)
    except Exception:
        return None


def normalize_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize columns and parse numeric fields for downstream processing.

    Returns a DataFrame with at least the following normalized columns:
    - ISIN, Instrument, Deal No., Initial Inv Date, Maturity Date,
      Coupon (decimal), Face (numeric), Yield (decimal), MarketValue (numeric)
    """
    df = df.copy()
    # drop completely empty rows
    df = df.dropna(how='all')

    # standardize column names
    colmap = {}
    for c in df.columns:
        cl = c.strip()
        key = cl.lower().replace('\n',' ').strip()
        colmap[c] = key
    df.columns = [colmap[c] for c in df.columns]

    # helper to get column by keyword
    def find_col(df, keywords):
        for k in keywords:
            for c in df.columns:
                if k in c:
                    return c
        return None

    isin_col = find_col(df, ['isin'])
    instr_col = find_col(df, ['instrument'])
    deal_col = find_col(df, ['deal'])
    init_col = find_col(df, ['initial inv', 'initial'])
    mat_col = find_col(df, ['matur'])
    coupon_col = find_col(df, ['coupon'])
    face_col = find_col(df, ['maturity value', 'face', 'amount', 'maturity value '])
    yield_col = find_col(df, ['yield', 'ytm'])
    # separately detect explicit YTM column if both exist in source
    ytm_col = find_col(df, ['ytm'])
    market_col = find_col(df, ['market', 'market value'])

    # build normalized frame
    out = pd.DataFrame(index=df.index)
    out['ISIN'] = df[isin_col] if isin_col else pd.Series([None] * len(df), index=df.index)
    out['Instrument'] = df[instr_col] if instr_col else pd.Series([None] * len(df), index=df.index)
    out['Deal No.'] = df[deal_col] if deal_col else pd.Series([None] * len(df), index=df.index)
    out['Initial Inv Date'] = pd.to_datetime(df[init_col]) if init_col else pd.Series([pd.NaT] * len(df), index=df.index)
    out['Maturity Date'] = pd.to_datetime(df[mat_col]) if mat_col else pd.Series([pd.NaT] * len(df), index=df.index)

    # numeric parsing (defensive)
    out['Coupon'] = df[coupon_col].apply(_parse_number) if coupon_col else pd.Series([None] * len(df), index=df.index)

    def _norm_coupon(x):
        if x is None:
            return None
        if isinstance(x, (int, float)):
            try:
                if pd.isna(x):
                    return None
            except Exception:
                pass
            return float(x/100.0) if x > 1 else float(x)
        # fallback: try to coerce
        try:
            xf = float(str(x).strip())
            return float(xf/100.0) if xf > 1 else float(xf)
        except Exception:
            return None

    out['Coupon'] = out['Coupon'].apply(_norm_coupon)
    out['Face'] = df[face_col].apply(_parse_number) if face_col else pd.Series([0.0] * len(df), index=df.index)
    out['Yield'] = df[yield_col].apply(_parse_number) if yield_col else pd.Series([None] * len(df), index=df.index)
    # preserve explicit YTM column (different from Yield) if present
    if ytm_col and ytm_col != yield_col:
        out['YTM'] = df[ytm_col].apply(_parse_number)
    out['Market value'] = df[market_col].apply(_parse_number) if market_col else pd.Series([None] * len(df), index=df.index)

    # Preserve any other original columns not yet mapped so UI can display raw fields
    mapped = {isin_col, instr_col, deal_col, init_col, mat_col, coupon_col, face_col, yield_col, market_col, ytm_col}
    for c in df.columns:
        if c not in mapped and c not in out.columns:
            out[c] = df[c]

    # drop rows without ISIN
    if 'ISIN' in out.columns:
        out = out.dropna(subset=['ISIN'])

    return out
