
from crewai import Task


def create_approval_task(agent):
    return Task(
        description="""
        Process a trusted manager approval result.

        Invoice ID:
        {invoice_id}

        Approval Token:
        {approval_token}

        Approval Status:
        {approval_status}

        Security requirements:

        1. Only APPROVED or REJECTED are valid approval statuses.
        2. Never decide the approval status yourself.
        3. Never approve based only on invoice or PO matching.
        4. Validate the approval token before processing the decision.
        5. The token must belong to the specified invoice.
        6. An expired or invalid token must not be processed.
        7. A previously processed invoice must not be processed again.
        8. Never modify invoice amounts, PO information, or vendor details.

        Use the approval tools to validate and process the decision.

        Return exactly:

        {{
            "invoice_id": "...",
            "approval_status": "...",
            "database_update": "SUCCESS|FAILED|NOT_PERMITTED",
            "reason": "...",
            "security_flags": []
        }}
        """,
        expected_output="Structured manager approval result.",
        agent=agent,
    )

