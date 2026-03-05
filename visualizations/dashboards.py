import streamlit as st
import pandas as pd
import io
import plotly.express as px
from .charts import (
    yield_curve, 
    maturity_distribution, 
    monthly_income_chart, 
    coupon_calendar_visual,
    yield_scatter
)
from analytics.transactions import (
    last_next_coupon, 
    coupon_schedule, 
    price_from_yield, 
    accrint, 
    full_price_from_clean, 
    funding_cost_over_period
)

def _parse_numeric(val):
    """Helper to convert string-based currency/percents to clean floats."""
    if pd.isna(val) or val == '': return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = str(val).replace('LKR', '').replace('Rs', '').replace(',', '').strip()
    if s.endswith('%'):
        return float(s[:-1]) / 100.0
    try:
        return float(s)
    except:
        return 0.0

def show_portfolio_overview(df: pd.DataFrame):
    # Professional Styling
    st.markdown("""
        <style>
        div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #1e293b; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f8f9fa; border-radius: 4px; padding: 10px; }
        </style>
    """, unsafe_allow_html=True)

    if df is None or df.empty:
        st.warning("Please upload a portfolio file to generate analytics.")
        return

    # --- 1. DATA PREPROCESSING & SMART MAPPING ---
    df = df.copy()
    today = pd.Timestamp.today().normalize()

    name_col = next((c for c in df.columns if any(k in c.lower() for k in ['isin', 'instrument', 'deal', 'party'])), df.columns[0])
    face_col = next((c for c in df.columns if 'face' in c.lower() or 'qty' in c.lower()), None)
    coupon_col = next((c for c in df.columns if 'coupon' in c.lower() or 'cupon' in c.lower()), None)
    mat_col = next((c for c in df.columns if 'mat' in c.lower()), None)
    yield_col = next((c for c in df.columns if 'yield' in c.lower()), None)
    clean_col = next((c for c in df.columns if 'clean' in c.lower() or 'price' in c.lower()), None)

    processed_rows = []
    for _, r in df.iterrows():
        face = _parse_numeric(r.get(face_col, 0))
        c_rate = _parse_numeric(r.get(coupon_col, 0))
        if c_rate > 1: c_rate /= 100.0 
        
        maturity = pd.to_datetime(r.get(mat_col))
        yld = _parse_numeric(r.get(yield_col, 0))
        if yld > 1: yld /= 100.0
        
        try:
            ai = accrint(today, maturity, c_rate, face=face, freq=2)
        except: ai = 0.0
            
        clean_px = _parse_numeric(r.get(clean_col, 100))
        mv = (clean_px / 100.0 * face + ai) if clean_px > 2 else (clean_px * face + ai)

        processed_rows.append({
            "Bond_Name": r.get(name_col) or "Bond",
            "Maturity_Date": maturity,
            "Coupon_Rate": c_rate * 100,
            "Yield_Rate": yld * 100,
            "Face_Value": face,
            "Market Value": mv,
            "Accrued_Interest": ai,
            "Initial Inv Date": r.get('Invest date') or r.get('Initial Inv Date') or today
        })

    pdf = pd.DataFrame(processed_rows)

    # --- 2. EXECUTIVE SUMMARY KPIs ---
    st.title("💼 Portfolio Executive Analytics")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_mv = pdf['Market Value'].sum()
    avg_yield = (pdf['Yield_Rate'] * pdf['Market Value']).sum() / total_mv if total_mv > 0 else 0
    
    kpi1.metric("Total Market Value", f"LKR {total_mv:,.2f}")
    kpi2.metric("Weighted Avg Yield", f"{avg_yield:.2f}%")
    kpi3.metric("Total Face Value", f"{pdf['Face_Value'].sum():,.0f}")
    kpi4.metric("Risk Status", "Diversified")
    st.divider()

    # --- 3. TABS ---
    tab_summary, tab_analytics, tab_cashflow, tab_valuation = st.tabs([
        "📊 Holdings", "📈 Yield & Risk", "📅 Income Schedule", "💡 Valuation & Shock"
    ])

    with tab_summary:
        st.dataframe(
            pdf,
            use_container_width=True,
            column_config={
                "Market Value": st.column_config.NumberColumn(format="LKR %,.2f"),
                "Face_Value": st.column_config.NumberColumn(format="%,.0f"),
                "Coupon_Rate": st.column_config.NumberColumn(format="%.2f%%"),
                "Yield_Rate": st.column_config.NumberColumn(format="%.2f%%"),
                "Maturity_Date": st.column_config.DateColumn("Maturity"),
            },
            hide_index=True
        )

    with tab_analytics:
        col_left, col_right = st.columns(2)
        with col_left:
            st.plotly_chart(yield_curve(pdf), use_container_width=True)
        with col_right:
            st.plotly_chart(maturity_distribution(pdf), use_container_width=True)

    with tab_cashflow:
        st.subheader("Liquidity & Income Schedule")
        cf_list = []
        for _, r in pdf.iterrows():
            try:
                schedule = coupon_schedule(r['Maturity_Date'], freq=2)
                for d in schedule:
                    if today < d <= (today + pd.DateOffset(months=12)):
                        amt = (r['Face_Value'] * (r['Coupon_Rate']/100)) / 2
                        cf_list.append({'Date': d, 'Bond': r['Bond_Name'], 'Amount': amt})
            except: continue
        
        cf_df = pd.DataFrame(cf_list)
        if not cf_df.empty:
            st.plotly_chart(monthly_income_chart(cf_df), use_container_width=True)
            st.plotly_chart(coupon_calendar_visual(cf_df), use_container_width=True)
            
            # Monthly Dropdowns
            months = cf_df.sort_values('Date')['Date'].dt.strftime('%B %Y').unique()
            for month in months:
                with st.expander(f"💰 Payments for {month}"):
                    month_data = cf_df[cf_df['Date'].dt.strftime('%B %Y') == month]
                    st.table(month_data.assign(
                        Date=lambda x: x['Date'].dt.strftime('%Y-%m-%d'),
                        Amount=lambda x: x['Amount'].map('LKR {:,.2f}'.format)
                    ))

    with tab_valuation:
        st.subheader('Market Sensitivity Analysis')
        col1, col2, col3 = st.columns(3)
        v_date = col1.date_input('Valuation date', value=today.date())
        shock_bps = col2.number_input('Global yield shock (bps)', value=0, step=25)
        funding_rate_pct = col3.number_input('Funding cost (annual %)', value=9.0, step=0.5)

        with st.expander('View Pricing Formulas (LaTeX)'):
            st.latex(r"P_{clean} = \sum_{t=1}^{n} \frac{C}{(1+y)^t} + \frac{F}{(1+y)^n}")
            [Image of the bond pricing formula for clean price]

        vdate_ts = pd.to_datetime(v_date)
        shock = float(shock_bps) / 10000.0
        funding_rate = float(funding_rate_pct) / 100.0

        val_rows = []
        for _, r in pdf.iterrows():
            try:
                coupon = r['Coupon_Rate'] / 100
                face = r['Face_Value']
                curr_y = r['Yield_Rate'] / 100
                init_cost = r['Market Value']

                # Calculate Shocked Price
                s_yield = curr_y + shock
                s_clean = price_from_yield(vdate_ts, r['Maturity_Date'], coupon, s_yield, face=face)
                s_ai = accrint(vdate_ts, r['Maturity_Date'], coupon, face=face)
                s_full = (s_clean/100 * face) + s_ai

                # Funding Cost
                days = (vdate_ts - pd.to_datetime(r['Initial Inv Date'])).days
                f_cost = funding_cost_over_period(init_cost, funding_rate, max(0, days))

                val_rows.append({
                    'ISIN': r['Bond_Name'],
                    'Face': face,
                    'Init Cost': init_cost,
                    'Shocked Value': s_full,
                    'Funding Cost': f_cost,
                    'P/L': (s_full - init_cost) - f_cost
                })
            except: continue

        res_df = pd.DataFrame(val_rows)
        if not res_df.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Shocked Value", f"LKR {res_df['Shocked Value'].sum():,.2f}")
            m2.metric("Total Funding Cost", f"LKR {res_df['Funding Cost'].sum():,.2f}")
            m3.metric("Net Portfolio P/L", f"LKR {res_df['P/L'].sum():,.2f}", delta=f"{shock_bps} bps Shock")
            
            st.divider()
            st.plotly_chart(px.bar(res_df, x='ISIN', y='P/L', title="P/L Impact by Asset", template="plotly_white", color='P/L', color_continuous_scale='RdYlGn'), use_container_width=True)