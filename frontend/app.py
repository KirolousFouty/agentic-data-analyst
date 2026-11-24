import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API = os.getenv("API_BASE_URL", "http://localhost:8000")
st.set_page_config(page_title="Enterprise AI Data Analyst", layout="wide")
st.markdown(
    """
    <style>
      [data-testid="stSidebar"] { min-width: 22rem; max-width: 22rem; }
      [data-testid="stSidebar"] p { font-size: 0.92rem; line-height: 1.45; }
      [data-testid="stSidebar"] code { font-size: 0.78rem; white-space: normal; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Enterprise AI Data Analyst Agent")
st.caption("Local Qwen + LangGraph • Read-only PostgreSQL • Evidence-grounded responses")
if "conversation_id" not in st.session_state: st.session_state.conversation_id = None
question = st.chat_input("Ask a business question, e.g. Which categories have the highest return rates?")
if question:
    with st.spinner("Planning, validating, and analyzing locally…"):
        try:
            response = requests.post(f"{API}/ask", json={"question": question, "conversation_id": st.session_state.conversation_id}, timeout=180)
            response.raise_for_status()
            data=response.json()
            st.session_state.conversation_id=data["conversation_id"]
        except requests.RequestException:
            data = {"answer": "The analysis service is temporarily unavailable. Please retry shortly.", "error": "service_unavailable"}
    st.chat_message("user").write(question)
    st.chat_message("assistant").write(data["answer"])
    if data.get("error"):
        st.info("The local model is initializing. Your database and dashboard remain available.")
    if data.get("sql"):
        with st.expander("Inspect executed SQL"): st.code(data["sql"], language="sql")
    if data.get("rows"):
        df=pd.DataFrame(data["rows"]); st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "analysis.csv", "text/csv")
        chart=data.get("chart")
        if chart and chart["x"] in df and chart["y"] in df: st.plotly_chart(px.bar(df, x=chart["x"], y=chart["y"], title=chart["title"]), use_container_width=True)
with st.sidebar:
    st.subheader("Metric definitions")
    st.caption("All monetary values are USD.")
    st.markdown("**Revenue**  ")
    st.code("SUM(quantity × unit price − discount)", language=None)
    st.markdown("**Gross margin**  ")
    st.code("Revenue − SUM(quantity × unit cost)", language=None)
    st.markdown("**Return rate**  ")
    st.code("Returned order items ÷ sold order items", language=None)
    st.markdown("**Retention**  ")
    st.caption("Customers ordering this month who also ordered in the preceding month.")
