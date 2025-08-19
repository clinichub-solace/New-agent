ClinicHub – Clinical-to-Billing Automation & Audit Report
Date: 2025-08-19
Environment: Preview/Production-ready build

Purpose
This report explains the end‑to‑end operational flow from a clinical SOAP note to billing and finance, including automated receipt generation, inventory deduction upon payment, and financial reporting. It also details user attribution (who did what) for audit/compliance.

Key actors and roles
- Admin: full access; can configure financial categories, inventory, and user roles
- Provider (Doctor/NP/PA): creates/approves encounters and SOAP notes
- Nurse/Technician: records vitals and procedures, administers shots/vaccines
- Reception/Billing: collects payments, closes receipts/invoices

Core data models involved (high level)
- Encounter and SOAP Note: clinical documentation, diagnosis (ICD‑10), procedures, administered items
- Receipt/Invoice: billing artifacts with line items and totals
- Inventory Item and Inventory Transaction: stock (in/out/adjustment) with created_by and reference_id
- Financial Transaction: income/expense entries for finance reporting
- Audit Event: immutable security/audit trail (who/when/what)

Primary automation: SOAP → Receipt → Payment → Inventory → Finance
1) SOAP note creation and completion
- Provider/Nurse creates a SOAP note for a patient and encounter (Subjective, Objective, Assessment, Plan).
- On completion (endpoint: POST /api/soap-notes/{id}/complete), the system can trigger:
  - Receipt generation populated from the SOAP note content (procedures/services administered)
  - Optional invoice generation or linkage if your clinic uses invoices separate from receipts
  - Domain event emission for interoperability (encounter.completed, receipt.created)
- User attribution:
  - SOAP note includes submitted_by/created_by
  - AuditEvent records user_id, user_name, timestamp, IP, and user_agent

2) Receipt generation from SOAP
- Endpoint: POST /api/receipts/soap-note/{soap_id}
- What happens:
  - The receipt is auto-constructed from SOAP note billable items (e.g., office visit, injection, medication administered) with quantities and pricing.
  - Patient linkage is carried forward; provider attribution may be stored in metadata.
  - Receipt number is auto-generated (e.g., RCP-YYYYMMDD-XXXXXX).
- User attribution:
  - The authenticated user invoking the receipt generation is stamped as created_by
  - Audit event recorded: event_type=create, resource_type=receipt

3) Payment and closing the receipt/invoice
- When a payment is collected and the receipt is closed (status paid), two downstream effects are expected:
  A. Inventory deduction for administered or dispensed items
     - For each line item tied to an inventory SKU (e.g., vaccine vial, medication unit), the system posts an InventoryTransaction with transaction_type=out and appropriate quantity.
     - The transaction references the receipt (reference_id) and stamps created_by (the user who processed the payment/closure).
     - This ensures stock levels are reduced only upon confirmed revenue recognition, not at SOAP draft time.
  B. Financial transaction entry
     - A FinancialTransaction is created with type=income, amount matching the payment (net of discounts/taxes as configured), category (e.g., clinical revenue), and reference to the receipt/invoice.
     - If there are associated costs (e.g., purchasing vaccines), those appear as FinancialTransaction entries of type=expense, created when stock is acquired or vendor bills are entered, keeping income vs expenses balanced.
- Endpoints commonly involved:
  - PUT/PATCH /api/invoices/{id}/status or a dedicated payment endpoint (implementation may vary) to mark paid
  - POST /api/financial-transactions to record income
  - POST /api/inventory/{item_id}/transactions to record stock deduction (out)
- User attribution:
  - The payment-collecting user is stamped on both the financial and inventory transactions
  - Audit events log the state transition (receipt closed/paid), inventory outflow, and finance posting

4) Finance module reporting (income vs expenses)
- Income entries:
  - Created when a receipt/invoice is paid and closed; mapped to revenue categories
- Expense entries:
  - Created on inventory purchases (stock in), vendor bills, or adjustments
- Period reporting:
  - Finance reports summarize totals by category/date range for P&L style visibility (income minus expenses)
  - Transactions link back to operational artifacts (receipt/invoice IDs, inventory transactions) for full traceability

User attribution and audit trail (who did what)
- Every critical action stamps created_by/updated_by fields where applicable (SOAP notes, receipts, inventory transactions, finance transactions).
- The audit subsystem stores AuditEvent records with:
  - event_type (e.g., create, update, access, login)
  - resource_type (e.g., soap_note, receipt, inventory, finance_transaction)
  - user_id, user_name, timestamp, IP address, user_agent
  - phi_accessed flag for HIPAA-sensitive reads
- Examples:
  - “Who created the note?” → SOAP note.created event with user attribution
  - “Who applied the shot?” → Documented within the SOAP/Procedure line item and reflected in inventory outflow created_by at payment closure
  - “Who closed the receipt?” → Receipt status change event, and linked financial/inventory transactions stamped with that user

Operational sequence (text diagram)
- Provider/Nurse → Create SOAP Note (draft)
- Provider → Complete SOAP Note → Triggers: Create Receipt (auto items)
- Reception/Billing → Take Payment → Close Receipt (status=paid)
  - Inventory Out (for any billable items tied to stock)
  - Financial Transaction (income)
- Finance → Income vs Expense reports reflect real-time position
- Compliance → Audit events and user stamps ensure traceability (who/when/what/from where)

Key endpoints involved (representative)
- SOAP flow
  - POST /api/soap-notes (create)
  - POST /api/soap-notes/{id}/complete (automation trigger)
- Receipt flow
  - POST /api/receipts/soap-note/{soap_id} (auto-generate from SOAP)
  - GET /api/receipts, GET /api/receipts/{id}
- Payment & Inventory & Finance
  - PUT/PATCH /api/invoices/{id}/status (or equivalent payment endpoint) – mark paid/closed
  - POST /api/inventory/{item_id}/transactions (type=out) – deduct stock
  - POST /api/financial-transactions (type=income) – revenue entry
- Security & audit
  - All routes protected via JWT/RBAC
  - Audit events recorded on create/update/access (PHI)

Data integrity and reconciliation
- Lineage links: SOAP Note ID → Receipt/Invoice ID(s) → Financial Transaction(s) and Inventory Transaction(s)
- Reference fields (reference_id, encounter_id, receipt_id) unify the operational trail
- jsonable_encoder and projections prevent ObjectId serialization leaks; consistent error shapes simplify reconciliation tools

Edge cases & guardrails
- Partial payments: create multiple income entries; final inventory deduction can be configured at fully paid or at first fulfillment (clinic policy)
- Refund/void: inverse financial transaction and inventory adjustment (type=in) to restore stock
- Back-dated entries: audit timestamps ensure historical accuracy; finance reports should be time‑bucketed by transaction date

Admin/Configuration considerations
- Pricing tables for procedures/medications
- Inventory SKU mapping to receipt items (for automatic outflow)
- Finance categories for income/expense rollups
- Role permissions for who can create/close receipts, post finance transactions, and adjust inventory

Benefits
- Reduces leakage: stock only decremented after actual payment
- Full traceability: every action stamped with user identity and logged to audit trail
- Real‑time P&L visibility: income vs expenses tracked without manual re‑entry

Notes
- In prior assessments, invoice status update endpoints needed verification; ensure the payment/closure mechanism used by your clinic calls both the inventory and finance posting logic.
- If ICD‑10 integration is enabled, diagnosis codes from SOAP notes can feed charge capture and reporting.
