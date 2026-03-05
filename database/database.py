"""Database connection and operations

Provides a simple SQLite connection factory used by small scripts
and the Streamlit app.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / 'bond_portfolio.db'

def get_connection(path: str | None = None) -> sqlite3.Connection:
	"""Return a sqlite3 connection to the repository database file.

	If `path` is provided it will be used instead of the default file.
	"""
	db_file = path or str(DB_PATH)
	return sqlite3.connect(db_file)

