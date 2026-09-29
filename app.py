
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


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Invoice Processing System",
    layout="wide",
)


# ============================================================
# DATABASE
# ============================================================

initialize_database()

database_path = (
    Path(__file__).resolve().parent
    / "database"
    / "invoices.db"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_latest_invoice():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    row = cursor.execute(
        """
        SELECT
            invoice_id,
            vendor_name,
            invoice_number,
            po_number,
            total,
            currency,
            extraction_status,
            verification_status,
            approval_status
        FROM invoices
        ORDER BY invoice_id DESC
        LIMIT 1
        """
    ).fetchone()

    connection.close()

    return row


def get_pending_invoices():
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
            currency,
            approval_status
        FROM invoices
        WHERE approval_status = 'PENDING'
        ORDER BY invoice_id DESC
        """
    ).fetchall()

    connection.close()

    return rows


def get_recent_invoices():
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

    return rows


def extract_task_results(crew_result):
    """
    Extract raw outputs from all CrewAI tasks.
    """

    task_results = []

    tasks_output = getattr(
        crew_result,
        "tasks_output",
        [],
    )

    for task_output in tasks_output:

        raw = getattr(
            task_output,
            "raw",
            "",
        )

        if not raw:
            continue

        try:
            data = json.loads(raw)
            task_results.append(data)

        except (json.JSONDecodeError, TypeError):
            continue

    return task_results


def find_result_by_key(task_results, key):
    """
    Find a task result containing a specific key.
    """

    for result in task_results:

        if key in result:
            return result

    return None


def display_workflow_results(crew_result):
    """
    Display clean results from Agent 1, Agent 2 and Agent 3.
    """

    task_results = extract_task_results(crew_result)

    st.subheader("Workflow Result")

    # --------------------------------------------------------
    # Agent 1
    # --------------------------------------------------------

    classification_result = find_result_by_key(
        task_results,
        "classification",
    )

    if classification_result:

        classification = classification_result.get(
            "classification",
            "UNKNOWN",
        )

        reason = classification_result.get(
            "reason",
            "",
        )

        st.write("### Agent 1 — Email Classification")

        if classification == "INVOICE":
            st.success(
                f"Classification: {classification}"
            )

        elif classification == "SECURITY_ALERT":
            st.error(
                f"Classification: {classification}"
            )

        else:
            st.warning(
                f"Classification: {classification}"
            )

        if reason:
            st.write(
                f"**Reason:** {reason}"
            )

        security_flags = classification_result.get(
            "security_flags",
            [],
        )

        if security_flags:
            st.error("Security Flags")
            st.json(security_flags)

    # --------------------------------------------------------
    # Agent 2
    # --------------------------------------------------------

    extraction_result = find_result_by_key(
        task_results,
        "extraction_status",
    )

    if extraction_result:

        extraction_status = extraction_result.get(
            "extraction_status",
            "UNKNOWN",
        )

        st.write("### Agent 2 — Invoice Extraction")

        if extraction_status == "SUCCESS":
            st.success(
                f"Extraction Status: {extraction_status}"
            )
        else:
            st.warning(
                f"Extraction Status: {extraction_status}"
            )

        invoice_record_id = extraction_result.get(
            "invoice_record_id",
            "UNKNOWN",
        )

        st.write(
            f"**Invoice Record ID:** {invoice_record_id}"
        )

        extracted_data = extraction_result.get(
            "extracted_data",
            {},
        )

        if extracted_data:

            st.write("**Extracted Invoice Data**")

            st.json(extracted_data)

        uncertain_fields = extraction_result.get(
            "uncertain_fields",
            [],
        )

        if uncertain_fields:

            st.warning("Uncertain Fields")

            st.json(uncertain_fields)

        security_flags = extraction_result.get(
            "security_flags",
            [],
        )

        if security_flags:

            st.error("Security Flags")

            st.json(security_flags)

    # --------------------------------------------------------
    # Agent 3
    # --------------------------------------------------------

    matching_result = find_result_by_key(
        task_results,
        "comparison",
    )

    if matching_result:

        status = matching_result.get(
            "status",
            "UNKNOWN",
        )

        invoice_id = matching_result.get(
            "invoice_id",
            "UNKNOWN",
        )

        po_id = matching_result.get(
            "po_id",
            "UNKNOWN",
        )

        comparison = matching_result.get(
            "comparison",
            {},
        )

        mismatches = matching_result.get(
            "mismatches",
            [],
        )

        reason = matching_result.get(
            "reason",
            "",
        )

        security_flags = matching_result.get(
            "security_flags",
            [],
        )

        st.write("### Agent 3 — PO Matching")

        if status == "MATCH":
            st.success(
                f"PO Matching Status: {status}"
            )

        elif status in {
            "MISMATCH",
            "SECURITY_ALERT",
        }:
            st.error(
                f"PO Matching Status: {status}"
            )

        else:
            st.warning(
                f"PO Matching Status: {status}"
            )

        col1, col2 = st.columns(2)

        with col1:
            st.write(
                f"**Invoice ID:** {invoice_id}"
            )

        with col2:
            st.write(
                f"**PO ID:** {po_id}"
            )

        if comparison:

            comparison_rows = [
                {
                    "Field": field.replace(
                        "_",
                        " ",
                    ).title(),
                    "Result": (
                        "MATCHED"
                        if value
                        else "NOT MATCHED"
                    ),
                }
                for field, value in comparison.items()
            ]

            st.dataframe(
                comparison_rows,
                use_container_width=True,
                hide_index=True,
            )

        if mismatches:

            st.write("**Mismatches**")

            st.json(mismatches)

        else:

            st.write("**Mismatches:** None")

        if reason:

            st.write(
                f"**Reason:** {reason}"
            )

        if security_flags:

            st.error("Security Flags")

            st.json(security_flags)

        else:

            st.write(
                "**Security Flags:** None"
            )

    # --------------------------------------------------------
    # Database Status
    # --------------------------------------------------------

    latest_invoice = get_latest_invoice()

    if latest_invoice:

        st.write("### Database Status")

        st.success(
            "Invoice record created successfully."
        )

        st.write(
            f"**Invoice ID:** {latest_invoice[0]}"
        )

        st.write(
            f"**Invoice Number:** {latest_invoice[2]}"
        )

        st.write(
            f"**Approval Status:** {latest_invoice[8]}"
        )


# ============================================================
# TITLE
# ============================================================

st.title(
    "Invoice Processing Multi-Agent System"
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

if st.button(
    "Run Invoice Workflow",
    use_container_width=True,
):

    if not email_content.strip():

        st.warning(
            "Please enter an email."
        )

    else:

        with st.spinner(
            "Running invoice processing workflow..."
        ):

            crew = create_invoice_processing_crew()

            result = crew.kickoff(
                inputs={
                    "email_content": email_content
                }
            )

        # ----------------------------------------------------
        # Display all task results
        # ----------------------------------------------------

        display_workflow_results(result)

        # ----------------------------------------------------
        # Generate approval token for latest PENDING invoice
        # ----------------------------------------------------

        latest_invoice = get_latest_invoice()

        if latest_invoice:

            latest_invoice_id = latest_invoice[0]
            approval_status = latest_invoice[8]

            if approval_status == "PENDING":

                token = create_approval_token(
                    latest_invoice_id
                )

                if token:

                    st.success(
                        f"Approval token generated for "
                        f"Invoice ID {latest_invoice_id}."
                    )

                    st.code(
                        token,
                        language="text",
                    )

                    st.info(
                        "Copy this token and use it in "
                        "the Manager Approval section."
                    )

                else:

                    st.warning(
                        "Could not generate approval token."
                    )

        # ----------------------------------------------------
        # Database records
        # ----------------------------------------------------

        rows = get_recent_invoices()

        st.subheader(
            "Database Records"
        )

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

st.header(
    "Manager Approval"
)


# ============================================================
# PENDING INVOICES
# ============================================================

pending_invoices = get_pending_invoices()


if pending_invoices:

    st.subheader(
        "Pending Invoices"
    )

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

    # --------------------------------------------------------
    # Select Invoice
    # --------------------------------------------------------

    invoice_options = {
        f"Invoice {row[0]} - {row[2]}": row[0]
        for row in pending_invoices
    }

    selected_invoice = st.selectbox(
        "Select Invoice",
        options=list(
            invoice_options.keys()
        ),
    )

    selected_invoice_id = invoice_options[
        selected_invoice
    ]

    # --------------------------------------------------------
    # Generate Approval Token
    # --------------------------------------------------------

   

       

           
    # --------------------------------------------------------
    # Enter Approval Token
    # --------------------------------------------------------

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

                with st.spinner(
                    "Processing approval..."
                ):

                    approval_crew = (
                        create_approval_processing_crew()
                    )

                    approval_result = (
                        approval_crew.kickoff(
                            inputs={
                                "invoice_id": (
                                    selected_invoice_id
                                ),
                                "approval_token": (
                                    approval_token.strip()
                                ),
                                "approval_status": (
                                    "APPROVED"
                                ),
                            }
                        )
                    )

                approval_raw = getattr(
                    approval_result,
                    "raw",
                    "",
                )

                st.subheader(
                    "Approval Result"
                )

                try:

                    approval_data = json.loads(
                        approval_raw
                    )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):

                    approval_data = None

                if approval_data:

                    database_update = (
                        approval_data.get(
                            "database_update",
                            "UNKNOWN",
                        )
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

                    security_flags = (
                        approval_data.get(
                            "security_flags",
                            [],
                        )
                    )

                    if security_flags:

                        st.error(
                            "Security Flags"
                        )

                        st.json(
                            security_flags
                        )

                else:

                    st.warning(
                        "Approval processing completed, "
                        "but the result could not be parsed."
                    )

                    st.write(
                        approval_raw
                    )

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

                with st.spinner(
                    "Processing rejection..."
                ):

                    approval_crew = (
                        create_approval_processing_crew()
                    )

                    approval_result = (
                        approval_crew.kickoff(
                            inputs={
                                "invoice_id": (
                                    selected_invoice_id
                                ),
                                "approval_token": (
                                    approval_token.strip()
                                ),
                                "approval_status": (
                                    "REJECTED"
                                ),
                            }
                        )
                    )

                approval_raw = getattr(
                    approval_result,
                    "raw",
                    "",
                )

                st.subheader(
                    "Approval Result"
                )

                try:

                    approval_data = json.loads(
                        approval_raw
                    )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):

                    approval_data = None

                if approval_data:

                    database_update = (
                        approval_data.get(
                            "database_update",
                            "UNKNOWN",
                        )
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

                    security_flags = (
                        approval_data.get(
                            "security_flags",
                            [],
                        )
                    )

                    if security_flags:

                        st.error(
                            "Security Flags"
                        )

                        st.json(
                            security_flags
                        )

                else:

                    st.warning(
                        "Rejection processing completed, "
                        "but the result could not be parsed."
                    )

                    st.write(
                        approval_raw
                    )

                st.rerun()

else:

    st.info(
        "No pending invoices available "
        "for manager approval."
    )

