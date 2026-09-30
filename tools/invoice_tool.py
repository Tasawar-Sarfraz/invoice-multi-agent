
import sqlite3
import secrets
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


DATABASE_PATH = (
    Path(__file__).resolve().parent.parent
    / "database"
    / "invoices.db"
)

APPROVAL_TOKEN_EXPIRY_MINUTES = 30


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sqlite3.connect(DATABASE_PATH)


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT,
            invoice_number TEXT,
            invoice_date TEXT,
            due_date TEXT,
            currency TEXT,
            po_number TEXT,
            items TEXT,
            subtotal TEXT,
            tax TEXT,
            shipping TEXT,
            total TEXT,
            payment_terms TEXT,
            extraction_status TEXT,
            verification_status TEXT,
            approval_status TEXT DEFAULT 'PENDING',
            approval_token TEXT,
            approval_token_expires_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Handle existing databases created by older versions.
    columns = {
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(invoices)"
        ).fetchall()
    }

    if "approval_token" not in columns:
        cursor.execute(
            "ALTER TABLE invoices ADD COLUMN approval_token TEXT"
        )

    if "approval_token_expires_at" not in columns:
        cursor.execute(
            "ALTER TABLE invoices ADD COLUMN approval_token_expires_at TEXT"
        )

    connection.commit()
    connection.close()


def create_invoice_record(invoice_data: dict) -> Optional[int]:
    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO invoices (
            vendor_name,
            invoice_number,
            invoice_date,
            due_date,
            currency,
            po_number,
            items,
            subtotal,
            tax,
            shipping,
            total,
            payment_terms,
            extraction_status,
            verification_status,
            approval_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            invoice_data.get("vendor_name", "UNKNOWN"),
            invoice_data.get("invoice_number", "UNKNOWN"),
            invoice_data.get("invoice_date", "UNKNOWN"),
            invoice_data.get("due_date", "UNKNOWN"),
            invoice_data.get("currency", "UNKNOWN"),
            invoice_data.get("PO_number", "UNKNOWN"),

            # Store items as valid JSON.
            json.dumps(
                invoice_data.get("items", [])
            ),

            invoice_data.get("subtotal", "UNKNOWN"),
            invoice_data.get("tax", "UNKNOWN"),
            invoice_data.get("shipping", "UNKNOWN"),
            invoice_data.get("total", "UNKNOWN"),
            invoice_data.get("payment_terms", "UNKNOWN"),
            invoice_data.get("extraction_status", "SUCCESS"),
            "PENDING",
            "PENDING",
        ),
    )

    invoice_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return invoice_id


def create_approval_token(invoice_id: int) -> Optional[str]:
    """
    Generate a secure approval token for a specific invoice.

    The token expires after APPROVAL_TOKEN_EXPIRY_MINUTES.
    """

    initialize_database()

    token = secrets.token_urlsafe(32)

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=APPROVAL_TOKEN_EXPIRY_MINUTES)
    ).isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE invoices
        SET
            approval_token = ?,
            approval_token_expires_at = ?
        WHERE invoice_id = ?
        AND approval_status = 'PENDING'
        """,
        (
            token,
            expires_at,
            invoice_id,
        ),
    )

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    if not updated:
        return None

    return token


def validate_approval_token(
    invoice_id: int,
    approval_token: str,
) -> dict:
    """
    Validate an approval token before allowing approval/rejection.

    Checks:
    1. Invoice exists
    2. Invoice is still PENDING
    3. Token matches
    4. Token has not expired
    """

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            approval_token,
            approval_token_expires_at,
            approval_status
        FROM invoices
        WHERE invoice_id = ?
        """,
        (invoice_id,),
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return {
            "valid": False,
            "reason": "Invoice not found.",
        }

    stored_token, expires_at, approval_status = row

    if approval_status != "PENDING":
        return {
            "valid": False,
            "reason": "Invoice has already been processed.",
        }

    if not stored_token:
        return {
            "valid": False,
            "reason": "No approval token exists for this invoice.",
        }

    if not approval_token or not secrets.compare_digest(
        stored_token,
        approval_token,
    ):
        return {
            "valid": False,
            "reason": "Invalid approval token.",
        }

    if not expires_at:
        return {
            "valid": False,
            "reason": "Approval token has no expiry information.",
        }

    try:
        expiry_time = datetime.fromisoformat(expires_at)

        if datetime.now(timezone.utc) >= expiry_time:
            return {
                "valid": False,
                "reason": "Approval token has expired.",
            }

    except ValueError:
        return {
            "valid": False,
            "reason": "Invalid token expiry information.",
        }

    return {
        "valid": True,
        "reason": "Approval token is valid.",
    }


def update_approval_status(
    invoice_id: int,
    approval_token: str,
    approval_status: str,
) -> bool:
    """
    Update invoice approval status only after token validation.
    """

    allowed_statuses = {
        "APPROVED",
        "REJECTED",
    }

    if approval_status not in allowed_statuses:
        return False

    validation = validate_approval_token(
        invoice_id,
        approval_token,
    )

    if not validation["valid"]:
        return False

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE invoices
        SET
            approval_status = ?,
            approval_token = NULL,
            approval_token_expires_at = NULL
        WHERE invoice_id = ?
        AND approval_token = ?
        AND approval_status = 'PENDING'
        """,
        (
            approval_status,
            invoice_id,
            approval_token,
        ),
    )

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated

