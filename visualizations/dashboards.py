import streamlit as st
import pandas as pd
import io
import plotly.express as px
from .charts import yield_scatter, maturity_histogram, income_projection_chart, coupon_calendar_visual
from analytics.transactions import last_next_coupon, coupon_schedule, price_from_yield, accrint, full_price_from_clean, funding_cost_over_period

def _clean_numeric(val):
    """Helper to convert string-based currency/percents to clean floats."""
    if pd.isna(val) or val == '':
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    # Remove LKR, Rs, commas, and whitespace
    clean_val = str(val).replace('LKR', '').replace('Rs', '').replace(',', '').strip()
    if clean_val.endswith('%'):
        return float(clean_val[:-1]) / 100.0
    try:
        return float(clean_val)
    except ValueError:
        return 0.0

def show_portfolio_overview(df: pd.DataFrame):
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

    # --- 1. SMART COLUMN DETECTOR & CLEANING ---
    name_col = next((c for c in df.columns if any(k in c.lower() for k in ['isin', 'instrument', 'deal', 'party'])), df.columns[0])
    yield_col = next((c for c in df.columns if 'yield' in c.lower()), None)
    face_col = next((c for c in df.columns if any(k in c.lower() for k in ['face', 'qty', 'units'])), None)
    mat_col = next((c for c in df.columns if 'mat' in c.lower()), None)
    coupon_col = next((c for c in df.columns if 'coupon' in c.lower() or 'cupon' in c.lower()), None)

    # Apply cleaning to numeric columns to prevent the 'str' / 'int' error
    df[face_col] = df[face_col].apply(_clean_numeric)
    if yield_col: df[yield_col] = df[yield_col].apply(_clean_numeric)
    if coupon_col: df[coupon_col] = df[coupon_col].apply(_clean_numeric)

    # --- 2. EXECUTIVE SUMMARY ---
    st.title("💼 Portfolio Management Suite")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_face = df[face_col].sum()
    avg_yield = df[yield_col].mean() if yield_col else 0
    
    kpi1.metric("Total Face Value", f"LKR {total_face:,.0f}")
    kpi2.metric("Weighted Avg Yield", f"{avg_yield:.2f}%")
    kpi3.metric("Asset Count", len(df))
    kpi4.metric("Risk Status", "Diversified")

    st.divider()

    # --- 3. TABS ---
    tab_summary, tab_analytics, tab_cashflow, tab_valuation = st.tabs(["📊 Portfolio Summary", "📈 Yield & Maturity", "📅 Cash Projections", "💡 Valuation & P/L"]) 

    with tab_summary:
        show_full = st.checkbox('Show full portfolio table', value=True)
        table_df = df if show_full else df.head(50)
        st.download_button('Download portfolio CSV', data=table_df.to_csv(index=False).encode('utf-8'), file_name='portfolio.csv', mime='text/csv')
        st.dataframe(
            table_df,
            use_container_width=True,
            column_config={
                mat_col: st.column_config.DateColumn("Maturity") if mat_col else None,
                face_col: st.column_config.NumberColumn("Principal", format="LKR %,.0f") if face_col else None,
                yield_col: st.column_config.NumberColumn("Yield", format="%.2f%%") if yield_col else None,
            },
            hide_index=True,
        )

    with tab_analytics:
        col_left, col_right = st.columns(2)
        with col_left:
            if yield_col:
                st.plotly_chart(yield_scatter(df, yield_col, name_col), use_container_width=True, key='yield_scatter')
        with col_right:
            if mat_col:
                st.plotly_chart(maturity_histogram(df, mat_col), use_container_width=True, key='maturity_histogram')

    with tab_cashflow:
        st.subheader("Liquidity & Income Schedule")
        cf_data = []
        today = pd.Timestamp.today().normalize()
        
        for _, r in df.iterrows():
            try:
                # Frequency set to 2 for semiannual treasury bonds
                schedule = coupon_schedule(r[mat_col], freq=2)
                for d in schedule:
                    if today < d <= (today + pd.DateOffset(months=12)):
                        # Safely handle coupon normalization
                        c_rate = r[coupon_col] / 100 if r[coupon_col] > 1 else r[coupon_col]
                        payment = (r[face_col] * c_rate) / 2
                        cf_data.append({'date': d, 'bond': r[name_col], 'payment': payment})
            except: continue
        
        cf_df = pd.DataFrame(cf_data)
        if not cf_df.empty:
            cf_df['date'] = pd.to_datetime(cf_df['date'])
            st.plotly_chart(income_projection_chart(cf_df), use_container_width=True, key='income_projection')
            st.dataframe(cf_df.sort_values('date'), use_container_width=True, hide_index=True)

            # Calendar visual: convert to expected column names and render
            cf_vis = cf_df.rename(columns={'date': 'Date', 'payment': 'Amount', 'bond': 'Bond'})
            cf_vis['Date'] = pd.to_datetime(cf_vis['Date'])
            st.subheader('Payment Intensity Calendar')
            st.plotly_chart(coupon_calendar_visual(cf_vis), use_container_width=True, key='payment_calendar')

            # Monthly slide-style summary
            st.markdown("### 🗓️ Monthly Payment Schedule")
            months = cf_vis.sort_values('Date')['Date'].dt.strftime('%B %Y').unique()
            for month in months:
                with st.expander(f"💰 {month}", expanded=(month == months[0])):
                    month_data = cf_vis[cf_vis['Date'].dt.strftime('%B %Y') == month]
                    st.table(month_data[['Date', 'Bond', 'Amount']].assign(
                        Date=lambda x: x['Date'].dt.strftime('%Y-%m-%d'),
                        Amount=lambda x: x['Amount'].map('LKR {:,.2f}'.format)
                    ))
    
    with tab_valuation:
        st.subheader('Valuation Settings')
        col1, col2, col3 = st.columns(3)
        valuation_date = col1.date_input('Valuation date', value=pd.Timestamp.today().date())
        shock_bps = col2.number_input('Global yield shock (bps)', value=0, step=1)
        funding_rate_pct = col3.number_input('Funding cost (annual %)', value=0.0, step=0.01)

        # Formulas / Documentation (LaTeX)
        with st.expander('Formulas (click to expand)'):
            st.write('Price, Accrued Interest and Funding Cost formulas used by the valuation engine:')
            st.latex(r"""P_{\text{clean}}(\%) = \frac{100}{F}\sum_{i=1}^{n}\frac{CF_i}{(1+y)^{t_i}}""")
            st.write('where $CF_i$ are coupon cashflows (last period includes principal $F$), $y$ is the annual yield (decimal), and $t_i$ is time in years from valuation date.')
            st.latex(r"""\text{Accrued Interest (AI)} = \text{Coupon}\times\frac{\text{days\_elapsed}}{\text{period\_days}},\quad \text{Coupon}=F\cdot\frac{r}{f}""")
            st.write('Here $r$ is the annual coupon rate (decimal) and $f$ is coupon frequency per year (e.g. $2$ for semiannual).')
            st.latex(r"""\text{Full Price (LKR)} = \frac{P_{\text{clean}}}{100}\times F + AI""")
            st.latex(r"""\text{Funding Cost} = B\times R_{\text{fund}} \times \frac{\text{days}}{365} """)
            st.write('Where $B$ is the running balance (LKR), $R_{\text{fund}}$ is the annual funding rate (decimal).')

        # compute per-ISIN valuation and P/L
        vdate = pd.to_datetime(valuation_date)
        shock = float(shock_bps) / 10000.0
        funding_rate = float(funding_rate_pct) / 100.0

        rows = []
        for _, r in df.iterrows():
            try:
                isin = r[name_col]
                face = float(r[face_col]) if face_col and not pd.isna(r[face_col]) else 0.0
                coupon = float(r[coupon_col]) if coupon_col and not pd.isna(r[coupon_col]) else 0.0
                # ensure coupon is decimal
                coupon = coupon/100.0 if coupon > 1 else coupon
                current_yield = float(r[yield_col]) if yield_col and not pd.isna(r[yield_col]) else None
                # initial cost: prefer Market value column if present
                init_cost = float(r['Market value']) if 'Market value' in r and not pd.isna(r.get('Market value')) else float(r.get('Market Value', 0.0) or 0.0)

                # valuation clean price percent at vdate
                val_clean = price_from_yield(vdate, r[mat_col], coupon, current_yield, face=face, freq=2) if current_yield is not None else None
                val_ai = accrint(vdate, r[mat_col], coupon, face=face, freq=2)
                val_full = full_price_from_clean(val_clean, val_ai, face=face) if val_clean is not None else None

                # shocked valuation
                shocked_yield = None if current_yield is None else (current_yield + shock)
                shocked_clean = price_from_yield(vdate, r[mat_col], coupon, shocked_yield, face=face, freq=2) if shocked_yield is not None else None
                shocked_ai = accrint(vdate, r[mat_col], coupon, face=face, freq=2)
                shocked_full = full_price_from_clean(shocked_clean, shocked_ai, face=face) if shocked_clean is not None else None

                # funding cost: from initial invest date to valuation
                inv_date = pd.to_datetime(r.get('Initial Inv Date')) if 'Initial Inv Date' in r else None
                days = (vdate - inv_date).days if inv_date is not None and not pd.isna(inv_date) else 0
                fund_cost = funding_cost_over_period(init_cost, funding_rate, days) if init_cost and days>0 else 0.0

                pl = None
                if val_full is not None:
                    pl = (val_full - init_cost) - fund_cost

                rows.append({
                    'ISIN': isin,
                    'Face': face,
                    'Coupon': coupon,
                    'Init Cost': init_cost,
                    'Valuation (clean%)': val_clean,
                    'Valuation (full)': val_full,
                    'Shocked Val (full)': shocked_full,
                    'Funding Cost': fund_cost,
                    'P/L': pl,
                    'maturity': r[mat_col],
                    'current_yield': current_yield,
                    'inv_date': r.get('Initial Inv Date') if 'Initial Inv Date' in r else None,
                })
            except Exception:
                continue

        val_df = pd.DataFrame(rows)
        if not val_df.empty:
            # allow per-ISIN overrides: shock (bps) and funding rate (%) using an editable table
            val_df['Shock_bps'] = 0
            val_df['FundingRatePct'] = funding_rate_pct

            editable_cols = ['ISIN', 'Face', 'Coupon', 'Init Cost', 'Valuation (full)', 'Shock_bps', 'FundingRatePct']
            try:
                edited = st.experimental_data_editor(val_df[editable_cols], num_rows="dynamic")
            except Exception:
                edited = st.data_editor(val_df[editable_cols], num_rows="dynamic")

            # recompute shocked valuation and P/L per edited row
            results = []
            for _, er in edited.iterrows():
                try:
                    isin = er['ISIN']
                    row = val_df[val_df['ISIN'] == isin].iloc[0]
                    mat = row['maturity']
                    coupon = row['Coupon']
                    coupon = coupon/100.0 if coupon > 1 else coupon
                    face = row['Face']
                    current_yield = row['current_yield']
                    init_cost = row['Init Cost']
                    shock = float(er.get('Shock_bps', 0)) / 10000.0
                    funding_rate_row = float(er.get('FundingRatePct', funding_rate_pct)) / 100.0

                    shocked_yield = None if current_yield is None else (current_yield + shock)
                    shocked_clean = price_from_yield(vdate, mat, coupon, shocked_yield, face=face, freq=2) if shocked_yield is not None else None
                    shocked_ai = accrint(vdate, mat, coupon, face=face, freq=2)
                    shocked_full = full_price_from_clean(shocked_clean, shocked_ai, face=face) if shocked_clean is not None else None

                    inv_date = pd.to_datetime(row.get('inv_date')) if row.get('inv_date') is not None else None
                    days = (vdate - inv_date).days if inv_date is not None and not pd.isna(inv_date) else 0
                    fund_cost = funding_cost_over_period(init_cost, funding_rate_row, days) if init_cost and days>0 else 0.0

                    pl = None
                    if shocked_full is not None:
                        pl = (shocked_full - init_cost) - fund_cost

                    results.append({
                        'ISIN': isin,
                        'Init Cost': init_cost,
                        'Shocked Val (full)': shocked_full,
                        'Funding Cost': fund_cost,
                        'P/L': pl,
                        'Shock_bps': er.get('Shock_bps', 0),
                        'FundingRatePct': er.get('FundingRatePct', funding_rate_pct),
                    })
                except Exception:
                    continue

            res_df = pd.DataFrame(results)
            if not res_df.empty:
                # Aggregated KPIs
                total_init = res_df['Init Cost'].fillna(0.0).sum()
                total_shocked = res_df['Shocked Val (full)'].fillna(0.0).sum()
                total_funding = res_df['Funding Cost'].fillna(0.0).sum()
                total_pl = res_df['P/L'].fillna(0.0).sum()

                k1, k2, k3, k4 = st.columns(4)
                k1.metric('Total Initial Cost', f"LKR {total_init:,.2f}")
                k2.metric('Total Shocked Value', f"LKR {total_shocked:,.2f}")
                k3.metric('Total Funding Cost', f"LKR {total_funding:,.2f}")
                k4.metric('Total P/L', f"LKR {total_pl:,.2f}")

                st.divider()

                # Download results
                csv_bytes = res_df.to_csv(index=False).encode('utf-8')
                st.download_button('Download Shocked Valuation CSV', data=csv_bytes, file_name='shocked_valuation.csv', mime='text/csv')

                # Per-ISIN cards: allow user to select which ISINs to inspect
                isins = res_df['ISIN'].tolist()
                default = isins[:5]
                sel = st.multiselect('Select ISINs to view as cards', options=isins, default=default)

                for isin in sel:
                    row = res_df[res_df['ISIN'] == isin].iloc[0]
                    with st.expander(f"{isin}"):
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric('Init Cost', f"LKR {row['Init Cost']:,.2f}")
                        c2.metric('Shocked Value', f"LKR {row['Shocked Val (full)']:,.2f}" if pd.notna(row['Shocked Val (full)']) else 'N/A')
                        c3.metric('Funding Cost', f"LKR {row['Funding Cost']:,.2f}")
                        c4.metric('P/L', f"LKR {row['P/L']:,.2f}" if pd.notna(row['P/L']) else 'N/A')

                        # small comparison chart
                        comp = pd.DataFrame({
                            'metric': ['Init Cost', 'Shocked Value'],
                            'amount': [row['Init Cost'] or 0.0, (row['Shocked Val (full)'] or 0.0)]
                        })
                        fig = px.bar(comp, x='metric', y='amount', title=f'{isin} - Init vs Shocked', template='plotly_white', color='metric')
                        st.plotly_chart(fig, use_container_width=True, key=f'isin_chart_{isin}')
                else:
                    st.info('No shocked valuations computed.')
        else:
            st.info('No valuation rows computed.')