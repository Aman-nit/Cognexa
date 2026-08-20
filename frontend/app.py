"""Streamlit investigator UI: submits claims questions and displays evidence."""

import streamlit as st

st.set_page_config(page_title="ClaimShield AI", page_icon="🛡️")
st.title("ClaimShield AI")
st.caption("Evidence-grounded insurance claim investigation")

query = st.text_input("Investigation query", placeholder="Enter a claim ID or fraud question")
if st.button("Investigate", type="primary") and query:
    st.info("Connect this UI to the FastAPI /investigate endpoint to retrieve evidence.")
    st.write({"query": query, "status": "API connection pending"})
