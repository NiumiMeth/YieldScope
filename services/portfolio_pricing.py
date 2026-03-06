import pandas as pd
from datetime import datetime
from typing import Dict, Optional

from calculations.bond_engine import calculate_bond_price
from calculations.purchase_values import compute_purchase_values


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    def clean_pct(x):
        if isinstance(x, str):
            return float(x.replace('%', '').replace(',', '').strip()) / 100.0
        try:
            return float(x)
        except Exception:
            return pd.NA

    def clean_num(x):
        if isinstance(x, str):
            return float(x.replace(',', '').strip())
        try:
            return float(x)
        except Exception:
            return pd.NA

    if 'Coupon' in df.columns:
        df['Coupon'] = df['Coupon'].apply(clean_pct)
    # normalize maturity value header
    if 'Maturity Value' in df.columns:
        df['Maturity Value'] = df['Maturity Value'].apply(clean_num)
    elif 'Maturity Value ' in df.columns:
        df['Maturity Value'] = df['Maturity Value '].apply(clean_num)

    if 'Market value' in df.columns:
        df['Market value'] = df['Market value'].apply(clean_num)

    # yield may be numeric already
    if 'Yield' in df.columns:
        df['Yield'] = pd.to_numeric(df['Yield'], errors='coerce')

    # keep clean price / accrued if present
    return df


def aggregate_by_isin(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate rows by ISIN producing one row per ISIN with summed face and first-known fields."""
    df = _clean_columns(df)

    # require ISIN
    if 'ISIN' not in df.columns:
        raise ValueError('Uploaded data must contain ISIN column')

    agg = df.groupby('ISIN').agg(
        Instrument=('Instrument', 'first'),
        Coupon=('Coupon', 'first'),
        Maturity_Date=('Maturity Date', 'first'),
        Face_Value=('Maturity Value', 'sum'),
        Current_Yield=('Yield', 'first'),
        Market_Value=('Market value', 'first'),
    )

    # ensure types
    agg = agg.reset_index()
    return agg


def compute_initial_cost_for_row(row: pd.Series) -> Optional[float]:
    """Compute initial cost for a single aggregated row.

    Priority:
      1) If `Initial Cost` column present -> use it (first per ISIN expected)
      2) If `Clean Price` / `Accrued` exist in row (as percent or amounts) -> compute
      3) else -> return None
    """
    # direct column
    if 'Initial Cost' in row.index and pd.notna(row['Initial Cost']):
        return float(row['Initial Cost'])

    face = row.get('Face_Value')
    if pd.isna(face):
        return None

    # detect clean price or accrued in the original row if present (allow multiple possible names)
    cp = None
    ac = None
    for k in row.index:
        lk = k.lower()
        if 'clean' in lk and 'price' in lk:
            cp = row[k]
        if 'acc' in lk or 'accrued' in lk or 'acc.int' in lk:
            ac = row[k]

    # try to compute
    if pd.notna(cp) or pd.notna(ac):
        # CP/AC may be percent or amount; pass both possibilities
        clean_pct = None
        clean_amt = None
        acc_pct = None
        acc_amt = None

        if isinstance(cp, str) and '%' in cp:
            try:
                clean_pct = float(cp.replace('%', '').replace(',', '').strip())
            except Exception:
                pass
        elif pd.notna(cp):
            try:
                clean_amt = float(str(cp).replace(',', '').strip())
            except Exception:
                pass

        if isinstance(ac, str) and '%' in ac:
            try:
                acc_pct = float(ac.replace('%', '').replace(',', '').strip())
            except Exception:
                pass
        elif pd.notna(ac):
            try:
                acc_amt = float(str(ac).replace(',', '').strip())
            except Exception:
                pass

        c_amt, a_amt, full = compute_purchase_values(
            face_value=face,
            clean_price_pct=clean_pct,
            clean_price_amount=clean_amt,
            accrued_pct=acc_pct,
            accrued_amount=acc_amt,
        )
        return full

    return None


def compute_portfolio_initial_cost(df: pd.DataFrame) -> pd.DataFrame:
    """Return aggregated ISIN dataframe with `Initial_Cost` column computed where possible."""
    agg = aggregate_by_isin(df)

    # try to pull Initial Cost from original rows per ISIN first
    # if original DF has `Initial Cost` use first value per ISIN
    if 'Initial Cost' in df.columns:
        ic = df.dropna(subset=['Initial Cost']).groupby('ISIN')['Initial Cost'].first()
        agg = agg.merge(ic.rename('Initial_Cost'), left_on='ISIN', right_index=True, how='left')
    else:
        agg['Initial_Cost'] = pd.NA

    # compute per row where missing
    for i, row in agg.iterrows():
        if pd.isna(row['Initial_Cost']):
            # try compute using any clean/acc columns in original df grouped by ISIN
            original_rows = df[df['ISIN'] == row['ISIN']].iloc[0]
            # merge original row fields into series for compute
            merged = pd.concat([row, original_rows])
            icost = compute_initial_cost_for_row(merged)
            if icost is not None:
                agg.at[i, 'Initial_Cost'] = icost

    return agg


def price_by_yield(face_value: float, coupon: float, ytm: float, maturity_date: datetime, spot_date: datetime) -> float:
    years = max((maturity_date - spot_date).days / 365.0, 0.0)
    # bond_engine.calculate_bond_price expects coupon_rate decimal and ytm decimal
    return calculate_bond_price(face_value, coupon, ytm, years_to_maturity=years)


def compute_pnl(agg_df: pd.DataFrame, spot_date: Optional[datetime] = None, new_yield_map: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    """Given aggregated ISIN dataframe, compute new market value at yields provided and P/L vs Initial_Cost.

    `new_yield_map` maps ISIN -> yield in percent (e.g., 12.5 means 12.5%). If an ISIN is missing, uses Current_Yield.
    Returns a dataframe with columns: ISIN, Face_Value, Initial_Cost, Old_Market_Value, New_Market_Value, PnL
    """
    if spot_date is None:
        spot_date = datetime.today()

    rows = []
    for _, r in agg_df.iterrows():
        isin = r['ISIN']
        face = float(r['Face_Value']) if pd.notna(r['Face_Value']) else 0.0
        coupon = float(r['Coupon']) if pd.notna(r['Coupon']) else 0.0
        mat = r['Maturity_Date']
        try:
            mat_dt = pd.to_datetime(mat, errors='coerce')
            if pd.isna(mat_dt):
                mat_dt = spot_date
            else:
                mat_dt = mat_dt.to_pydatetime()
        except Exception:
            mat_dt = spot_date

        old_yield = float(r['Current_Yield'])/100.0 if pd.notna(r.get('Current_Yield')) else None
        # new yield - accept percent (e.g., 12.5) in map
        new_y = None
        if new_yield_map and isin in new_yield_map:
            new_y = float(new_yield_map[isin]) / 100.0
        elif old_yield is not None:
            new_y = old_yield
        else:
            new_y = 0.0

        # compute new market value at new_y
        new_market = price_by_yield(face, coupon, new_y, mat_dt, spot_date)

        old_market = float(r['Market_Value']) if pd.notna(r.get('Market_Value')) else None
        initial = float(r['Initial_Cost']) if pd.notna(r.get('Initial_Cost')) else None

        pnl = None
        if initial is not None:
            pnl = new_market - initial
        elif old_market is not None:
            pnl = new_market - old_market

        rows.append({
            'ISIN': isin,
            'Instrument': r.get('Instrument'),
            'Face_Value': face,
            'Initial_Cost': initial,
            'Old_Market_Value': old_market,
            'New_Market_Value': new_market,
            'PnL': pnl,
        })

    return pd.DataFrame(rows)
