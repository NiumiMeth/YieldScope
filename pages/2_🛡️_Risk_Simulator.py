import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

st.header("Interest Rate Sensitivity (Stress Test)")

st.warning("Simulate how a Central Bank rate change affects your portfolio value.")

# Controls
rate_change = st.slider("Simulate Interest Rate Change (%)", -3.0, 3.0, 0.0, 0.25)
duration = st.number_input("Portfolio Duration (yrs)", value=4.2, step=0.1)
portfolio_value = st.number_input("Portfolio Value (LKR)", value=12_500_000, step=10000)

# Approximate impact calculation
impact = -(duration * (rate_change / 100)) * portfolio_value
new_value = portfolio_value + impact

st.divider()
c1, c2 = st.columns(2)
c1.metric("Impact on Portfolio", f"LKR {impact:,.2f}", delta=f"{rate_change}% Rate Move", delta_color="inverse")
c2.metric("New Estimated Value", f"LKR {new_value:,.2f}")

if abs(rate_change) > 1.5:
    st.error("🚨 HIGH RISK: Your portfolio is sensitive to this rate move.")

st.markdown("---")

# Plot the portfolio value across a range of rate moves
rates = np.arange(-3.0, 3.01, 0.25)
values = portfolio_value * (1 - duration * (rates / 100))
df = pd.DataFrame({"Rate Change (%)": rates, "Portfolio Value": values})

fig = px.line(df, x="Rate Change (%)", y="Portfolio Value", title="Portfolio Value vs Interest Rate Change")
fig.update_traces(line_color="#00CC99")
fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)
