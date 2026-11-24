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
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def render_response(data: dict, message_id: int) -> None:
    with st.chat_message("assistant"):
        st.write(data["answer"])
        if data.get("error"):
            st.info("The analysis service could not complete this request. You can refine the question and try again.")
        if data.get("sql"):
            with st.expander("Inspect executed SQL"):
                st.code(data["sql"], language="sql")
        if data.get("rows"):
            frame = pd.DataFrame(data["rows"])
            st.dataframe(frame, use_container_width=True)
            st.download_button(
                "Download CSV",
                frame.to_csv(index=False),
                f"analysis-{message_id}.csv",
                "text/csv",
                key=f"csv-{message_id}",
            )
            chart = data.get("chart")
            if chart and chart["x"] in frame and chart["y"] in frame:
                st.plotly_chart(
                    px.bar(frame, x=chart["x"], y=chart["y"], title=chart["title"]),
                    use_container_width=True,
                    key=f"chart-{message_id}",
                )


for index, message in enumerate(st.session_state.chat_history):
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
    else:
        render_response(message["data"], index)

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
    st.session_state.chat_history.extend([
        {"role": "user", "content": question},
        {"role": "assistant", "data": data},
    ])
    st.rerun()
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
    if st.button("Clear chat history", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.conversation_id = None
        st.rerun()
