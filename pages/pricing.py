import streamlit as st
import pandas as pd

from services.portfolio_pricing import compute_portfolio_initial_cost, compute_pnl
from services.data_loader import load_data


def show():
    st.header("Portfolio Pricing & PnL")

    uploaded = st.file_uploader("Upload portfolio CSV (Details 1)", type=["csv"]) 

    if uploaded is None:
        st.info("Upload a CSV file or use the sample data.")
        df = load_data()
    else:
        try:
            df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Failed to read CSV: {e}")
            return

    with st.spinner("Aggregating by ISIN and computing initial costs..."):
        agg = compute_portfolio_initial_cost(df)

    st.subheader("Aggregated Holdings (one row per ISIN)")
    display_cols = [c for c in ['ISIN', 'Instrument', 'Face_Value', 'Initial_Cost', 'Market_Value', 'Current_Yield'] if c in agg.columns]
    st.dataframe(agg[display_cols].fillna(''))

    st.markdown("---")
    st.subheader("Optional: Per-ISIN Yield Overrides")
    st.write("Enter overrides as CSV lines: ISIN,YieldPercent  (e.g. LKB00529J154,11.5)")
    overrides_text = st.text_area("Overrides (one per line)")

    overrides = {}
    for line in overrides_text.splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 2:
            try:
                overrides[parts[0]] = float(parts[1])
            except Exception:
                st.warning(f"Could not parse override line: {line}")

    if st.button("Compute PnL"):
        pnl_df = compute_pnl(agg, new_yield_map=overrides)

        st.subheader("PnL by ISIN")
        st.dataframe(pnl_df.fillna(''))

        total_initial = pnl_df['Initial_Cost'].dropna().sum() if 'Initial_Cost' in pnl_df.columns else 0.0
        total_new = pnl_df['New_Market_Value'].dropna().sum()
        total_pnl = pnl_df['PnL'].dropna().sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Initial Cost", f"LKR {total_initial:,.2f}")
        c2.metric("Total New Market Value", f"LKR {total_new:,.2f}")
        c3.metric("Total PnL", f"LKR {total_pnl:,.2f}")

    else:
        st.info("Click 'Compute PnL' to price holdings at the provided yields.")
