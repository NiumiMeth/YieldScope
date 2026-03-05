"""Streamlit entrypoint for the Bond Portfolio Analytics dashboard.

Run with: `streamlit run app.py`
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from portfolio.portfolio_loader import load_portfolio
from portfolio.normalizer import normalize_portfolio
from visualizations.dashboards import show_portfolio_overview

st.set_page_config(page_title='Bond Portfolio Analytics', layout='wide')
st.title('Bond Portfolio Analytics Dashboard')

st.sidebar.header('Data')
uploaded = st.sidebar.file_uploader('Upload portfolio CSV/Excel', type=['csv', 'xls', 'xlsx'])
if uploaded is not None:
	try:
		if str(uploaded.name).lower().endswith(('.xls', '.xlsx')):
			df_raw = pd.read_excel(uploaded)
		else:
			df_raw = pd.read_csv(uploaded)
		df = normalize_portfolio(df_raw)
		show_portfolio_overview(df)
	except Exception as e:
		st.error(f'Failed to load uploaded portfolio: {e}')
else:
	# If no upload, try to load a sample Details.csv from data/ for convenience
	try:
		sample_paths = ['data/Details.csv', 'data/details.csv', 'data/sample_portfolio.csv']
		sample = next((p for p in sample_paths if Path(p).exists()), None)
		if sample:
			df_raw = pd.read_csv(sample)
			df = normalize_portfolio(df_raw)
			st.info(f'Loaded sample portfolio: {sample}')
			show_portfolio_overview(df)
		else:
			st.info('Upload a portfolio CSV/Excel file in the sidebar to begin.')
	except Exception as e:
		st.error(f'Failed to load sample portfolio: {e}')

