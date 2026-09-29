
import sqlite3
from pathlib import Path

from crew.invoice_crew import create_approval_processing_crew
from tools.database_tool import create_approval_token


DATABASE_PATH = (
    Path(__file__).resolve().parent
    / "database"
    / "invoices.db"
)


# ============================================================
# STEP 1: Find a pending invoice
# ============================================================

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

invoice = cursor.execute(
    """
    SELECT
        invoice_id,
        vendor_name,
        invoice_number,
        approval_status
    FROM invoices
    WHERE approval_status = 'PENDING'
    ORDER BY invoice_id DESC
    LIMIT 1
    """
).fetchone()

connection.close()


if not invoice:
    print("ERROR: No PENDING invoice found.")
    print("Run the invoice workflow first.")
    raise SystemExit


invoice_id = invoice[0]

print("\n========================================")
print("PENDING INVOICE")
print("========================================")
print(f"Invoice ID:     {invoice[0]}")
print(f"Vendor:         {invoice[1]}")
print(f"Invoice Number: {invoice[2]}")
print(f"Status:         {invoice[3]}")


# ============================================================
# STEP 2: Generate secure approval token
# ============================================================

token = create_approval_token(invoice_id)

if not token:
    print("\nERROR: Could not generate approval token.")
    raise SystemExit


print("\n========================================")
print("APPROVAL TOKEN")
print("========================================")
print(token)


# ============================================================
# STEP 3: Create Agent 4 Crew
# ============================================================

approval_crew = create_approval_processing_crew()


# ============================================================
# TEST 1: APPROVED with valid token
# ============================================================

print("\n========================================")
print("TEST 1: VALID TOKEN + APPROVED")
print("========================================")

result = approval_crew.kickoff(
    inputs={
        "invoice_id": invoice_id,
        "approval_token": token,
        "approval_status": "APPROVED",
    }
)

print(result)


# ============================================================
# Check database
# ============================================================

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

status = cursor.execute(
    """
    SELECT approval_status
    FROM invoices
    WHERE invoice_id = ?
    """,
    (invoice_id,),
).fetchone()

connection.close()

print("\nDatabase Approval Status:")
print(status[0] if status else "NOT FOUND")


# ============================================================
# TEST 2: INVALID TOKEN
# ============================================================

print("\n========================================")
print("TEST 2: INVALID TOKEN")
print("========================================")

# Create another pending invoice for this test.
connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

second_invoice = cursor.execute(
    """
    SELECT invoice_id
    FROM invoices
    WHERE approval_status = 'PENDING'
    ORDER BY invoice_id DESC
    LIMIT 1
    """
).fetchone()

connection.close()


if second_invoice:

    second_invoice_id = second_invoice[0]

    valid_token = create_approval_token(
        second_invoice_id
    )

    invalid_token = "INVALID-TOKEN-12345"

    result = approval_crew.kickoff(
        inputs={
            "invoice_id": second_invoice_id,
            "approval_token": invalid_token,
            "approval_status": "APPROVED",
        }
    )

    print(result)

else:

    print(
        "SKIPPED: No second pending invoice available."
    )


# ============================================================
# TEST 3: REJECTED with valid token
# ============================================================

print("\n========================================")
print("TEST 3: VALID TOKEN + REJECTED")
print("========================================")

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

third_invoice = cursor.execute(
    """
    SELECT invoice_id
    FROM invoices
    WHERE approval_status = 'PENDING'
    ORDER BY invoice_id DESC
    LIMIT 1
    """
).fetchone()

connection.close()


if third_invoice:

    third_invoice_id = third_invoice[0]

    third_token = create_approval_token(
        third_invoice_id
    )

    result = approval_crew.kickoff(
        inputs={
            "invoice_id": third_invoice_id,
            "approval_token": third_token,
            "approval_status": "REJECTED",
        }
    )

    print(result)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    final_status = cursor.execute(
        """
        SELECT approval_status
        FROM invoices
        WHERE invoice_id = ?
        """,
        (third_invoice_id,),
    ).fetchone()

    connection.close()

    print("\nDatabase Approval Status:")
    print(
        final_status[0]
        if final_status
        else "NOT FOUND"
    )

else:

    print(
        "SKIPPED: No third pending invoice available."
    )


print("\n========================================")
print("TESTING COMPLETE")
print("========================================")

