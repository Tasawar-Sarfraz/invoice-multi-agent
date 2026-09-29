
import json
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
# DATABASE PATH
# ============================================================

database_path = (
    Path(__file__).resolve().parent
    / "database"
    / "invoices.db"
)


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

        # ----------------------------------------------------
        # Extract only the final workflow result
        # ----------------------------------------------------

        workflow_raw = getattr(result, "raw", "")

        try:
            workflow_data = json.loads(workflow_raw)
        except (json.JSONDecodeError, TypeError):
            workflow_data = None

        st.subheader("Workflow Result")

        if workflow_data:

            status = workflow_data.get("status", "UNKNOWN")
            invoice_id = workflow_data.get("invoice_id", "UNKNOWN")
            po_id = workflow_data.get("po_id", "UNKNOWN")
            comparison = workflow_data.get("comparison", {})
            mismatches = workflow_data.get("mismatches", [])
            reason = workflow_data.get("reason", "")
            security_flags = workflow_data.get(
                "security_flags",
                [],
            )

            # ------------------------------------------------
            # Status
            # ------------------------------------------------

            if status == "MATCH":
                st.success(f"Status: {status}")

            elif status in {
                "MISMATCH",
                "SECURITY_ALERT",
            }:
                st.error(f"Status: {status}")

            else:
                st.warning(f"Status: {status}")

            # ------------------------------------------------
            # Basic information
            # ------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Invoice ID:** {invoice_id}")

            with col2:
                st.write(f"**PO ID:** {po_id}")

            # ------------------------------------------------
            # Comparison
            # ------------------------------------------------

            if comparison:

                st.write("**Comparison**")

                comparison_rows = [
                    {
                        "Field": field.replace("_", " ").title(),
                        "Result": "MATCHED" if value else "NOT MATCHED",
                    }
                    for field, value in comparison.items()
                ]

                st.dataframe(
                    comparison_rows,
                    use_container_width=True,
                    hide_index=True,
                )

            # ------------------------------------------------
            # Mismatches
            # ------------------------------------------------

            if mismatches:

                st.write("**Mismatches**")
                st.json(mismatches)

            else:

                st.write("**Mismatches:** None")

            # ------------------------------------------------
            # Reason
            # ------------------------------------------------

            if reason:
                st.write(f"**Reason:** {reason}")

            # ------------------------------------------------
            # Security flags
            # ------------------------------------------------

            if security_flags:

                st.error("Security Flags Detected")

                st.json(security_flags)

            else:

                st.write("**Security Flags:** None")

        else:

            st.warning(
                "Workflow completed, but the final result "
                "could not be parsed."
            )

            st.write(workflow_raw)


        # ====================================================
        # GENERATE APPROVAL TOKEN
        # ====================================================

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
                        f"Approval token generated for "
                        f"Invoice ID {invoice_id}."
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


        # ====================================================
        # DATABASE VERIFICATION
        # ====================================================

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
                hide_index=True,
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


# ============================================================
# GET PENDING INVOICES
# ============================================================

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
        hide_index=True,
    )


    # ========================================================
    # SELECT INVOICE
    # ========================================================

    invoice_options = {
        f"Invoice {row[0]} - {row[2]}": row[0]
        for row in pending_invoices
    }

    selected_invoice = st.selectbox(
        "Select Invoice",
        options=list(invoice_options.keys()),
    )

    selected_invoice_id = invoice_options[selected_invoice]


    # ========================================================
    # APPROVAL TOKEN
    # ========================================================

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

                # --------------------------------------------
                # Show only clean approval result
                # --------------------------------------------

                approval_raw = getattr(
                    approval_result,
                    "raw",
                    "",
                )

                st.subheader("Approval Result")

                try:
                    approval_data = json.loads(approval_raw)
                except (json.JSONDecodeError, TypeError):
                    approval_data = None

                if approval_data:

                    database_update = approval_data.get(
                        "database_update",
                        "UNKNOWN",
                    )

                    if database_update == "SUCCESS":

                        st.success(
                            "Invoice approved successfully."
                        )

                    elif database_update == "NOT_PERMITTED":

                        st.error(
                            "Approval was not permitted."
                        )

                    else:

                        st.warning(
                            "Approval processing failed."
                        )

                    st.write(
                        f"**Invoice ID:** "
                        f"{approval_data.get('invoice_id', 'UNKNOWN')}"
                    )

                    st.write(
                        f"**Approval Status:** "
                        f"{approval_data.get('approval_status', 'UNKNOWN')}"
                    )

                    st.write(
                        f"**Database Update:** "
                        f"{database_update}"
                    )

                    st.write(
                        f"**Reason:** "
                        f"{approval_data.get('reason', '')}"
                    )

                    security_flags = approval_data.get(
                        "security_flags",
                        [],
                    )

                    if security_flags:
                        st.error("Security Flags")
                        st.json(security_flags)

                else:

                    st.warning(
                        "Approval processing completed, "
                        "but the result could not be parsed."
                    )

                    st.write(approval_raw)

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

                # --------------------------------------------
                # Show only clean approval result
                # --------------------------------------------

                approval_raw = getattr(
                    approval_result,
                    "raw",
                    "",
                )

                st.subheader("Approval Result")

                try:
                    approval_data = json.loads(approval_raw)
                except (json.JSONDecodeError, TypeError):
                    approval_data = None

                if approval_data:

                    database_update = approval_data.get(
                        "database_update",
                        "UNKNOWN",
                    )

                    if database_update == "SUCCESS":

                        st.success(
                            "Invoice rejected successfully."
                        )

                    elif database_update == "NOT_PERMITTED":

                        st.error(
                            "Rejection was not permitted."
                        )

                    else:

                        st.warning(
                            "Rejection processing failed."
                        )

                    st.write(
                        f"**Invoice ID:** "
                        f"{approval_data.get('invoice_id', 'UNKNOWN')}"
                    )

                    st.write(
                        f"**Approval Status:** "
                        f"{approval_data.get('approval_status', 'UNKNOWN')}"
                    )

                    st.write(
                        f"**Database Update:** "
                        f"{database_update}"
                    )

                    st.write(
                        f"**Reason:** "
                        f"{approval_data.get('reason', '')}"
                    )

                    security_flags = approval_data.get(
                        "security_flags",
                        [],
                    )

                    if security_flags:
                        st.error("Security Flags")
                        st.json(security_flags)

                else:

                    st.warning(
                        "Approval processing completed, "
                        "but the result could not be parsed."
                    )

                    st.write(approval_raw)

                st.rerun()


else:

    st.info(
        "No pending invoices available for manager approval."
    )

