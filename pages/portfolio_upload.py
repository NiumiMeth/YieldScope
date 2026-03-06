import streamlit as st
import pandas as pd


def _clean_numeric_series(s: pd.Series) -> pd.Series:
    # convert to string, strip percent signs, commas, and whitespace
    return (
        s.astype(str)
        .str.replace('%', '', regex=False)
        .str.replace(',', '', regex=False)
        .str.strip()
        .replace({'': None, 'nan': None})
        .pipe(pd.to_numeric, errors='coerce')
    )


def show():
    st.header("Upload Portfolio CSV")
    uploaded = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded is None:
        st.info("Upload a CSV with columns: ISIN, Instrument, Maturity Date, Coupon, Maturity Value, Yield, Market value, Duration")
        return

    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        return

    # normalize column names
    col_map = {c: c.strip().lower().replace(' ', '_') for c in df.columns}
    df.rename(columns=col_map, inplace=True)

    # expected column names after normalizing
    # isin, instrument, maturity_date, coupon, maturity_value, yield, market_value, duration

    # Find likely yield and market value column names
    possible_yield_cols = [c for c in df.columns if 'yield' in c]
    possible_mv_cols = [c for c in df.columns if 'market' in c or 'market_value' in c or 'marketvalue' in c]

    if not possible_yield_cols:
        st.warning('Could not find a column that looks like "Yield". Please ensure one exists.')
    if not possible_mv_cols:
        st.warning('Could not find a column that looks like "Market value". Please ensure one exists.')

    yield_col = possible_yield_cols[0] if possible_yield_cols else None
    mv_col = possible_mv_cols[0] if possible_mv_cols else None

    # Clean numeric columns if present
    if yield_col:
        df[yield_col] = _clean_numeric_series(df[yield_col])
    if mv_col:
        df[mv_col] = _clean_numeric_series(df[mv_col])

    # Also try to clean coupon and maturity_value/par
    for name in ['coupon', 'maturity_value', 'maturity_value', 'par', 'maturity_value', 'maturity_value']:
        if name in df.columns:
            df[name] = _clean_numeric_series(df[name])

    st.subheader('Cleaned Data (preview)')
    st.dataframe(df.head(50))

    # Calculate metrics
    if mv_col and yield_col:
        total_market_value = df[mv_col].sum(min_count=1)
        if pd.isna(total_market_value) or total_market_value == 0:
            st.warning('Total market value is zero or could not be calculated.')
        else:
            weighted_yield = (df[yield_col] * df[mv_col]).sum(min_count=1) / total_market_value

            # display nicely
            st.metric('Total Market Value', f"{total_market_value:,.2f}")
            st.metric('Weighted Average Yield', f"{weighted_yield:.4f}%" if weighted_yield is not None else 'n/a')

    else:
        st.info('Upload contains cleaned data but either market value or yield column is missing, so metrics cannot be computed.')

    # show raw column names to help users
    st.caption(f"Columns detected: {', '.join(df.columns)}")
