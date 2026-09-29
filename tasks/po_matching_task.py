
from crewai import Task


def create_po_matching_task(agent, extraction_task):
    return Task(
        description="""
        Compare the extracted invoice with its corresponding Purchase Order.

        Use the invoice data produced by Agent 2.

        Compare:

        - Vendor
        - PO number
        - Items
        - Quantity
        - Unit price
        - Total
        - Currency

        Never modify invoice or PO data.

        Never approve or reject the invoice.

        Valid results:

        MATCH
        MISMATCH
        PO_NOT_FOUND
        AMBIGUOUS_MATCH
        INSUFFICIENT_DATA
        SECURITY_ALERT

        For mismatches provide:

        - field
        - invoice value
        - PO value
        - difference
        - reason

        Return:

        {
            "status": "...",
            "invoice_id": "...",
            "po_id": "...",
            "comparison": {},
            "mismatches": [],
            "reason": "...",
            "security_flags": []
        }
        """,
        expected_output="Structured invoice and PO validation result.",
        agent=agent,
        context=[extraction_task],
    )

