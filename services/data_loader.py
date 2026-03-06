import pandas as pd
from pathlib import Path


def load_data():
    p = Path(__file__).parent.parent / 'data' / 'sample_bonds.csv'
    df = pd.read_csv(p)
    return df
