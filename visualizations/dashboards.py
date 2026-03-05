"""Dashboard pieces for Streamlit

Tiny helpers wiring charts into Streamlit components.
"""
import streamlit as st
from .charts import yield_scatter, maturity_histogram

def show_portfolio_overview(df):
	st.header('Portfolio Overview')
	st.dataframe(df)
	st.plotly_chart(yield_scatter(df))
	st.plotly_chart(maturity_histogram(df))

