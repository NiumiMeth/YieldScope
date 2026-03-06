Bond Portfolio Analytics — minimal Streamlit dashboard

Quick start:

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

2. Run the dashboard:

```bash
streamlit run bond_portfolio_dashboard/app.py
```

Files created under `bond_portfolio_dashboard/`:
- `app.py` — Streamlit entrypoint
- `pages/` — UI pages
- `calculations/` — analytics helpers
- `services/` — data access
- `models/` — domain models
- `utils/` — small utilities
- `data/sample_bonds.csv` — sample data

This is a small starter scaffold you can extend.
