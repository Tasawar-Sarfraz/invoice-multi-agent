# Invoice Multi-Agent System

An AI-powered **multi-agent invoice processing system** built with **CrewAI, Groq LLM, Python, Streamlit, and SQLite**.

The system processes an invoice from the moment it is submitted through the final manager decision. Different AI agents handle different responsibilities such as email classification, invoice extraction, Purchase Order matching, and approval/rejection processing.

## What Does This System Do?

The Invoice Multi-Agent System automates the following workflow:

```text
Incoming Invoice Email
        ↓
   Agent 1
Email Classification
        ↓
   Agent 2
Invoice Extraction
        ↓
   Database
Invoice Record Save
        ↓
   Agent 3
Purchase Order Matching
        ↓
Manager Review
        ↓
Approval Token
        ↓
   Agent 4
Approval/Rejection Processing
        ↓
   Database
APPROVED / REJECTED
```

The system uses **specialized agents**, where each agent has a specific responsibility.

---

# Complete Workflow

## 1. Streamlit UI — Workflow Starts Here

The workflow starts from the **Streamlit application**.

The user provides an invoice email, for example:

```text
From: accounts@brighttech.com
Subject: Invoice INV-3003

Vendor: Bright Tech Solutions
Invoice Number: INV-3003
Invoice Date: 2026-09-30
Due Date: 2026-10-30
Currency: USD
PO Number: PO-3003

Items:
1. Keyboard | Quantity: 5 | Unit Price: 100 | Subtotal: 500

Subtotal: 500
Tax: 50
Shipping: 0
Total: 550

Payment Terms: Net 30
```

The user clicks:

```text
Run Invoice Workflow
```

The multi-agent workflow begins.

---

# 2. Agent 1 — Email Classification

### Purpose

Agent 1 determines what type of email has been submitted.

Possible results:

```text
INVOICE
NOT_INVOICE
UNCERTAIN
SECURITY_ALERT
```

Example:

```text
Invoice Email
     ↓
  Agent 1
     ↓
  INVOICE
```

### AI Used

Yes.

Agent 1 uses:

```text
CrewAI + Groq LLM
```

### Agent 1 Responsibilities

Agent 1 is responsible only for classification.

It does **not**:

* Approve an invoice
* Reject an invoice
* Modify the database
* Modify a Purchase Order
* Process manager decisions

---

# 3. Agent 2 — Invoice Extraction

After the email is classified as an invoice, Agent 2 extracts structured information from the invoice.

Example:

```text
Vendor          → Bright Tech Solutions
Invoice Number  → INV-3003
Invoice Date    → 2026-09-30
Due Date        → 2026-10-30
PO Number       → PO-3003
Currency        → USD
Subtotal        → 500
Tax             → 50
Shipping        → 0
Total           → 550
Payment Terms   → Net 30
```

### Invoice Items

```text
Keyboard
Quantity: 5
Unit Price: 100
Subtotal: 500
```

### AI Used

Yes.

```text
Agent 2
   ↓
Groq LLM
```

Agent 2 also has access to:

```text
SaveInvoiceTool
```

The complete flow is:

```text
Agent 2
   ↓
Extract Invoice Data
   ↓
SaveInvoiceTool
   ↓
SQLite Database
```

---

# 4. Database — Central Storage

The system uses SQLite as the central database for invoice records and workflow states.

```text
database/
└── invoices.db
```

Example invoice record:

```text
Invoice ID       12
Invoice Number   INV-3003
Vendor           Bright Tech Solutions
PO Number        PO-3003
Total            550
Currency         USD
Approval Status  PENDING
```

The database stores:

* Vendor
* Invoice number
* Invoice date
* Due date
* Currency
* PO number
* Invoice items
* Subtotal
* Tax
* Shipping
* Total
* Payment terms
* Extraction status
* Verification status
* Approval status
* Approval token
* Approval token expiry

Database operations are handled through:

```text
tools/database_tool.py
```

---

# 5. Agent 3 — Purchase Order Matching

Agent 3 compares the extracted invoice against the corresponding Purchase Order.

The workflow is:

```text
Invoice
   ↓
PO Number
   ↓
Agent 3
   ↓
PurchaseOrderTool
   ↓
PO JSON
```

For example:

```text
Invoice PO Number:
PO-3003
```

Agent 3 asks the Purchase Order tool to find:

```text
PO-3003
```

The tool searches the Purchase Order JSON files and returns the matching PO.

## What Does Agent 3 Compare?

Agent 3 compares:

* Vendor
* PO number
* Items
* Quantity
* Unit price
* Invoice subtotal against PO total
* Currency

Possible results:

```text
MATCH
MISMATCH
PO_NOT_FOUND
AMBIGUOUS_MATCH
INSUFFICIENT_DATA
SECURITY_ALERT
```

## Important Amount Matching Rule

The system compares:

```text
Invoice Subtotal
        VS
PO Total
```

It does **not** directly compare:

```text
Invoice Final Total
        VS
PO Total
```

### Example

Invoice:

```text
Subtotal = 650
Tax      = 65
Shipping = 20
Total    = 735
```

Purchase Order:

```text
Total = 650
```

The correct comparison is:

```text
Invoice Subtotal = 650
PO Total         = 650
```

Therefore:

```text
MATCH
```

Tax and shipping can be additional invoice charges and are not automatically treated as a Purchase Order amount mismatch.

## AI Used

Yes.

Agent 3 uses:

```text
CrewAI + Groq LLM
```

Agent 3 also uses:

```text
PurchaseOrderTool
```

The responsibilities are separated:

```text
Agent 3
   ↓
AI reasoning and comparison

PurchaseOrderTool
   ↓
Actual PO file lookup
```

Agent 3 does not approve or reject the invoice.

---

# 6. Manager Approval

After PO matching, the invoice does not automatically become approved.

The invoice remains:

```text
PENDING
```

The Manager Approval section in the Streamlit UI allows the manager to review the invoice.

The manager selects an invoice and generates an:

```text
Approval Token
```

---

# 7. Approval Token

The approval token provides an additional security layer for the manager approval workflow.

The token is:

* Randomly generated
* Linked to a specific invoice
* Valid for 30 minutes
* Cleared after successful processing
* Protected against duplicate processing

The approval request requires:

```text
Invoice ID
+
Approval Token
+
Manager Decision
```

---

# 8. Agent 4 — Approval Processor

Agent 4 handles the manager's approval or rejection request.

Agent 4 does **not independently decide** whether an invoice should be approved.

The manager makes the decision:

```text
APPROVED
```

or:

```text
REJECTED
```

The workflow becomes:

```text
Invoice ID
      +
Approval Token
      +
Manager Decision
      ↓
   Agent 4
      ↓
Validate Token
      ↓
Process Decision
      ↓
SQLite Database
```

## AI Used

Yes.

Agent 4 uses:

```text
CrewAI + Groq LLM
```

The actual security and database operations are handled by dedicated tools/functions such as:

```text
validate_approval_token
process_approval
```

This separates AI processing from sensitive database operations.

---

# 9. Security and Duplicate Protection

The approval workflow includes multiple validation checks.

## Invalid Token

If the provided token is incorrect:

```text
Invalid Token
      ↓
FAILED
```

The invoice is not processed.

## Expired Token

Approval tokens have a limited validity period.

If the token has expired:

```text
Expired Token
      ↓
FAILED
```

The invoice is not processed.

## Duplicate Processing

An invoice that has already been processed cannot be processed again.

For example:

```text
PENDING
   ↓
APPROVED
```

A second approval attempt results in:

```text
NOT_PERMITTED
```

Similarly:

```text
PENDING
   ↓
REJECTED
```

A second rejection attempt is also prevented.

---

# 10. Final Database States

If the manager approves the invoice:

```text
PENDING
   ↓
APPROVED
```

If the manager rejects the invoice:

```text
PENDING
   ↓
REJECTED
```

The final status is stored in the SQLite database.

---

# System Architecture

```text
                         GROQ LLM
                            │
          ┌─────────────────┼─────────────────┐
          ↓                 ↓                 ↓
       Agent 1           Agent 2           Agent 3
          │                 │                 │
   Classification       Extraction        PO Matching
                            │                 │
                            ↓                 ↓
                       SQLite DB          PO JSON
                            │
                            ↓
                    Manager Approval
                            │
                            ↓
                         Agent 4
                            │
                     Approval Tools
                            │
                            ↓
                       SQLite DB
                            │
                   ┌────────┴────────┐
                   ↓                 ↓
                APPROVED          REJECTED
```

---

# Agent Responsibilities

| Agent   | Responsibility                | Uses AI | Database Write     | Approval Decision     |
| ------- | ----------------------------- | ------- | ------------------ | --------------------- |
| Agent 1 | Email Classification          | Yes     | No                 | No                    |
| Agent 2 | Invoice Extraction            | Yes     | Yes, through tool  | No                    |
| Agent 3 | PO Matching                   | Yes     | No                 | No                    |
| Agent 4 | Approval/Rejection Processing | Yes     | Yes, through tools | Uses Manager Decision |

---

# Technology Stack

* **Python 3.12**
* **CrewAI** — Multi-agent orchestration
* **Groq LLM** — AI model used by the agents
* **Streamlit** — Web interface
* **SQLite** — Invoice and workflow database
* **JSON** — Purchase Order storage

---

# Project Structure

```text
invoice-multi-agent/
│
├── agents/
│   ├── agent1_email_classifier.py
│   ├── agent2_invoice_extractor.py
│   ├── agent3_po_matcher.py
│   └── agent4_approval_processor.py
│
├── tasks/
│   ├── email_classification_task.py
│   ├── invoice_extraction_task.py
│   ├── po_matching_task.py
│   └── approval_task.py
│
├── tools/
│   ├── database_tool.py
│   ├── invoice_tool.py
│   ├── po_tool.py
│   └── approval_tool.py
│
├── crew/
│   └── invoice_crew.py
│
├── database/
│   └── invoices.db
│
├── data/
│   ├── emails/
│   ├── invoices/
│   └── purchase_orders/
│
├── app.py
├── config.py
├── requirements.txt
└── README.md
```

---

# End-to-End Example

```text
1. User pastes invoice email
             ↓
2. Click "Run Invoice Workflow"
             ↓
3. Agent 1
   Classifies email as INVOICE
             ↓
4. Agent 2
   Extracts structured invoice data
             ↓
5. SaveInvoiceTool
   Saves invoice to SQLite
             ↓
6. Agent 3
   Finds the requested PO
             ↓
7. Agent 3
   Compares invoice and PO
             ↓
8. Invoice remains PENDING
             ↓
9. Manager reviews invoice
             ↓
10. Approval Token generated
             ↓
11. Manager selects APPROVED or REJECTED
             ↓
12. Agent 4 processes the decision
             ↓
13. Token is validated
             ↓
14. SQLite database is updated
             ↓
15. Final state:
       APPROVED
          or
       REJECTED
```

---

# Key Design Principles

### Specialized Agents

Each agent has a focused responsibility instead of handling the entire workflow.

### Tool-Based Operations

Sensitive operations such as database updates, PO lookup, and approval validation are handled through dedicated tools.

### Human-in-the-Loop Approval

The system does not automatically approve invoices after PO matching. A manager makes the final approval or rejection decision.

### Approval Security

Approval tokens are invoice-specific, time-limited, and protected against duplicate processing.

### Clear Separation of Responsibilities

```text
Agent 1 → Classification
Agent 2 → Extraction
Agent 3 → PO Matching
Agent 4 → Approval Processing
```

---

# Final Workflow

```text
                    INVOICE EMAIL
                         │
                         ↓
                    ┌─────────┐
                    │ Agent 1 │
                    └────┬────┘
                         │
                    Classification
                         │
                         ↓
                    ┌─────────┐
                    │ Agent 2 │
                    └────┬────┘
                         │
                     Extraction
                         │
                         ↓
                   ┌────────────┐
                   │  SQLite DB │
                   └─────┬──────┘
                         │
                         ↓
                    ┌─────────┐
                    │ Agent 3 │
                    └────┬────┘
                         │
                    PO Matching
                         │
                         ↓
                  MANAGER REVIEW
                         │
                         ↓
                  APPROVAL TOKEN
                         │
                         ↓
                    ┌─────────┐
                    │ Agent 4 │
                    └────┬────┘
                         │
                  Validate Token
                         │
                         ↓
                   ┌────────────┐
                   │  SQLite DB │
                   └─────┬──────┘
                         │
                  ┌──────┴──────┐
                  ↓             ↓
              APPROVED       REJECTED
```

---

## Project Goal

The goal of this project is to demonstrate a complete **AI-powered invoice processing workflow** using multiple specialized agents.

Instead of giving one AI agent every responsibility, the system separates the workflow into focused stages:

    text
Classification
      ↓
Extraction
      ↓
Database Persistence
      ↓
PO Matching
      ↓
Human Review
      ↓
Secure Approval Processing
      ↓
Final Database State


This architecture makes the invoice workflow easier to understand, test, maintain, and extend.
