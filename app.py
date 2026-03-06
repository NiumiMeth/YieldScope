import streamlit as st
from pathlib import Path
import sys

# Ensure package modules under this folder are importable when running from workspace root
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from pages import home, portfolio, analytics


def main():
    st.set_page_config(page_title="Bond Portfolio Dashboard", layout="wide")
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Portfolio", "Analytics"]) 

    if page == "Home":
        home.show()
    elif page == "Portfolio":
        portfolio.show()
    else:
        analytics.show()


if __name__ == '__main__':
    main()
