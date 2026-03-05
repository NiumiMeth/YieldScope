"""Chart generation for visualizations

Small wrappers returning Plotly figures for common charts.
"""
import plotly.express as px
import pandas as pd

def yield_scatter(df: pd.DataFrame, yield_col: str = 'Market_Yield', name_col: str = 'Bond_Name'):
	return px.scatter(df, x=name_col, y=yield_col, title='Bond Yields', hover_data=df.columns)

def maturity_histogram(df: pd.DataFrame, maturity_col: str = 'Maturity_Date'):
	# Expecting maturity_col to be datetime-like
	df = df.copy()
	df[maturity_col] = pd.to_datetime(df[maturity_col])
	return px.histogram(df, x=maturity_col, nbins=20, title='Maturity Distribution')

