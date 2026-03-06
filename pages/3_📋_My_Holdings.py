import streamlit as st
import pandas as pd

from services.portfolio_service import process_uploaded_data


st.header("Detailed Portfolio Holdings")

# File upload in sidebar
uploaded_file = st.sidebar.file_uploader("Upload your Portfolio CSV", type="csv")

if uploaded_file:
    try:
        raw_df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        raw_df = None

    if raw_df is not None:
        df = process_uploaded_data(raw_df)

        # save into session for other pages
        st.session_state['portfolio_df'] = df

        # Display clean table with column formatting when available
        cols = [c for c in ['ISIN', 'Instrument', 'Maturity Date', 'Coupon', 'Maturity Value', 'Yield', 'Market value', 'Duration', 'Initial_Cost'] if c in df.columns]

        st.dataframe(
            df[cols],
            column_config={
                k: st.column_config.NumberColumn(k, format="%.2f%%") for k in ['Coupon'] if k in df.columns
            } if hasattr(st, 'column_config') else None,
            hide_index=True,
            use_container_width=True
        )
else:
    st.info("Please upload your 'Details 1' CSV file in the sidebar to see your holdings.")
