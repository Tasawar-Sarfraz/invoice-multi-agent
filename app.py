
import sqlite3
from pathlib import Path

import streamlit as st

from tools.database_tool import initialize_database
from crew.invoice_crew import create_invoice_processing_crew


st.set_page_config(
    page_title="Invoice Processing System",
    layout="wide",
)

initialize_database()

st.title("Invoice Processing Multi-Agent System")

email_content = st.text_area(
    "Incoming Email",
    height=250,
    placeholder="Paste invoice email here...",
)


if st.button("Run Invoice Workflow"):

    if not email_content.strip():
        st.warning("Please enter an email.")

    else:
        crew = create_invoice_processing_crew()

        result = crew.kickoff(
            inputs={
                "email_content": email_content
            }
        )

        st.subheader("Workflow Result")
        st.write(result)

        # Database verification
        database_path = (
            Path(__file__).resolve().parent
            / "database"
            / "invoices.db"
        )

        connection = sqlite3.connect(database_path)

        cursor = connection.cursor()

        rows = cursor.execute(
            """
            SELECT
                invoice_id,
                vendor_name,
                invoice_number,
                po_number,
                total,
                extraction_status,
                verification_status,
                approval_status
            FROM invoices
            ORDER BY invoice_id DESC
            LIMIT 5
            """
        ).fetchall()

        connection.close()

        st.subheader("Database Records")

        if rows:
            st.dataframe(
                rows,
                column_config={
                    0: "Invoice ID",
                    1: "Vendor",
                    2: "Invoice Number",
                    3: "PO Number",
                    4: "Total",
                    5: "Extraction Status",
                    6: "Verification Status",
                    7: "Approval Status",
                },
                use_container_width=True,
            )
        else:
            st.info("No invoice records found in the database.")




