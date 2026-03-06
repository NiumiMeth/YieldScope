import streamlit as st
from services.data_loader import load_data
from calculations.durations import macaulay_duration
from calculations.yield_curve import fit_yield_curve


def show():
    st.header("Analytics")
    df = load_data()

    st.subheader("Yield Curve (fitted)")
    yc = fit_yield_curve(df)
    st.line_chart(yc)

    st.subheader("Approximate Durations")
    df = df.copy()
    df['duration'] = df.apply(lambda r: macaulay_duration(r['coupon'], r['yield'], r['years_to_maturity'], r['par']), axis=1)
    st.dataframe(df[['id', 'issuer', 'years_to_maturity', 'yield', 'duration']])
