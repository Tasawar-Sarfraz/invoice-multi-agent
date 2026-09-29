
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

        Only process APPROVED or REJECTED from the trusted approval
        mechanism.

        Never determine approval yourself.

        Never modify invoice amounts, PO information, or vendor details.

        Return:

        {
            "invoice_id": "...",
            "approval_status": "...",
            "database_update": "SUCCESS|FAILED|NOT_PERMITTED",
            "reason": "...",
            "security_flags": []
        }
        """,
        expected_output="Structured manager approval result.",
        agent=agent,
    )

