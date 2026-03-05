import streamlit as st
import pandas as pd
from .charts import yield_curve, maturity_distribution, monthly_income_chart
from analytics.transactions import last_next_coupon, accrint, coupon_schedule

def _parse_numeric(val):
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
    st.set_page_config(layout="wide") # Use full screen width for professional look
    
    # --- 1. DATA PREPROCESSING (Fixing the 'Market Value' Error) ---
    df = df.copy()
    today = pd.Timestamp.today().normalize()

    # Column Mapping (Handling variations in user spreadsheets)
    face_col = next((c for c in df.columns if 'face' in c.lower() or 'qty' in c.lower()), None)
    coupon_col = next((c for c in df.columns if 'coupon' in c.lower() or 'cupon' in c.lower()), None)
    mat_col = next((c for c in df.columns if 'mat' in c.lower()), None)
    yield_col = next((c for c in df.columns if 'yield' in c.lower()), None)
    clean_col = next((c for c in df.columns if 'clean' in c.lower() or 'price' in c.lower()), None)

    # Required internal columns
    processed_rows = []
    for _, r in df.iterrows():
        face = _parse_numeric(r.get(face_col, 0))
        c_rate = _parse_numeric(r.get(coupon_col, 0))
        if c_rate > 1: c_rate /= 100.0 # Normalize 10.75 to 0.1075
        
        maturity = pd.to_datetime(r.get(mat_col))
        yld = _parse_numeric(r.get(yield_col, 0))
        if yld > 1: yld /= 100.0
        
        # Calculate Accrued Interest & Market Value
        try:
            ai = accrint(today, maturity, c_rate, face=face, freq=2)
        except:
            ai = 0.0
            
        # Simplified Market Value: (Clean Price % of Face) + Accrued
        clean_px = _parse_numeric(r.get(clean_col, 100))
        if clean_px > 2: # it's a percentage like 98.5
            mv = (clean_px / 100.0) * face + ai
        else: # it's already a multiplier
            mv = (clean_px * face) + ai

        processed_rows.append({
            "Bond_Name": r.get('Party') or r.get('Deal No') or "Bond",
            "Maturity_Date": maturity,
            "Coupon_Rate": c_rate * 100, # Display as percentage
            "Yield_Rate": yld * 100,     # Display as percentage
            "Face_Value": face,
            "Market Value": mv,
            "Accrued_Interest": ai
        })

    pdf = pd.DataFrame(processed_rows)

    # --- 2. PREMIUM UI: KPI CARDS ---
    st.title("💼 Portfolio Executive Analytics")
    
    m1, m2, m3, m4 = st.columns(4)
    total_mv = pdf['Market Value'].sum()
    avg_yield = (pdf['Yield_Rate'] * pdf['Market Value']).sum() / total_mv if total_mv > 0 else 0
    
    m1.metric("Total Market Value", f"LKR {total_mv:,.2f}")
    m2.metric("Weighted Avg Yield", f"{avg_yield:.2f}%")
    m3.metric("Total Face Value", f"{pdf['Face_Value'].sum():,.0f}")
    m4.metric("Active Positions", len(pdf))

    st.markdown("---")

    # --- 3. TABBED NAVIGATION ---
    tab1, tab2, tab3 = st.tabs(["📊 Holdings", "📈 Risk & Yield", "📅 Cash Flows"])

    with tab1:
        st.subheader("Current Positions")
        st.dataframe(
            pdf,
            column_config={
                "Market Value": st.column_config.NumberColumn(format="LKR %,.2f"),
                "Face_Value": st.column_config.NumberColumn(format="%,.0f"),
                "Coupon_Rate": st.column_config.NumberColumn(format="%.2f%%"),
                "Yield_Rate": st.column_config.NumberColumn(format="%.2f%%"),
                "Maturity_Date": st.column_config.DateColumn("Maturity"),
            },
            hide_index=True,
            use_container_width=True
        )

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(yield_curve(pdf), use_container_width=True)
        with c2:
            st.plotly_chart(maturity_distribution(pdf), use_container_width=True)

    with tab3:
        st.subheader("12-Month Income Projection")
        # Generate cash flows for the chart
        st.plotly_chart(monthly_income_chart(pdf), use_container_width=True)
        
        # Display the raw calendar below
        cf_cal = cash_flow_calendar(pdf)
        if not cf_cal.empty:
            st.write("Upcoming Payments")
            st.dataframe(cf_cal, use_container_width=True, hide_index=True)

# Helper for the chart logic
def cash_flow_calendar(df):
    rows = []
    today = pd.Timestamp.today().normalize()
    end = today + pd.DateOffset(months=12)
    
    for _, r in df.iterrows():
        # Re-using the schedule logic from your analytics module
        try:
            # You'll need to ensure coupon_schedule is imported correctly
            from analytics.transactions import coupon_schedule
            dates = coupon_schedule(r['Maturity_Date'], freq=2)
            for d in dates:
                if today < d <= end:
                    amt = (r['Face_Value'] * (r['Coupon_Rate']/100)) / 2
                    rows.append({'date': d, 'bond': r['Bond_Name'], 'payment': amt})
        except:
            continue
    return pd.DataFrame(rows).sort_values('date') if rows else pd.DataFrame()