import json
import sqlite3
import secrets
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

    columns = {
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(invoices)"
        ).fetchall()
    }

    if "approval_token" not in columns:
        cursor.execute(
            """
            ALTER TABLE invoices
            ADD COLUMN approval_token TEXT
            """
        )

    if "approval_token_expires_at" not in columns:
        cursor.execute(
            """
            ALTER TABLE invoices
            ADD COLUMN approval_token_expires_at TEXT
            """
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
            json.dumps(
                invoice_data.get("items", [])
            ),
            invoice_data.get("subtotal", "UNKNOWN"),
            invoice_data.get("tax", "UNKNOWN"),
            invoice_data.get("shipping", "UNKNOWN"),
            invoice_data.get("total", "UNKNOWN"),
            invoice_data.get("payment_terms", "UNKNOWN"),
            invoice_data.get(
                "extraction_status",
                "SUCCESS",
            ),
            "PENDING",
            "PENDING",
        ),
    )

    invoice_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return invoice_id


def update_verification_status(
    invoice_id: int,
    verification_status: str,
) -> bool:
    """
    Update invoice verification status after Agent 3 validation.
    """

    allowed_statuses = {
        "VERIFIED",
        "FAILED",
    }

    if verification_status not in allowed_statuses:
        return False

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE invoices
        SET verification_status = ?
        WHERE invoice_id = ?
        """,
        (
            verification_status,
            invoice_id,
        ),
    )

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated


def create_approval_token(
    invoice_id: int,
) -> Optional[str]:
    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT approval_status
        FROM invoices
        WHERE invoice_id = ?
        """,
        (invoice_id,),
    )

    row = cursor.fetchone()

    if row is None:
        connection.close()
        return None

    approval_status = row[0]

    if approval_status != "PENDING":
        connection.close()
        return None

    token = secrets.token_urlsafe(32)

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=APPROVAL_TOKEN_EXPIRY_MINUTES
        )
    ).isoformat()

    cursor.execute(
        """
        UPDATE invoices
        SET approval_token = ?,
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


def process_approval(
    invoice_id: int,
    approval_token: str,
    decision: str,
) -> dict:
    initialize_database()

    decision = decision.strip().upper()

    if decision not in {
        "APPROVED",
        "REJECTED",
    }:
        return {
            "status": "FAILED",
            "reason": "Invalid approval decision.",
            "security_flags": [],
        }

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                approval_status,
                approval_token,
                approval_token_expires_at
            FROM invoices
            WHERE invoice_id = ?
            """,
            (invoice_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return {
                "status": "FAILED",
                "reason": "Invoice not found.",
                "security_flags": [
                    "INVOICE_NOT_FOUND"
                ],
            }

        (
            approval_status,
            stored_token,
            expires_at,
        ) = row

        if approval_status != "PENDING":
            return {
                "status": "NOT_PERMITTED",
                "reason": (
                    "Invoice has already been processed."
                ),
                "security_flags": [
                    "DUPLICATE_PROCESSING"
                ],
            }

        if not stored_token or approval_token != stored_token:
            return {
                "status": "FAILED",
                "reason": "Invalid approval token.",
                "security_flags": [
                    "INVALID_TOKEN"
                ],
            }

        if not expires_at:
            return {
                "status": "FAILED",
                "reason": "Approval token has no expiry.",
                "security_flags": [
                    "INVALID_TOKEN_EXPIRY"
                ],
            }

        try:
            expiry_datetime = datetime.fromisoformat(
                expires_at
            )

            if (
                expiry_datetime.tzinfo is None
            ):
                expiry_datetime = expiry_datetime.replace(
                    tzinfo=timezone.utc
                )

        except ValueError:
            return {
                "status": "FAILED",
                "reason": "Invalid approval token expiry.",
                "security_flags": [
                    "INVALID_TOKEN_EXPIRY"
                ],
            }

        if (
            datetime.now(timezone.utc)
            >= expiry_datetime
        ):
            return {
                "status": "FAILED",
                "reason": "Approval token has expired.",
                "security_flags": [
                    "EXPIRED_TOKEN"
                ],
            }

        cursor.execute(
            """
            UPDATE invoices
            SET approval_status = ?,
                approval_token = NULL,
                approval_token_expires_at = NULL
            WHERE invoice_id = ?
              AND approval_status = 'PENDING'
              AND approval_token = ?
            """,
            (
                decision,
                invoice_id,
                approval_token,
            ),
        )

        if cursor.rowcount != 1:
            connection.rollback()

            return {
                "status": "NOT_PERMITTED",
                "reason": (
                    "Invoice has already been processed."
                ),
                "security_flags": [
                    "DUPLICATE_PROCESSING"
                ],
            }

        connection.commit()

        return {
            "status": "SUCCESS",
            "invoice_id": str(invoice_id),
            "approval_status": decision,
            "security_flags": [],
        }

    finally:
        connection.close()

def validate_approval_token(
    invoice_id: int,
    approval_token: str,
) -> dict:
    """
    Validate an approval token without changing invoice status.

    Returns:
        {
            "valid": True/False,
            "reason": "...",
            "security_flags": [...]
        }
    """

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                approval_status,
                approval_token,
                approval_token_expires_at
            FROM invoices
            WHERE invoice_id = ?
            """,
            (invoice_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return {
                "valid": False,
                "reason": "Invoice not found.",
                "security_flags": [
                    "INVOICE_NOT_FOUND"
                ],
            }

        (
            approval_status,
            stored_token,
            expires_at,
        ) = row

        if approval_status != "PENDING":
            return {
                "valid": False,
                "reason": (
                    "Invoice has already been processed."
                ),
                "security_flags": [
                    "DUPLICATE_PROCESSING"
                ],
            }

        if not stored_token or approval_token != stored_token:
            return {
                "valid": False,
                "reason": "Invalid approval token.",
                "security_flags": [
                    "INVALID_TOKEN"
                ],
            }

        if not expires_at:
            return {
                "valid": False,
                "reason": (
                    "Approval token has no expiry."
                ),
                "security_flags": [
                    "INVALID_TOKEN_EXPIRY"
                ],
            }

        try:
            expiry_datetime = datetime.fromisoformat(
                expires_at
            )

            if expiry_datetime.tzinfo is None:
                expiry_datetime = expiry_datetime.replace(
                    tzinfo=timezone.utc
                )

        except ValueError:
            return {
                "valid": False,
                "reason": (
                    "Invalid approval token expiry."
                ),
                "security_flags": [
                    "INVALID_TOKEN_EXPIRY"
                ],
            }

        if datetime.now(timezone.utc) >= expiry_datetime:
            return {
                "valid": False,
                "reason": (
                    "Approval token has expired."
                ),
                "security_flags": [
                    "EXPIRED_TOKEN"
                ],
            }

        return {
            "valid": True,
            "reason": "Approval token is valid.",
            "security_flags": [],
        }

    finally:
        connection.close()
