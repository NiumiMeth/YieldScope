import streamlit as st
from services.data_loader import load_data
from models.portfolio import Portfolio


def show():
    st.header("Portfolio")
    df = load_data()
    portfolio = Portfolio.from_dataframe(df)

    st.subheader("Summary")
    st.json(portfolio.summary())

    st.subheader("Holdings")
    st.dataframe(df)
