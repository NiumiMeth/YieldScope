import pandas as pd


def normalize_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # normalize column names
    df.columns = [c.strip() for c in df.columns]

    # drop subtotal rows where ISIN missing
    if 'ISIN' in df.columns:
        df = df.dropna(subset=['ISIN']).copy()

    # helpers
    def clean_pct(x):
        if isinstance(x, str):
            return float(x.replace('%', '').replace(',', '').strip()) / 100
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
    if 'Maturity Value' in df.columns:
        df['Maturity Value'] = df['Maturity Value'].apply(clean_num)
    elif 'Maturity Value ' in df.columns:
        df['Maturity Value'] = df['Maturity Value '].apply(clean_num)
    if 'Market value' in df.columns:
        df['Market value'] = df['Market value'].apply(clean_num)
    if 'Yield' in df.columns:
        df['Yield'] = pd.to_numeric(df['Yield'], errors='coerce')
    if 'Duration' in df.columns:
        df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce')

    # Annual income
    if 'Maturity Value' in df.columns and 'Coupon' in df.columns:
        df['Annual_Income'] = df['Maturity Value'] * df['Coupon']
    else:
        df['Annual_Income'] = pd.NA

    # Detect common initial cost column names and normalize to `Initial_Cost`
    initial_candidates = [c for c in df.columns if c.strip().lower() in (
        'initial cost', 'initialcost', 'initial investment', 'initialinvestment',
        'initial inv amount', 'initial_inv_amount', 'initial inv value', 'initialamount',
        'initial_amount')]
    if initial_candidates:
        ic = initial_candidates[0]
        df['Initial_Cost'] = df[ic].apply(clean_num) if ic in df.columns else pd.NA
    else:
        df['Initial_Cost'] = pd.NA

        # If clean price (%) and accrued (%) exist, compute Initial_Cost = clean_amt + accrued_amt
        # Look for clean price percent columns
        clean_price_cols = [c for c in df.columns if 'clean' in c.lower() and 'price' in c.lower()]
        accrued_cols = [c for c in df.columns if 'acc' in c.lower() or 'accrued' in c.lower() or 'acc.int' in c.lower()]

        # prefer percent fields (strings with %), else numeric amount fields
        for i, row in df.iterrows():
            if pd.isna(df.at[i, 'Initial_Cost']):
                face = df.at[i, 'Maturity Value'] if 'Maturity Value' in df.columns else None
                clean_pct = None
                clean_amt = None
                acc_pct = None
                acc_amt = None

                # detect clean price
                for cp in clean_price_cols:
                    val = df.at[i, cp]
                    if isinstance(val, str) and '%' in val:
                        try:
                            clean_pct = float(val.replace('%', '').replace(',', '').strip())
                            break
                        except Exception:
                            continue
                    elif pd.notna(val):
                        try:
                            clean_amt = float(str(val).replace(',', '').strip())
                            break
                        except Exception:
                            continue

                # detect accrued
                for ac in accrued_cols:
                    val = df.at[i, ac]
                    if isinstance(val, str) and '%' in val:
                        try:
                            acc_pct = float(val.replace('%', '').replace(',', '').strip())
                            break
                        except Exception:
                            continue
                    elif pd.notna(val):
                        try:
                            acc_amt = float(str(val).replace(',', '').strip())
                            break
                        except Exception:
                            continue

                # compute using helper if we have any of the pieces
                if face is not None and (clean_pct is not None or clean_amt is not None or acc_pct is not None or acc_amt is not None):
                    # avoid import loop: import local helper
                    from calculations.purchase_values import compute_purchase_values

                    c_amt, a_amt, full = compute_purchase_values(
                        face_value=face,
                        clean_price_pct=clean_pct,
                        clean_price_amount=clean_amt,
                        accrued_pct=acc_pct,
                        accrued_amount=acc_amt,
                    )
                    # if computed full is available, set Initial_Cost
                    if full is not None:
                        df.at[i, 'Initial_Cost'] = full

    return df


def summarize(df: pd.DataFrame) -> dict:
    df = normalize_and_clean(df)

    # total face
    total_face = df['Maturity Value'].sum(skipna=True)

    # total market value: take first per ISIN (group totals in source)
    if 'Market value' in df.columns:
        total_market = df.groupby('ISIN')['Market value'].first().sum()
    else:
        total_market = pd.NA

    unrealized_vs_face = pd.NA
    try:
        unrealized_vs_face = total_market - total_face
    except Exception:
        unrealized_vs_face = pd.NA

    # total initial cost if available (first per ISIN)
    total_initial = pd.NA
    if 'Initial_Cost' in df.columns and df['Initial_Cost'].notna().any():
        try:
            total_initial = df.groupby('ISIN')['Initial_Cost'].first().sum()
        except Exception:
            total_initial = pd.NA

    unrealized_vs_initial = pd.NA
    try:
        if pd.notna(total_initial) and pd.notna(total_market):
            unrealized_vs_initial = total_market - total_initial
    except Exception:
        unrealized_vs_initial = pd.NA

    weighted_coupon = (df['Coupon'] * df['Maturity Value']).sum(skipna=True) / total_face if total_face else pd.NA
    weighted_yield = (df['Yield'] * df['Maturity Value']).sum(skipna=True) / total_face if total_face else pd.NA
    weighted_duration = (df['Duration'] * df['Maturity Value']).sum(skipna=True) / total_face if total_face else pd.NA

    # maturity ladder
    if 'Maturity Date' in df.columns:
        years = pd.to_datetime(df['Maturity Date'], errors='coerce').dt.year
        maturity_ladder = df.assign(Maturity_Year=years).groupby('Maturity_Year')['Maturity Value'].sum().dropna()
    else:
        maturity_ladder = pd.Series(dtype=float)

    # ISIN concentration
    isin_conc = df.groupby('ISIN')['Maturity Value'].sum().div(total_face).fillna(0) * 100 if total_face else pd.Series(dtype=float)

    # annual income
    total_annual_income = df['Annual_Income'].sum(skipna=True)

    return {
        'total_face': total_face,
        'total_market': total_market,
        'unrealized_vs_face': unrealized_vs_face,
        'total_initial_cost': total_initial,
        'unrealized_vs_initial': unrealized_vs_initial,
        'weighted_coupon': weighted_coupon,
        'weighted_yield': weighted_yield,
        'weighted_duration': weighted_duration,
        'maturity_ladder': maturity_ladder.sort_index(),
        'isin_concentration': isin_conc.sort_values(ascending=False),
        'total_annual_income': total_annual_income,
        'cleaned_df': df,
    }
