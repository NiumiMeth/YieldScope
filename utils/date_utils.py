"""Date utility helpers."""
import pandas as pd

def parse_date(series_or_value):
	return pd.to_datetime(series_or_value)

