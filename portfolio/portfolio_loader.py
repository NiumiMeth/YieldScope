"""Portfolio loading functions

Load a CSV or Excel portfolio into a pandas DataFrame.
"""
import pandas as pd
from typing import Union

def load_portfolio(path: str) -> pd.DataFrame:
	"""Load CSV or Excel file into a DataFrame.

	Accepts CSV and Excel (.xls, .xlsx).
	"""
	if path.lower().endswith(('.xls', '.xlsx')):
		return pd.read_excel(path)
	return pd.read_csv(path)

