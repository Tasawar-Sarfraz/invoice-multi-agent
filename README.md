# invoice-multi-agent
Complete workflow — Start se End tak
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
PO Matching
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
Start kahan se hota hai?

Streamlit UI se.

User invoice email paste karta hai:

From: accounts@brighttech.com
Subject: Invoice INV-3003

Vendor: Bright Tech Solutions
Invoice Number: INV-3003
PO Number: PO-3003
...

Phir:

Run Invoice Workflow

click hota hai.

2. Agent 1 — Email Classification
Kaam

Agent 1 sirf ye determine karta hai:

INVOICE
NOT_INVOICE
UNCERTAIN
SECURITY_ALERT

Example:

Invoice INV-3003
        ↓
Agent 1
        ↓
INVOICE
AI use karta hai?

YES ✅

Agent 1 CrewAI + Groq LLM use karta hai.

Agent 1
   ↓
Groq LLM

Agent 1 ka kaam sirf classification hai.

Ye:

invoice approve nahi karta
database modify nahi karta
PO modify nahi karta
email send nahi karta
3. Agent 2 — Invoice Extraction

Agent 2 invoice/email se structured information extract karta hai.

Example:

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

Items:

Keyboard
Quantity: 5
Unit Price: 100
Line Total: 500
AI use karta hai?

YES ✅

Agent 2
   ↓
Groq LLM

Agent 2 ke paas save_invoice_record tool bhi hai.

Agent 2
   ↓
SaveInvoiceTool
   ↓
database/invoices.db

Yani Agent 2 AI se extraction karta hai aur tool ke through database mein record save karta hai.

4. Database

Database humara central storage hai:

database/
└── invoices.db

Ismein invoice ki information save hoti hai.

Example:

Invoice ID       12
Invoice Number   INV-3003
Vendor           Bright Tech Solutions
PO Number        PO-3003
Total            550
Currency         USD
Approval Status  PENDING

Database already exist karta hai, aur database_tool.py usko handle karta hai.

5. Agent 3 — Purchase Order Matching

Agent 3 invoice aur PO compare karta hai.

Example:

Invoice
   ↓
PO-3003
   ↓
Agent 3
   ↓
PO-3003.json

PO:

Vendor: Bright Tech Solutions
Item: Keyboard
Quantity: 5
Unit Price: 100
Total: 550

Phir Agent 3 compare karta hai:

Vendor
PO number
Item
Quantity
Unit price
Total
Currency

Possible result:

MATCH
MISMATCH
PO_NOT_FOUND
AMBIGUOUS_MATCH
INSUFFICIENT_DATA
SECURITY_ALERT
AI use karta hai?

YES ✅

Agent 3 bhi Groq LLM + CrewAI use karta hai.

Uske paas:

PurchaseOrderTool

hai jo actual PO JSON file search karta hai.

Important distinction:

Agent 3 = AI reasoning/comparison
PO Tool  = actual PO file lookup
6. Manager Approval

Agent 3 ke baad automatic approval nahi hoti.

Invoice:

PENDING

rehta hai.

Manager Approval UI mein pending invoices show hoti hain.

Manager invoice select karta hai.

Phir:

Generate Approval Token

Token generate hota hai.

Token:

random hota hai
specific invoice se linked hota hai
30 minutes expire hota hai
successful processing ke baad clear ho jata hai
7. Agent 4 — Approval Processor

Agent 4 ka role different hai.

Agent 4 khud decide nahi karta ke invoice approve honi chahiye ya reject.

Manager decision deta hai:

APPROVED

ya

REJECTED

Aur approval token provide hota hai.

Agent 4:

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
Process Approval
      ↓
Database
AI use karta hai?

YES ✅

Agent 4 bhi:

CrewAI + Groq LLM

use karta hai.

Lekin actual security/database operations tools perform karte hain:

validate_approval_token
process_invoice_approval
8. Final End

Agar manager approve kare:

PENDING
   ↓
APPROVED

Agar manager reject kare:

PENDING
   ↓
REJECTED

Aur database update ho jata hai.

                    GROQ LLM
                       │
       ┌───────────────┼────────────────┐
       ↓               ↓                ↓
    Agent 1          Agent 2          Agent 3
       │               │                │
 Classification     Extraction       Matching
                       │                │
                       ↓                ↓
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
           APPROVED           REJECTED

           Agent 4 ka role

Agent 4 ko ye 3 cheezen milni hain:

Invoice ID — 15
Approval Token
Manager Decision — APPROVED ya REJECTED

Phir Agent 4:

Token validate karega.
Manager decision verify karega.
SQLite database mein invoice status update karega.
Final result return karega.

Expected database states:

APPROVED
REJECTED
