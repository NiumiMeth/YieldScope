import pandas as pd


def process_uploaded_data(df: pd.DataFrame) -> pd.DataFrame:
    """Specific cleaner for your 'Details 1' CSV format"""
    # Clean column names
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    # Drop subtotal rows (rows where ISIN is missing)
    if 'ISIN' in df.columns:
        df = df.dropna(subset=['ISIN']).copy()

    # Helper to clean currency and percentages
    def clean_val(val):
        if isinstance(val, str):
            v = val.replace('%', '').replace(',', '').strip()
            try:
                return float(v)
            except Exception:
                return pd.NA
        return val

    # Apply cleaning where columns exist
    if 'Coupon' in df.columns:
        df['Coupon'] = df['Coupon'].apply(clean_val) / 100
    if 'Maturity Value' in df.columns:
        df['Maturity Value'] = df['Maturity Value'].apply(clean_val)
    if 'Market value' in df.columns:
        df['Market value'] = df['Market value'].apply(clean_val)

    if 'Yield' in df.columns:
        df['Yield'] = pd.to_numeric(df['Yield'], errors='coerce')
    if 'Duration' in df.columns:
        df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce')

    # Calculate Annual Income per bond when possible
    if 'Maturity Value' in df.columns and 'Coupon' in df.columns:
        df['Annual_Income'] = df['Maturity Value'] * df['Coupon']
    else:
        df['Annual_Income'] = pd.NA

    return df
