import json
from pathlib import Path

from crewai.tools import BaseTool


PO_DIRECTORY = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "purchase_orders"
)


class PurchaseOrderTool(BaseTool):
    name: str = "find_purchase_order"
    description: str = (
        "Find a purchase order using the PO number provided by the invoice. "
        "Only search for the requested PO number."
    )

    def _run(self, po_number: str) -> str:
        po_number = po_number.strip()

        if not po_number:
            return json.dumps(
                {
                    "status": "PO_NOT_FOUND",
                    "reason": "PO number was not provided.",
                }
            )

        if not PO_DIRECTORY.exists():
            return json.dumps(
                {
                    "status": "PO_NOT_FOUND",
                    "reason": "Purchase order directory does not exist.",
                }
            )

        matching_files = []

        for file_path in PO_DIRECTORY.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    po_data = json.load(file)

                if str(po_data.get("po_number", "")).strip() == po_number:
                    matching_files.append(
                        {
                            "file": file_path.name,
                            "data": po_data,
                        }
                    )

            except (json.JSONDecodeError, OSError):
                continue

        if len(matching_files) == 0:
            return json.dumps(
                {
                    "status": "PO_NOT_FOUND",
                    "reason": f"No PO found for PO number {po_number}.",
                }
            )

        if len(matching_files) > 1:
            return json.dumps(
                {
                    "status": "AMBIGUOUS_MATCH",
                    "reason": f"Multiple POs found for PO number {po_number}.",
                }
            )

        return json.dumps(
            {
                "status": "FOUND",
                "po_id": matching_files[0]["file"],
                "po_data": matching_files[0]["data"],
            }
        )
