import streamlit as st

from tools.database_tool import initialize_database

from crew.invoice_crew import (
    create_invoice_classification_crew,
    create_invoice_extraction_crew,
    create_po_matching_crew,
)


st.set_page_config(
    page_title="Invoice Processing System",
    layout="wide",
)

initialize_database()

st.title("Invoice Processing Multi-Agent System")


email_content = st.text_area(
    "Incoming Email",
    height=200,
    placeholder="Paste test email here...",
)

if st.button("Run Agent 1"):

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


st.divider()


invoice_content = st.text_area(
    "Invoice Content",
    height=300,
    placeholder="Paste invoice text here...",
)

if st.button("Run Agent 2"):

    if not invoice_content.strip():
        st.warning("Please enter invoice content.")
    else:
        crew = create_invoice_extraction_crew()

        result = crew.kickoff(
            inputs={
                "invoice_content": invoice_content
            }
        )

        st.subheader("Agent 2 Result")
        st.write(result)


st.divider()


invoice_data = st.text_area(
    "Invoice Data for PO Matching",
    height=300,
    placeholder="Enter extracted invoice JSON here...",
)

if st.button("Run Agent 3"):

    if not invoice_data.strip():
        st.warning("Please enter invoice data.")
    else:
        crew = create_po_matching_crew()

        result = crew.kickoff(
            inputs={
                "invoice_data": invoice_data
            }
        )

        st.subheader("Agent 3 Result")
        st.write(result)
