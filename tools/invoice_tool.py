
import json

from crewai.tools import BaseTool

from tools.database_tool import create_invoice_record


class SaveInvoiceTool(BaseTool):
    name: str = "save_invoice_record"

    description: str = (
        "Save structured invoice data into the invoice database. "
        "The input must contain actual extracted invoice fields."
    )

    def _run(self, invoice_data: str) -> str:
        try:
            data = json.loads(invoice_data)

            # --------------------------------------------------
            # Handle nested extracted_data
            # --------------------------------------------------

            if isinstance(data.get("extracted_data"), dict):
                data = data["extracted_data"]

            # --------------------------------------------------
            # Normalize vendor field
            # --------------------------------------------------

            if "vendor" in data:
                data["vendor_name"] = data["vendor"]

            # --------------------------------------------------
            # Normalize PO field
            # --------------------------------------------------

            if "po_number" in data:
                data["PO_number"] = data["po_number"]

            # --------------------------------------------------
            # Validate important fields
            # --------------------------------------------------

            required_fields = [
                "vendor_name",
                "invoice_number",
                "invoice_date",
                "due_date",
                "currency",
                "PO_number",
                "items",
                "subtotal",
                "tax",
                "shipping",
                "total",
                "payment_terms",
            ]

            missing_fields = [
                field
                for field in required_fields
                if field not in data
            ]

            # --------------------------------------------------
            # Do NOT silently save incomplete invoices
            # --------------------------------------------------

            if missing_fields:
                return json.dumps(
                    {
                        "status": "FAILED",
                        "reason": "Required invoice fields are missing.",
                        "missing_fields": missing_fields,
                    }
                )

            # --------------------------------------------------
            # Save invoice
            # --------------------------------------------------

            data["extraction_status"] = data.get(
                "extraction_status",
                "SUCCESS",
            )

            invoice_id = create_invoice_record(data)

            if invoice_id is None:
                return json.dumps(
                    {
                        "status": "FAILED",
                        "reason": (
                            "Database did not confirm "
                            "the invoice record."
                        ),
                    }
                )

            return json.dumps(
                {
                    "status": "SUCCESS",
                    "invoice_record_id": str(invoice_id),
                }
            )

        except json.JSONDecodeError:
            return json.dumps(
                {
                    "status": "FAILED",
                    "reason": "Invalid JSON invoice data.",
                }
            )

        except Exception as error:
            return json.dumps(
                {
                    "status": "FAILED",
                    "reason": str(error),
                }
            )

