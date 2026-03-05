"""Streamlit entrypoint for the Bond Portfolio Analytics dashboard.

Run with: `streamlit run app.py`
"""
import streamlit as st
import pandas as pd
from pathlib import Path

# Custom Module Imports
from portfolio.portfolio_loader import load_portfolio
from portfolio.normalizer import normalize_portfolio
from visualizations.dashboards import show_portfolio_overview

# 1. Page Configuration (Must be the first Streamlit command)
st.set_page_config(
    page_title='Institutional Bond Analytics', 
    layout='wide', 
    initial_sidebar_state='expanded'
)

# 2. Sidebar Data Management
st.sidebar.header('📂 Portfolio Data')

# User Uploader
uploaded_file = st.sidebar.file_uploader(
    'Upload Portfolio (CSV/Excel)', 
    type=['csv', 'xls', 'xlsx'],
    help="Upload your bond confirmation or portfolio export here."
)

# Configuration for Default/Sample Data
DEFAULT_PATH = 'data/Details.csv'
df = None

# --- Data Loading Logic ---
if uploaded_file is not None:
    try:
        # Determine file type and read
        if uploaded_file.name.lower().endswith(('.xls', '.xlsx')):
            df_raw = pd.read_excel(uploaded_file)
        else:
            df_raw = pd.read_csv(uploaded_file)
        
        # Pass to your normalizer to map columns like 'Qty Traded' -> 'Face Value'
        df = normalize_portfolio(df_raw)
        st.sidebar.success(f"✅ {uploaded_file.name} loaded")
    except Exception as e:
        st.sidebar.error(f"Upload Error: {e}")

else:
    # Fallback to local sample data if it exists
    try:
        sample_paths = [DEFAULT_PATH, 'data/details.csv', 'data/sample_portfolio.csv']
        valid_path = next((p for p in sample_paths if Path(p).exists()), None)
        
        if valid_path:
            # We use load_portfolio if it handles specific CSV parsing, 
            # otherwise read_csv + normalize_portfolio
            df_raw = pd.read_csv(valid_path)
            df = normalize_portfolio(df_raw)
            st.sidebar.info(f"💡 Active: {valid_path}")
        else:
            st.sidebar.warning("⚠️ Waiting for data upload...")
    except Exception as e:
        st.sidebar.error(f"Sample Load Error: {e}")

# --- Dashboard Execution ---
if df is not None:
    # This calls the high-end UI with Metrics, Tabs, and Charts
    show_portfolio_overview(df)
else:
    # Landing Page UI when no data is present
    st.title("Bond Portfolio Analytics")
    st.info("Welcome! Please use the sidebar to upload your bond portfolio (CSV or Excel) to generate your executive dashboard.")
    
    # Optional: Display a diagram showing the data flow