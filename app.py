
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
# DATABASE HELPERS
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
            invoice_date,
            due_date,
            currency,
            po_number,
            items,
            subtotal,
            tax,
            shipping,
            total,
            payment_terms,
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
            invoice_number,
            vendor_name,
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

    return [
        {
            "Invoice ID": row[0],
            "Invoice Number": row[1],
            "Vendor": row[2],
            "PO Number": row[3],
            "Total": row[4],
            "Currency": row[5],
            "Approval Status": row[6],
        }
        for row in rows
    ]


def get_recent_invoices():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    rows = cursor.execute(
        """
        SELECT
            invoice_id,
            invoice_number,
            vendor_name,
            po_number,
            total,
            currency,
            extraction_status,
            verification_status,
            approval_status
        FROM invoices
        ORDER BY invoice_id DESC
        LIMIT 5
        """
    ).fetchall()

    connection.close()

    return [
        {
            "Invoice ID": row[0],
            "Invoice Number": row[1],
            "Vendor": row[2],
            "PO Number": row[3],
            "Total": row[4],
            "Currency": row[5],
            "Extraction Status": row[6],
            "Verification Status": row[7],
            "Approval Status": row[8],
        }
        for row in rows
    ]


def get_approval_invoices():
    """
    Get all invoices for the Manager Approval section.

    Previously approved/rejected invoices remain visible so
    their current status can be checked and duplicate approval
    attempts can be tested.
    """

    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    rows = cursor.execute(
        """
        SELECT
            invoice_id,
            invoice_number,
            vendor_name,
            po_number,
            total,
            currency,
            approval_status
        FROM invoices
        ORDER BY invoice_id DESC
        """
    ).fetchall()

    connection.close()

    return [
        {
            "Invoice ID": row[0],
            "Invoice Number": row[1],
            "Vendor": row[2],
            "PO Number": row[3],
            "Total": row[4],
            "Currency": row[5],
            "Approval Status": row[6],
        }
        for row in rows
    ]


# ============================================================
# ITEM HELPERS
# ============================================================

def normalize_items(items):
    """
    Normalize invoice items so the UI can handle the expected
    list-of-dictionaries structure.

    Expected structure:

    [
        {
            "item_description": "Mouse",
            "quantity": 20,
            "unit_price": 50,
            "subtotal": 1000
        }
    ]
    """

    if not items:
        return []

    # If items is stored as JSON text in the database
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except (json.JSONDecodeError, TypeError):
            return []

    # Make sure items is a list
    if not isinstance(items, list):
        return []

    normalized_rows = []

    for item in items:

        # Handle dictionary-based item structure
        if isinstance(item, dict):

            item_description = (
                item.get("item_description")
                or item.get("description")
                or item.get("item")
                or item.get("name")
                or "UNKNOWN"
            )

            quantity = item.get(
                "quantity",
                "UNKNOWN",
            )

            unit_price = item.get(
                "unit_price",
                "UNKNOWN",
            )

            line_total = item.get(
                "line_total",
                item.get(
                    "subtotal",
                    "UNKNOWN",
                ),
            )

            normalized_rows.append(
                {
                    "Item": item_description,
                    "Quantity": quantity,
                    "Unit Price": unit_price,
                    "Line Total": line_total,
                }
            )

        # Handle simple string item structure
        elif isinstance(item, str):

            normalized_rows.append(
                {
                    "Item": item,
                    "Quantity": "UNKNOWN",
                    "Unit Price": "UNKNOWN",
                    "Line Total": "UNKNOWN",
                }
            )

    return normalized_rows


# ============================================================
# CREWAI RESULT HELPERS
# ============================================================

def extract_task_results(crew_result):
    """
    Extract JSON results from all CrewAI tasks.
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

            if isinstance(data, dict):
                task_results.append(data)

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            continue

    return task_results


def find_result_by_key(task_results, key):
    """
    Find a task result containing the requested key.
    """

    for result in task_results:

        if key in result:
            return result

    return None


# ============================================================
# DISPLAY WORKFLOW RESULTS
# ============================================================

def display_workflow_results(crew_result):

    task_results = extract_task_results(
        crew_result
    )

    st.subheader(
        "Workflow Result"
    )


    # ========================================================
    # AGENT 1
    # ========================================================

    classification_result = find_result_by_key(
        task_results,
        "classification",
    )

    if classification_result:

        st.write(
            "### Agent 1 — Email Classification"
        )

        classification = classification_result.get(
            "classification",
            "UNKNOWN",
        )

        reason = classification_result.get(
            "reason",
            "",
        )

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

            st.error(
                "Security Flags"
            )

            st.json(
                security_flags
            )


    # ========================================================
    # AGENT 2
    # ========================================================

    extraction_result = find_result_by_key(
        task_results,
        "extraction_status",
    )

    if extraction_result:

        st.write(
            "### Agent 2 — Invoice Extraction"
        )

        extraction_status = extraction_result.get(
            "extraction_status",
            "UNKNOWN",
        )

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

            st.write(
                "**Extracted Invoice Details**"
            )


            # ------------------------------------------------
            # Basic invoice information
            # ------------------------------------------------

            invoice_columns = [

                {
                    "Field": "Vendor",
                    "Value": extracted_data.get(
                        "vendor",
                        extracted_data.get(
                            "vendor_name",
                            "UNKNOWN",
                        ),
                    ),
                },

                {
                    "Field": "Invoice Number",
                    "Value": extracted_data.get(
                        "invoice_number",
                        "UNKNOWN",
                    ),
                },

                {
                    "Field": "Invoice Date",
                    "Value": extracted_data.get(
                        "invoice_date",
                        "UNKNOWN",
                    ),
                },

                {
                    "Field": "Due Date",
                    "Value": extracted_data.get(
                        "due_date",
                        "UNKNOWN",
                    ),
                },

                {
                    "Field": "PO Number",
                    "Value": extracted_data.get(
                        "po_number",
                        extracted_data.get(
                            "PO_number",
                            "UNKNOWN",
                        ),
                    ),
                },

                {
                    "Field": "Currency",
                    "Value": extracted_data.get(
                        "currency",
                        "UNKNOWN",
                    ),
                },

                {
                    "Field": "Subtotal",
                    "Value": extracted_data.get(
                        "subtotal",
                        "UNKNOWN",
                    ),
                },

                {
                    "Field": "Tax",
                    "Value": extracted_data.get(
                        "tax",
                        "UNKNOWN",
                    ),
                },

                {
                    "Field": "Shipping",
                    "Value": extracted_data.get(
                        "shipping",
                        "UNKNOWN",
                    ),
                },

                {
                    "Field": "Total",
                    "Value": extracted_data.get(
                        "total",
                        "UNKNOWN",
                    ),
                },

                {
                    "Field": "Payment Terms",
                    "Value": extracted_data.get(
                        "payment_terms",
                        "UNKNOWN",
                    ),
                },
            ]

            st.dataframe(
                invoice_columns,
                use_container_width=True,
                hide_index=True,
            )


            # ------------------------------------------------
            # Invoice Items
            # ------------------------------------------------

            items = extracted_data.get(
                "items",
                [],
            )

            item_rows = normalize_items(
                items
            )

            if item_rows:

                st.write(
                    "**Invoice Items**"
                )

                st.dataframe(
                    item_rows,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.warning(
                    "No invoice items were extracted."
                )


        uncertain_fields = extraction_result.get(
            "uncertain_fields",
            [],
        )

        if uncertain_fields:

            st.warning(
                "Uncertain Fields"
            )

            st.json(
                uncertain_fields
            )


        security_flags = extraction_result.get(
            "security_flags",
            [],
        )

        if security_flags:

            st.error(
                "Security Flags"
            )

            st.json(
                security_flags
            )


    # ========================================================
    # AGENT 3
    # ========================================================

    matching_result = find_result_by_key(
        task_results,
        "comparison",
    )

    if matching_result:

        st.write(
            "### Agent 3 — Purchase Order Matching"
        )

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


        # ----------------------------------------------------
        # Matching status
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # Invoice / PO IDs
        # ----------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Invoice ID:** {invoice_id}"
            )

        with col2:

            st.write(
                f"**PO ID:** {po_id}"
            )


        # ----------------------------------------------------
        # Comparison
        # ----------------------------------------------------

        if comparison:

            comparison_rows = []

            for field, value in comparison.items():

                comparison_rows.append(
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
                )

            st.dataframe(
                comparison_rows,
                use_container_width=True,
                hide_index=True,
            )


        # ----------------------------------------------------
        # Mismatches
        # ----------------------------------------------------

        if mismatches:

            st.write(
                "**Mismatches**"
            )

            st.json(
                mismatches
            )

        else:

            st.write(
                "**Mismatches:** None"
            )


        # ----------------------------------------------------
        # Reason
        # ----------------------------------------------------

        if reason:

            st.write(
                f"**Reason:** {reason}"
            )


        # ----------------------------------------------------
        # Security flags
        # ----------------------------------------------------

        if security_flags:

            st.error(
                "Security Flags"
            )

            st.json(
                security_flags
            )

        else:

            st.write(
                "**Security Flags:** None"
            )


    # ========================================================
    # DATABASE STATUS
    # ========================================================

    latest_invoice = get_latest_invoice()

    if latest_invoice:

        st.write(
            "### Database Status"
        )

        st.success(
            "Invoice record created successfully."
        )


        database_rows = [

            {
                "Field": "Invoice ID",
                "Value": latest_invoice[0],
            },

            {
                "Field": "Vendor",
                "Value": latest_invoice[1],
            },

            {
                "Field": "Invoice Number",
                "Value": latest_invoice[2],
            },

            {
                "Field": "Invoice Date",
                "Value": latest_invoice[3],
            },

            {
                "Field": "Due Date",
                "Value": latest_invoice[4],
            },

            {
                "Field": "Currency",
                "Value": latest_invoice[5],
            },

            {
                "Field": "PO Number",
                "Value": latest_invoice[6],
            },

            {
                "Field": "Subtotal",
                "Value": latest_invoice[8],
            },

            {
                "Field": "Tax",
                "Value": latest_invoice[9],
            },

            {
                "Field": "Shipping",
                "Value": latest_invoice[10],
            },

            {
                "Field": "Total",
                "Value": latest_invoice[11],
            },

            {
                "Field": "Payment Terms",
                "Value": latest_invoice[12],
            },

            {
                "Field": "Extraction Status",
                "Value": latest_invoice[13],
            },

            {
                "Field": "Verification Status",
                "Value": latest_invoice[14],
            },

            {
                "Field": "Approval Status",
                "Value": latest_invoice[15],
            },
        ]

        st.dataframe(
            database_rows,
            use_container_width=True,
            hide_index=True,
        )


        # ----------------------------------------------------
        # Database Invoice Items
        # ----------------------------------------------------

        database_items = normalize_items(
            latest_invoice[7]
        )

        if database_items:

            st.write(
                "**Database Invoice Items**"
            )

            st.dataframe(
                database_items,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.warning(
                "No invoice items found in the database."
            )


# ============================================================
# TITLE
# ============================================================

st.title(
    "Invoice Processing Multi-Agent System"
)

st.caption(
    "Automated invoice classification, extraction, "
    "purchase-order matching, and manager approval."
)


# ============================================================
# INCOMING EMAIL
# ============================================================

email_content = st.text_area(
    "Incoming Invoice Email",
    height=300,
    placeholder="Paste invoice email here...",
)


# ============================================================
# RUN WORKFLOW
# ============================================================

if st.button(
    "Run Invoice Workflow",
    use_container_width=True,
):

    if not email_content.strip():

        st.warning(
            "Please enter an invoice email."
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

        display_workflow_results(
            result
        )


        # ----------------------------------------------------
        # Recent Database Records
        # ----------------------------------------------------

        rows = get_recent_invoices()

        st.subheader(
            "Database Records"
        )

        if rows:

            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No invoice records found."
            )


# ============================================================
# MANAGER APPROVAL
# ============================================================

st.divider()

st.header(
    "Manager Approval"
)


approval_invoices = get_approval_invoices()


if approval_invoices:

    st.subheader(
        "Invoices"
    )


    # --------------------------------------------------------
    # All invoices table
    # --------------------------------------------------------

    st.dataframe(
        approval_invoices,
        use_container_width=True,
        hide_index=True,
    )


    # --------------------------------------------------------
    # Select Invoice
    # --------------------------------------------------------

    invoice_options = {
        (
            f"Invoice {row['Invoice ID']} — "
            f"{row['Invoice Number']} — "
            f"{row['Vendor']} — "
            f"{row['Total']} {row['Currency']} — "
            f"{row['Approval Status']}"
        ):
        row["Invoice ID"]
        for row in approval_invoices
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


    # Find the complete selected invoice record.
    selected_invoice_data = next(
        row
        for row in approval_invoices
        if row["Invoice ID"] == selected_invoice_id
    )


    st.write(
        f"**Selected Invoice ID:** "
        f"{selected_invoice_id}"
    )


    st.write(
        f"**Current Approval Status:** "
        f"{selected_invoice_data['Approval Status']}"
    )


    # ========================================================
    # APPROVAL TOKEN
    # ========================================================

    st.write(
        "### Approval Token"
    )


    if st.button(
        "Generate Approval Token",
        use_container_width=True,
    ):

        current_status = (
            selected_invoice_data[
                "Approval Status"
            ]
        )


        if current_status != "PENDING":

            st.warning(
                f"Invoice {selected_invoice_id} is already "
                f"{current_status}. "
                "A new approval token cannot be generated."
            )

        else:

            token = create_approval_token(
                selected_invoice_id
            )


            if token:

                st.success(
                    f"Approval token generated for "
                    f"Invoice ID {selected_invoice_id}."
                )

                st.code(
                    token,
                    language="text",
                )

                st.info(
                    "Copy this token and enter it below."
                )

            else:

                st.error(
                    "Could not generate approval token."
                )


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
                                "invoice_id": selected_invoice_id,
                                "approval_token": (
                                    approval_token.strip()
                                ),
                                "approval_status": "APPROVED",
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
                                "invoice_id": selected_invoice_id,
                                "approval_token": (
                                    approval_token.strip()
                                ),
                                "approval_status": "REJECTED",
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


else:

    st.info(
        "No invoices available."
    )

