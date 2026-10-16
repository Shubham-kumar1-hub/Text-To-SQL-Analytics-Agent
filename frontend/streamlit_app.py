"""
Streamlit frontend for the Text-to-SQL analytics agent.
"""

# python -m streamlit run frontend/streamlit_app.py

import requests
import streamlit as st


# FastAPI runs locally on port 8000.
API_URL = "http://127.0.0.1:8000/query"
METRICS_URL = "http://127.0.0.1:8000/metrics"

@st.cache_data(ttl=60)
def get_metrics():
    """Fetch the latest evaluation metrics from FastAPI."""

    try:
        response = requests.get(METRICS_URL, timeout=5)
        response.raise_for_status()

        return response.json()

    except requests.RequestException:
        return None

st.set_page_config(
    page_title="Text-to-SQL Analytics Agent",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Text-to-SQL Analytics Agent")
st.caption("Ask ecommerce analytics questions in plain English.")

metrics = get_metrics()

if metrics:
    metric_column, case_column = st.columns(2)

    metric_column.metric(
        "Execution accuracy",
        f"{metrics['execution_accuracy_percent']:.1f}%",
    )

    case_column.metric(
        "Custom evaluation cases",
        f"{metrics['passed_cases']}/{metrics['total_cases']}",
    )

    st.caption("Measured on the custom ecommerce evaluation set.")


st.markdown(
    """
Try questions such as:

- Which 5 products have the highest price?
- Which customers returned the most products?
- What is the total revenue by product category?
"""
)

question = st.text_area(
    "Your analytics question",
    placeholder="Example: Which customers returned the most products?",
)

if st.button("Ask question", type="primary"):
    if not question.strip():
        st.warning("Please enter an analytics question.")

    else:
        with st.spinner("Generating and running SQL safely..."):
            try:
                response = requests.post(
                    API_URL,
                    json={"question": question},
                    timeout=60,
                )

                response.raise_for_status()
                data = response.json()

            except requests.RequestException:
                st.error(
                    "Could not connect to the FastAPI backend. "
                    "Make sure it is running on port 8000."
                )

            else:
                st.subheader("Answer")
                st.write(data["answer"])

                # Ambiguous questions intentionally do not generate SQL.
                if data["needs_clarification"]:
                    st.info(
                        "Please submit a revised question that includes this detail. "
                        "For example: Which customers returned the highest number of items?"
                    )

                else:
                    if data["rows"]:
                        st.subheader("Results")
                        st.dataframe(
                            data["rows"],
                            use_container_width=True,
                        )

                    with st.expander("Generated SQL"):
                        st.code(data["sql"], language="sql")

                    st.caption(
                        f"SQL attempts: {data['sql_attempts']}"
                    )