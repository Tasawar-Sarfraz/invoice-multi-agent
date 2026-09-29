import sqlite3
from pathlib import Path
from typing import Optional


DATABASE_PATH = (
    Path(__file__).resolve().parent.parent
    / "database"
    / "invoices.db"
)


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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()

    # For existing testing databases created by the previous version.
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
            str(invoice_data.get("items", [])),
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
    import secrets

    initialize_database()

    token = secrets.token_urlsafe(32)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE invoices
        SET approval_token = ?
        WHERE invoice_id = ?
        """,
        (token, invoice_id),
    )

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    if not updated:
        return None

    return token


def update_approval_status(
    invoice_id: int,
    approval_token: str,
    approval_status: str,
) -> bool:

    initialize_database()

    allowed_statuses = {
        "APPROVED",
        "REJECTED",
    }

    if approval_status not in allowed_statuses:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE invoices
        SET approval_status = ?
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
