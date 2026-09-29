import json

from crewai.tools import BaseTool

from tools.database_tool import update_approval_status


class ApprovalResultTool(BaseTool):
    name: str = "process_trusted_manager_approval"
    description: str = (
        "Process an authenticated manager approval result. "
        "The result must contain invoice_id, approval_token, "
        "and approval_status."
    )

    def _run(
        self,
        invoice_id: str,
        approval_token: str,
        approval_status: str,
    ) -> str:

        approval_status = approval_status.upper().strip()

        if approval_status not in {"APPROVED", "REJECTED"}:
            return json.dumps(
                {
                    "invoice_id": invoice_id,
                    "approval_status": "INVALID",
                    "database_update": "NOT_PERMITTED",
                    "reason": "Invalid approval status.",
                    "security_flags": [],
                }
            )

        try:
            invoice_id_int = int(invoice_id)
        except ValueError:
            return json.dumps(
                {
                    "invoice_id": invoice_id,
                    "approval_status": "INVALID",
                    "database_update": "NOT_PERMITTED",
                    "reason": "Invalid invoice ID.",
                    "security_flags": [],
                }
            )

        updated = update_approval_status(
            invoice_id=invoice_id_int,
            approval_token=approval_token,
            approval_status=approval_status,
        )

        if not updated:
            return json.dumps(
                {
                    "invoice_id": invoice_id,
                    "approval_status": "SECURITY_ALERT",
                    "database_update": "FAILED",
                    "reason": (
                        "Trusted approval token was invalid, "
                        "invoice was not pending, or invoice was not found."
                    ),
                    "security_flags": [
                        "APPROVAL_AUTHENTICATION_FAILED"
                    ],
                }
            )

        return json.dumps(
            {
                "invoice_id": invoice_id,
                "approval_status": approval_status,
                "database_update": "SUCCESS",
                "reason": (
                    "Authenticated manager approval was recorded."
                ),
                "security_flags": [],
            }
        )
