from crewai import Task


def create_po_matching_task(agent, extraction_task):
    return Task(
        description="""
        Compare the extracted invoice with its corresponding Purchase Order.

        The invoice data comes from Agent 2.

        IMPORTANT:

        First read Agent 2's "extracted_data" object.

        Get the exact PO number from:

        extracted_data.po_number

        Do NOT invent a PO number.

        Do NOT use a PO number from your own knowledge.

        Do NOT search for a different PO number.

        If Agent 2 provides:

        "po_number": "PO-2002"

        then you MUST call the purchase order tool with exactly:

        PO-2002

        Use the purchase order tool to find that exact PO.

        After finding the PO, compare:

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

        Return exactly:

        {{
            "status": "...",
            "invoice_id": "...",
            "po_id": "...",
            "comparison": {{}},
            "mismatches": [],
            "reason": "...",
            "security_flags": []
        }}
        """,
        expected_output="Structured invoice and PO validation result.",
        agent=agent,
        context=[extraction_task],
    )
