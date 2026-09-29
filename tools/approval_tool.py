
from crewai.tools import tool

from tools.database_tool import (
    create_approval_token,
    validate_approval_token,
    update_approval_status,
)


@tool("generate_approval_token")
def generate_approval_token_tool(invoice_id: int) -> str:
    """
    Generate a secure approval token for a pending invoice.

    The token is linked to the specific invoice and has
    a limited expiration time.
    """

    token = create_approval_token(invoice_id)

    if not token:
        return (
            f"FAILED: Could not generate approval token "
            f"for invoice {invoice_id}."
        )

    return token


@tool("validate_approval_token")
def validate_approval_token_tool(
    invoice_id: int,
    approval_token: str,
) -> str:
    """
    Validate an approval token before processing approval.
    """

    result = validate_approval_token(
        invoice_id=invoice_id,
        approval_token=approval_token,
    )

    if result["valid"]:
        return "VALID: Approval token is valid."

    return f"INVALID: {result['reason']}"


@tool("process_invoice_approval")
def process_invoice_approval_tool(
    invoice_id: int,
    approval_token: str,
    approval_status: str,
) -> str:
    """
    Process APPROVED or REJECTED status after token validation.
    """

    approval_status = approval_status.upper().strip()

    if approval_status not in {"APPROVED", "REJECTED"}:
        return (
            "FAILED: approval_status must be "
            "APPROVED or REJECTED."
        )

    validation = validate_approval_token(
        invoice_id=invoice_id,
        approval_token=approval_token,
    )

    if not validation["valid"]:
        return f"NOT_PERMITTED: {validation['reason']}"

    updated = update_approval_status(
        invoice_id=invoice_id,
        approval_token=approval_token,
        approval_status=approval_status,
    )

    if not updated:
        return (
            "FAILED: Database approval update "
            "could not be completed."
        )

    return (
        f"SUCCESS: Invoice {invoice_id} "
        f"has been marked as {approval_status}."
    )

