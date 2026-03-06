import numpy as np
import pandas as pd


def fit_yield_curve(df):
    x = df['years_to_maturity'].astype(float).values
    y = df['yield'].astype(float).values
    if len(x) < 2:
        return pd.Series(y, index=x)
    coef = np.polyfit(x, y, 2)
    xs = np.linspace(float(x.min()), float(x.max()), 50)
    ys = np.polyval(coef, xs)
    return pd.Series(ys, index=xs)
