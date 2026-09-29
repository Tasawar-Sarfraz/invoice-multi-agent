import streamlit as st

from tools.database_tool import initialize_database
from crew.invoice_crew import create_invoice_classification_crew


st.set_page_config(
    page_title="Invoice Processing System",
    layout="wide",
)

initialize_database()

st.title("Invoice Processing Multi-Agent System")

email_content = st.text_area(
    "Incoming Email",
    height=250,
    placeholder="Paste test email here...",
)

if st.button("Classify Email"):

    if not email_content.strip():
        st.warning("Please enter an email.")
    else:
        crew = create_invoice_classification_crew()

        result = crew.kickoff(
            inputs={
                "email_content": email_content
            }
        )

        st.subheader("Agent 1 Result")
        st.write(result)
