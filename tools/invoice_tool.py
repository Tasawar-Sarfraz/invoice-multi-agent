import json

from crewai.tools import BaseTool

from tools.database_tool import create_invoice_record


class SaveInvoiceTool(BaseTool):
    name: str = "save_invoice_record"
    description: str = (
        "Save the extracted invoice data into the invoice database. "
        "Only invoice workflow fields may be written."
    )

    def _run(self, invoice_data: str) -> str:
        try:
            data = json.loads(invoice_data)

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
                "extraction_status",
            ]

            for field in required_fields:
                if field not in data:
                    data[field] = "UNKNOWN"

            invoice_id = create_invoice_record(data)

            if invoice_id is None:
                return json.dumps(
                    {
                        "status": "FAILED",
                        "reason": "Database did not confirm the invoice record.",
                    }
                )

            return json.dumps(
                {
                    "status": "SUCCESS",
                    "invoice_record_id": str(invoice_id),
                }
            )

        except Exception as error:
            return json.dumps(
                {
                    "status": "FAILED",
                    "reason": str(error),
                }
            )
