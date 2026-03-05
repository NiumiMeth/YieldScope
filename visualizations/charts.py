import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def yield_scatter(df: pd.DataFrame, yield_col: str, name_col: str):
    fig = px.scatter(
        df, 
        x=name_col, 
        y=yield_col, 
        size=df[yield_col].apply(lambda x: max(x, 1)), # Bubble size
        color=yield_col,
        hover_name=name_col,
        title='Portfolio Yield Concentration',
        template='plotly_white',
        color_continuous_scale='GnBu'
    )
    fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))
    return fig

def maturity_histogram(df: pd.DataFrame, maturity_col: str):
    df = df.copy()
    df[maturity_col] = pd.to_datetime(df[maturity_col])
    fig = px.histogram(
        df, 
        x=maturity_col, 
        title='Maturity Profile',
        template='plotly_white',
        color_discrete_sequence=['#1e293b']
    )
    fig.update_layout(bargap=0.1, margin=dict(l=0, r=0, t=50, b=0))
    return fig

def income_projection_chart(cf_df: pd.DataFrame):
    cf_df['Month'] = cf_df['date'].dt.strftime('%b %Y')
    monthly = cf_df.groupby(['Month', 'date'])['payment'].sum().reset_index().sort_values('date')
    
    fig = px.bar(
        monthly, 
        x='Month', 
        y='payment',
        title="Projected Monthly Coupon Income",
        template='plotly_white',
        color_discrete_sequence=['#10b981']
    )
    return fig


def coupon_calendar_visual(cf_df: pd.DataFrame):
    """Creates a Calendar Heatmap using month (x) and weekday (y).

    Expects a DataFrame with at least: `Date`/`date` (datetime) and `Amount`/`payment` (numeric).
    """
    df = cf_df.copy()
    # normalize column names
    if 'Date' not in df.columns and 'date' in df.columns:
        df = df.rename(columns={'date': 'Date'})
    if 'Amount' not in df.columns and 'payment' in df.columns:
        df = df.rename(columns={'payment': 'Amount'})
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month_Name'] = df['Date'].dt.strftime('%b')
    df['Weekday'] = df['Date'].dt.strftime('%a')

    agg = df.groupby(['Month_Name', 'Weekday', 'Date'], as_index=False).agg({'Amount': 'sum'})

    fig = px.density_heatmap(
        agg,
        x="Month_Name",
        y="Weekday",
        z="Amount",
        title="Payment Intensity Calendar",
        category_orders={"Weekday": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                         "Month_Name": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]},
        color_continuous_scale="Viridis",
        template="plotly_white"
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Day of Week",
        coloraxis_colorbar=dict(title="LKR Income")
    )
    return fig