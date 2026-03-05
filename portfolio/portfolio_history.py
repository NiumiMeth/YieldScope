"""Portfolio history tracking

Small helper to save versions of portfolio snapshots.
"""
import pandas as pd
from datetime import datetime
from pathlib import Path

def save_snapshot(df: pd.DataFrame, out_dir: str = 'portfolio_snapshots') -> str:
	Path(out_dir).mkdir(parents=True, exist_ok=True)
	ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
	out_path = Path(out_dir) / f'portfolio_snapshot_{ts}.csv'
	df.to_csv(out_path, index=False)
	return str(out_path)

