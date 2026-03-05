"""Streamlit entrypoint for the Bond Portfolio Analytics dashboard.

Run with: `streamlit run app.py`
"""
import streamlit as st
import pandas as pd
from portfolio.portfolio_loader import load_portfolio
from visualizations.dashboards import show_portfolio_overview

st.title('Bond Portfolio Analytics Dashboard')

DEFAULT_DATA = 'data/Details.csv'

path = st.sidebar.text_input('Portfolio path', DEFAULT_DATA)
try:
	df = load_portfolio(path)
	show_portfolio_overview(df)
except Exception as e:
	st.error(f'Failed to load portfolio: {e}')

