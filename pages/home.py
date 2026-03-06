import streamlit as st
import plotly.express as px
from services.data_loader import load_data
from services.portfolio_analytics import summarize


def show():
    st.title("Bond Portfolio Dashboard")
    st.write("A lightweight dashboard for exploring a sample bond portfolio.")

    df = st.session_state.get('portfolio_df') or load_data()

    stats = summarize(df)
    cleaned = stats['cleaned_df']

    # Executive cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Market Value", f"LKR {stats['total_market']:,.0f}" if stats['total_market'] is not None else "n/a")
    c2.metric("Total Face Value", f"LKR {stats['total_face']:,.0f}" if stats['total_face'] is not None else "n/a")

    # show initial cost if present
    if stats.get('total_initial_cost') is not None and pd.notna(stats.get('total_initial_cost')):
        c3.metric("Total Initial Cost", f"LKR {stats['total_initial_cost']:,.0f}")
        c4.metric("Weighted Avg Yield", f"{stats['weighted_yield']*100:.2f}%" if stats['weighted_yield'] is not None else "n/a")
    else:
        unreal = stats['unrealized_vs_face']
        c3.metric("Unrealized Gain (vs Face)", f"LKR {unreal:,.0f}" if unreal is not None else "n/a")
        c4.metric("Weighted Avg Yield", f"{stats['weighted_yield']*100:.2f}%" if stats['weighted_yield'] is not None else "n/a")

    st.markdown("---")

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Maturity Ladder")
        ml = stats['maturity_ladder']
        if not ml.empty:
            ml_df = ml.reset_index().rename(columns={'Maturity_Year': 'Year', 'Maturity Value': 'Amount'})
            fig = px.bar(ml_df, x='Maturity_Year', y='Maturity Value', title='Maturity Ladder (LKR)')
            fig.update_layout(template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info('No maturity data available')

    with right:
        st.subheader('ISIN Concentration')
        ic = stats['isin_concentration']
        if not ic.empty:
            ic_df = ic.reset_index().rename(columns={'index': 'ISIN', 'Maturity Value': 'Pct'})
            fig2 = px.pie(values=ic_df[0], names=ic_df['ISIN'], title='ISIN Concentration')
            fig2.update_layout(template='plotly_dark')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info('No ISIN concentration data')

    st.markdown('---')

    # Annual income
    st.subheader('Annual Income Forecast')
    total_income = stats['total_annual_income']
    st.metric('Estimated Annual Coupon Income', f"LKR {total_income:,.0f}" if total_income is not None else 'n/a')

    # Holdings preview
    st.subheader('Portfolio Holdings (preview)')
    cols = [c for c in ['ISIN', 'Instrument', 'Maturity Date', 'Coupon', 'Maturity Value', 'Yield', 'Market value', 'Duration'] if c in cleaned.columns]
    st.dataframe(cleaned[cols].head(50))

