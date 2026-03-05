import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def yield_curve(df: pd.DataFrame):
    """Visualizes the relationship between Maturity and Yield."""
    fig = px.scatter(
        df, 
        x='Maturity_Date', 
        y='Yield_Rate',
        size='Market Value', 
        color='Coupon_Rate',
        hover_name='Bond_Name',
        title="Portfolio Yield Curve",
        labels={'Maturity_Date': 'Maturity', 'Yield_Rate': 'Yield (%)'}
    )
    fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
    return fig

def maturity_distribution(df: pd.DataFrame):
    """Shows the concentration of bond maturities."""
    # Ensure maturity is datetime
    df['Maturity_Date'] = pd.to_datetime(df['Maturity_Date'])
    fig = px.histogram(
        df, 
        x='Maturity_Date', 
        nbins=20, 
        title='Maturity Concentration',
        color_discrete_sequence=['#636EFA']
    )
    fig.update_layout(template="plotly_white")
    return fig

def monthly_income_chart(df: pd.DataFrame):
    """Aggregates upcoming payments into a monthly bar chart."""
    # This assumes your cash_flow_calendar helper is available or logic is included
    from .dashboards import cash_flow_calendar 
    cf = cash_flow_calendar(df)
    
    if cf.empty:
        # Return an empty figure with a message if no data
        fig = go.Figure()
        fig.add_annotation(text="No upcoming payments found", showarrow=False)
        return fig
    
    cf['Month'] = cf['date'].dt.strftime('%b %Y')
    monthly = cf.groupby(['Month', 'date'])['payment'].sum().reset_index().sort_values('date')
    
    fig = px.bar(
        monthly, 
        x='Month', 
        y='payment',
        title="Projected Monthly Coupon Income",
        color_discrete_sequence=['#00CC96']
    )
    fig.update_layout(template="plotly_white", yaxis_title="Income (LKR)")
    return fig