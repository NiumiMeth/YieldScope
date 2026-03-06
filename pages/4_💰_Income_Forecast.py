import streamlit as st
import pandas as pd
import plotly.express as px

from services.portfolio_service import process_uploaded_data


st.header("Future Income Projection")

# Use session_state if available
if 'portfolio_df' in st.session_state:
    df = st.session_state['portfolio_df']

    if 'Maturity Date' in df.columns:
        df = df.copy()
        df['Year'] = pd.to_datetime(df['Maturity Date'], errors='coerce').dt.year
        income_by_year = df.groupby('Year')['Annual_Income'].sum().reset_index()

        fig = px.bar(
            income_by_year.dropna(),
            x='Year',
            y='Annual_Income',
            title="Expected Annual Coupon Income (LKR)",
            text_auto='.2s',
            color_discrete_sequence=['#00FFAA']
        )

        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        total_cash = df['Annual_Income'].sum(skipna=True)
        st.success(f"Estimated Total Annual Cash Flow: LKR {total_cash:,.2f}")
    else:
        st.warning("'Maturity Date' column missing from uploaded data.")
else:
    st.warning("Upload data in the 'My Holdings' page first to see your income forecast.")
