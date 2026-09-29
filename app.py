
# import sqlite3
# from pathlib import Path

# import streamlit as st

# from tools.database_tool import initialize_database
# from crew.invoice_crew import create_invoice_processing_crew


# st.set_page_config(
#     page_title="Invoice Processing System",
#     layout="wide",
# )

# initialize_database()

# st.title("Invoice Processing Multi-Agent System")

# email_content = st.text_area(
#     "Incoming Email",
#     height=250,
#     placeholder="Paste invoice email here...",
# )


# if st.button("Run Invoice Workflow"):

#     if not email_content.strip():
#         st.warning("Please enter an email.")

#     else:
#         crew = create_invoice_processing_crew()

#         result = crew.kickoff(
#             inputs={
#                 "email_content": email_content
#             }
#         )

#         st.subheader("Workflow Result")
#         st.write(result)

#         # Database verification
#         database_path = (
#             Path(__file__).resolve().parent
#             / "database"
#             / "invoices.db"
#         )

#         connection = sqlite3.connect(database_path)

#         cursor = connection.cursor()

#         rows = cursor.execute(
#             """
#             SELECT
#                 invoice_id,
#                 vendor_name,
#                 invoice_number,
#                 po_number,
#                 total,
#                 extraction_status,
#                 verification_status,
#                 approval_status
#             FROM invoices
#             ORDER BY invoice_id DESC
#             LIMIT 5
#             """
#         ).fetchall()

#         connection.close()

#         st.subheader("Database Records")

#         if rows:
#             st.dataframe(
#                 rows,
#                 column_config={
#                     0: "Invoice ID",
#                     1: "Vendor",
#                     2: "Invoice Number",
#                     3: "PO Number",
#                     4: "Total",
#                     5: "Extraction Status",
#                     6: "Verification Status",
#                     7: "Approval Status",
#                 },
#                 use_container_width=True,
#             )
#         else:
#             st.info("No invoice records found in the database.")



import sqlite3
from pathlib import Path

import streamlit as st

from tools.database_tool import (
    initialize_database,
    create_approval_token,
)
from crew.invoice_crew import (
    create_invoice_processing_crew,
    create_approval_processing_crew,
)


st.set_page_config(
    page_title="Invoice Processing System",
    layout="wide",
)

initialize_database()


st.title("Invoice Processing Multi-Agent System")


# ============================================================
# INCOMING EMAIL
# ============================================================

email_content = st.text_area(
    "Incoming Email",
    height=250,
    placeholder="Paste invoice email here...",
)


# ============================================================
# RUN INVOICE WORKFLOW
# ============================================================

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

        # ----------------------------------------------------
        # Generate approval token for latest pending invoice
        # ----------------------------------------------------

        database_path = (
            Path(__file__).resolve().parent
            / "database"
            / "invoices.db"
        )

        connection = sqlite3.connect(database_path)

        cursor = connection.cursor()

        latest_invoice = cursor.execute(
            """
            SELECT
                invoice_id,
                vendor_name,
                invoice_number,
                po_number,
                total,
                approval_status
            FROM invoices
            ORDER BY invoice_id DESC
            LIMIT 1
            """
        ).fetchone()

        connection.close()

        if latest_invoice:

            invoice_id = latest_invoice[0]
            approval_status = latest_invoice[5]

            if approval_status == "PENDING":

                token = create_approval_token(invoice_id)

                if token:

                    st.success(
                        f"Approval token generated for Invoice ID "
                        f"{invoice_id}."
                    )

                    st.code(
                        token,
                        language="text",
                    )

                    st.info(
                        "Use this token in the Manager Approval section."
                    )

                else:

                    st.warning(
                        "Could not generate approval token."
                    )


        # ----------------------------------------------------
        # Database verification
        # ----------------------------------------------------

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

            st.info(
                "No invoice records found in the database."
            )


# ============================================================
# MANAGER APPROVAL
# ============================================================

st.divider()

st.header("Manager Approval")


database_path = (
    Path(__file__).resolve().parent
    / "database"
    / "invoices.db"
)


connection = sqlite3.connect(database_path)

cursor = connection.cursor()

pending_invoices = cursor.execute(
    """
    SELECT
        invoice_id,
        vendor_name,
        invoice_number,
        po_number,
        total,
        currency,
        approval_status
    FROM invoices
    WHERE approval_status = 'PENDING'
    ORDER BY invoice_id DESC
    """
).fetchall()

connection.close()


if pending_invoices:

    st.subheader("Pending Invoices")

    st.dataframe(
        pending_invoices,
        column_config={
            0: "Invoice ID",
            1: "Vendor",
            2: "Invoice Number",
            3: "PO Number",
            4: "Total",
            5: "Currency",
            6: "Approval Status",
        },
        use_container_width=True,
    )

    invoice_options = {
        f"Invoice {row[0]} - {row[2]}": row[0]
        for row in pending_invoices
    }

    selected_invoice = st.selectbox(
        "Select Invoice",
        options=list(invoice_options.keys()),
    )

    selected_invoice_id = invoice_options[selected_invoice]

    approval_token = st.text_input(
        "Approval Token",
        type="password",
        placeholder="Enter approval token...",
    )

    col1, col2 = st.columns(2)


    # ========================================================
    # APPROVE
    # ========================================================

    with col1:

        if st.button(
            "Approve Invoice",
            use_container_width=True,
        ):

            if not approval_token.strip():

                st.warning(
                    "Please enter the approval token."
                )

            else:

                approval_crew = (
                    create_approval_processing_crew()
                )

                approval_result = approval_crew.kickoff(
                    inputs={
                        "invoice_id": selected_invoice_id,
                        "approval_token": approval_token.strip(),
                        "approval_status": "APPROVED",
                    }
                )

                st.subheader("Approval Result")

                st.write(approval_result)

                st.rerun()


    # ========================================================
    # REJECT
    # ========================================================

    with col2:

        if st.button(
            "Reject Invoice",
            use_container_width=True,
        ):

            if not approval_token.strip():

                st.warning(
                    "Please enter the approval token."
                )

            else:

                approval_crew = (
                    create_approval_processing_crew()
                )

                approval_result = approval_crew.kickoff(
                    inputs={
                        "invoice_id": selected_invoice_id,
                        "approval_token": approval_token.strip(),
                        "approval_status": "REJECTED",
                    }
                )

                st.subheader("Approval Result")

                st.write(approval_result)

                st.rerun()


else:

    st.info(
        "No pending invoices available for manager approval."
    )



