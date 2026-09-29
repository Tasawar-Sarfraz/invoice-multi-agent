import sqlite3
from pathlib import Path
from typing import Optional


DATABASE_PATH = Path(__file__).resolve().parent.parent / "database" / "invoices.db"


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
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
            approval_status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
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


def update_approval_status(invoice_id: int, approval_status: str) -> bool:
    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE invoices
        SET approval_status = ?
        WHERE invoice_id = ?
        """,
        (approval_status, invoice_id),
    )

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated
