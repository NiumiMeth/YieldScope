import streamlit as st
from ..services.data_loader import load_data


def show():
    st.title("Bond Portfolio Dashboard")
    st.write("A lightweight dashboard for exploring a sample bond portfolio.")

    df = load_data()
    st.subheader("Sample bonds")
    st.dataframe(df)
