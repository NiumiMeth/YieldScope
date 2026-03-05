"""Portfolio metrics calculations

Simple portfolio aggregate computations.
"""
import pandas as pd

def total_face_value(df: pd.DataFrame, face_col: str = 'Face_Value') -> float:
	return float(df[face_col].sum())

def weighted_coupon(df: pd.DataFrame, face_col: str = 'Face_Value', coupon_col: str = 'Coupon_Rate') -> float:
	total = df[face_col].sum()
	if total == 0:
		return 0.0
	return float((df[face_col] * df[coupon_col]).sum() / total)

