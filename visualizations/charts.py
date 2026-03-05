import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def yield_curve(df: pd.DataFrame, yield_col: str, mat_col: str, name_col: str):
    """Institutional Yield Curve: Relationship between Maturity and Yield."""
    fig = px.scatter(
        df, x=mat_col, y=yield_col,
        size=df.columns[0], color=yield_col,
        hover_name=name_col, title="Portfolio Yield Curve Analysis",
        labels={mat_col: 'Maturity', yield_col: 'Yield (%)'},
        template="plotly_white", color_continuous_scale='Viridis'
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig

def maturity_distribution(df: pd.DataFrame, mat_col: str):
    """Maturity Ladder: Shows concentration of principal repayments."""
    df[mat_col] = pd.to_datetime(df[mat_col])
    fig = px.histogram(
        df, x=mat_col, nbins=15,
        title='Liquidity Profile (Maturity Ladder)',
        color_discrete_sequence=['#1e293b'],
        template="plotly_white"
    )
    fig.update_layout(bargap=0.1, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def coupon_calendar_visual(cf_df: pd.DataFrame):
    """Payment Intensity Heatmap: Visualizes income density."""
    if cf_df.empty: return go.Figure()
    
    df = cf_df.copy()
    df['Month_Name'] = df['Date'].dt.strftime('%b')
    df['Weekday'] = df['Date'].dt.strftime('%a')
    agg = df.groupby(['Month_Name', 'Weekday', 'Date'], as_index=False).agg({'Amount': 'sum'})

    fig = px.density_heatmap(
        agg, x="Month_Name", y="Weekday", z="Amount",
        title="Payment Intensity Heatmap",
        category_orders={"Weekday": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                         "Month_Name": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]},
        color_continuous_scale="Viridis", template="plotly_white"
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="Day of Week")
    return fig

def income_projection_chart(cf_df: pd.DataFrame):
    """Monthly Bar Chart: Projected Cash Inflows."""
    if cf_df.empty: return go.Figure()
    cf_df['Month'] = cf_df['Date'].dt.strftime('%b %Y')
    monthly = cf_df.groupby(['Month', 'Date'])['Amount'].sum().reset_index().sort_values('Date')
    
    return px.bar(
        monthly, x='Month', y='Amount',
        title="Projected Monthly Coupon Income",
        color_discrete_sequence=['#10b981'],
        template="plotly_white"
    )