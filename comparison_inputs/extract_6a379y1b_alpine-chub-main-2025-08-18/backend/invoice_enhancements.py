# ClinicHub Invoice System Enhancements
# SOAP Note Integration & Inventory Deduction

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum
import uuid

# Enhanced Invoice Models

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    CHECK = "check"
    BANK_TRANSFER = "bank_transfer"
    INSURANCE = "insurance"
    CREDIT = "credit"

class InvoiceItemType(str, Enum):
    SERVICE = "service"
    PRODUCT = "product"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    CONSULTATION = "consultation"

class InvoiceItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    item_type: InvoiceItemType = InvoiceItemType.SERVICE
    quantity: int = 1
    unit_price: float
    total_price: float = 0.0
    inventory_item_id: Optional[str] = None
    cpt_code: Optional[str] = None  # CPT code for procedures
    icd10_code: Optional[str] = None  # ICD-10 code for diagnoses
    is_service: bool = True
    tax_rate: float = 0.0
    discount_percentage: float = 0.0
    notes: Optional[str] = None

class PaymentRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str
    amount: float
    payment_method: PaymentMethod
    payment_date: date = Field(default_factory=date.today)
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    processed_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ComprehensiveInvoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str = Field(default_factory=lambda: f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}")
    patient_id: str
    encounter_id: Optional[str] = None  # Link to SOAP note encounter
    provider_id: str
    
    # Invoice Details
    description: str
    status: InvoiceStatus = InvoiceStatus.DRAFT
    items: List[InvoiceItem] = []
    
    # Dates
    issue_date: date = Field(default_factory=date.today)
    due_date: Optional[date] = None
    sent_date: Optional[date] = None
    paid_date: Optional[date] = None
    
    # Financial Details
    subtotal: float = 0.0
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    total_amount: float = 0.0
    paid_amount: float = 0.0
    balance_due: float = 0.0
    
    # Payment Information
    payments: List[PaymentRecord] = []
    payment_terms: Optional[str] = None
    late_fee_rate: float = 0.0
    
    # SOAP Note Integration
    generated_from_soap: bool = False
    soap_encounter_id: Optional[str] = None
    treatment_plan_items: List[str] = []  # IDs of plan items from SOAP
    
    # Insurance Information
    insurance_claim_number: Optional[str] = None
    insurance_authorization: Optional[str] = None
    insurance_copay: float = 0.0
    
    # Notes and Communication
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    patient_message: Optional[str] = None
    
    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_totals(self):
        """Calculate invoice totals"""
        self.subtotal = sum(item.total_price for item in self.items)
        self.tax_amount = sum(item.total_price * (item.tax_rate / 100) for item in self.items)
        self.discount_amount = sum(item.total_price * (item.discount_percentage / 100) for item in self.items)
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.paid_amount = sum(payment.amount for payment in self.payments)
        self.balance_due = self.total_amount - self.paid_amount
        
        # Update status based on payment
        if self.balance_due <= 0 and self.paid_amount > 0:
            self.status = InvoiceStatus.PAID
        elif self.due_date and date.today() > self.due_date and self.balance_due > 0:
            self.status = InvoiceStatus.OVERDUE

class SOAPPlanItem(BaseModel):
    """Item from SOAP note treatment plan"""
    description: str
    item_type: InvoiceItemType
    estimated_cost: float
    quantity: int = 1
    inventory_item_id: Optional[str] = None
    cpt_code: Optional[str] = None
    priority: str = "normal"  # high, normal, low
    notes: Optional[str] = None

class InventoryDeduction(BaseModel):
    """Inventory deduction record"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str
    invoice_item_id: str
    inventory_item_id: str
    quantity_deducted: int
    unit_cost: float
    total_cost: float
    deduction_date: datetime = Field(default_factory=datetime.utcnow)
    deducted_by: str
    reason: str = "Invoice payment processed"
    reversed: bool = False
    reversal_date: Optional[datetime] = None
    reversal_reason: Optional[str] = None

class InvoiceTemplate(BaseModel):
    """Template for common invoice types"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    template_type: str  # consultation, procedure, medication, etc.
    default_items: List[InvoiceItem] = []
    payment_terms: str = "Net 30"
    notes_template: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Receipt Generation Models

class ReceiptFormat(str, Enum):
    STANDARD = "standard"
    DETAILED = "detailed"    
    SUMMARY = "summary"
    INSURANCE = "insurance"

class Receipt(BaseModel):
    """Generated receipt from invoice"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str
    receipt_number: str = Field(default_factory=lambda: f"RCP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}")
    format_type: ReceiptFormat = ReceiptFormat.STANDARD
    
    # Receipt Content
    practice_info: Dict[str, Any] = {}
    patient_info: Dict[str, Any] = {}
    payment_info: Dict[str, Any] = {}
    items_summary: List[Dict[str, Any]] = []
    
    # Generation Details
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str
    printed_at: Optional[datetime] = None
    emailed_at: Optional[datetime] = None
    
    # Content
    receipt_html: Optional[str] = None
    receipt_pdf: Optional[bytes] = None

# Integration Classes

class SOAPInvoiceGenerator:
    """Generate invoices from SOAP note treatment plans"""
    
    @staticmethod
    def create_invoice_from_soap(
        encounter_id: str,
        patient_id: str,
        provider_id: str,
        plan_items: List[SOAPPlanItem],
        notes: Optional[str] = None
    ) -> ComprehensiveInvoice:
        """Create invoice from SOAP note treatment plan"""
        
        invoice_items = []
        for plan_item in plan_items:
            item = InvoiceItem(
                description=plan_item.description,
                item_type=plan_item.item_type,
                quantity=plan_item.quantity,
                unit_price=plan_item.estimated_cost,
                total_price=plan_item.quantity * plan_item.estimated_cost,
                inventory_item_id=plan_item.inventory_item_id,
                cpt_code=plan_item.cpt_code,
                is_service=plan_item.inventory_item_id is None,
                notes=plan_item.notes
            )
            invoice_items.append(item)
        
        invoice = ComprehensiveInvoice(
            patient_id=patient_id,
            encounter_id=encounter_id,
            provider_id=provider_id,
            description=f"Treatment services from encounter {encounter_id}",
            items=invoice_items,
            generated_from_soap=True,
            soap_encounter_id=encounter_id,
            treatment_plan_items=[item.description for item in plan_items],
            notes=notes or "Generated from SOAP note treatment plan",
            created_by=provider_id
        )
        
        invoice.calculate_totals()
        return invoice

class InventoryIntegration:
    """Handle inventory deductions when invoices are paid"""
    
    @staticmethod
    async def process_inventory_deductions(invoice: ComprehensiveInvoice, processed_by: str) -> List[InventoryDeduction]:
        """Process inventory deductions for paid invoice"""
        deductions = []
        
        for item in invoice.items:
            if not item.is_service and item.inventory_item_id:
                deduction = InventoryDeduction(
                    invoice_id=invoice.id,
                    invoice_item_id=item.id,
                    inventory_item_id=item.inventory_item_id,
                    quantity_deducted=item.quantity,
                    unit_cost=item.unit_price,
                    total_cost=item.total_price,
                    deducted_by=processed_by
                )
                deductions.append(deduction)
        
        return deductions
    
    @staticmethod
    async def reverse_inventory_deductions(invoice_id: str, reason: str, reversed_by: str) -> List[InventoryDeduction]:
        """Reverse inventory deductions (for refunds/cancellations)"""
        # Implementation would update existing deduction records
        pass

class ReceiptGenerator:
    """Generate professional receipts from invoices"""
    
    @staticmethod
    def generate_receipt(
        invoice: ComprehensiveInvoice,
        format_type: ReceiptFormat = ReceiptFormat.STANDARD,
        practice_info: Dict[str, Any] = {},
        generated_by: str = ""
    ) -> Receipt:
        """Generate receipt from invoice"""
        
        receipt = Receipt(
            invoice_id=invoice.id,
            format_type=format_type,
            practice_info=practice_info,
            patient_info={
                "id": invoice.patient_id,
                "name": "Patient Name",  # Would be populated from patient data
            },
            payment_info={
                "total_paid": invoice.paid_amount,
                "payment_method": invoice.payments[-1].payment_method.value if invoice.payments else "N/A",
                "payment_date": invoice.payments[-1].payment_date if invoice.payments else None
            },
            items_summary=[{
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total": item.total_price
            } for item in invoice.items],
            generated_by=generated_by
        )
        
        # Generate HTML content
        receipt.receipt_html = ReceiptGenerator._generate_receipt_html(receipt, invoice)
        
        return receipt
    
    @staticmethod
    def _generate_receipt_html(receipt: Receipt, invoice: ComprehensiveInvoice) -> str:
        """Generate HTML receipt content"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Receipt #{receipt.receipt_number}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
                .receipt-info {{ margin: 20px 0; }}
                .items-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .items-table th, .items-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .items-table th {{ background-color: #f2f2f2; }}
                .total {{ text-align: right; font-weight: bold; font-size: 18px; }}
                .payment-info {{ margin-top: 20px; border-top: 1px solid #ddd; padding-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{receipt.practice_info.get('name', 'ClinicHub Practice')}</h1>
                <p>{receipt.practice_info.get('address', '')}</p>
                <p>Phone: {receipt.practice_info.get('phone', '')} | Email: {receipt.practice_info.get('email', '')}</p>
            </div>
            
            <div class="receipt-info">
                <h2>Receipt #{receipt.receipt_number}</h2>
                <p><strong>Date:</strong> {receipt.generated_at.strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>Patient:</strong> {receipt.patient_info.get('name', 'N/A')}</p>
                <p><strong>Invoice:</strong> {invoice.invoice_number}</p>
            </div>
            
            <table class="items-table">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Qty</th>
                        <th>Unit Price</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in receipt.items_summary:
            html += f"""
                    <tr>
                        <td>{item['description']}</td>
                        <td>{item['quantity']}</td>
                        <td>${item['unit_price']:.2f}</td>
                        <td>${item['total']:.2f}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
            </table>
            
            <div class="total">
                <p>Subtotal: ${invoice.subtotal:.2f}</p>
                <p>Tax: ${invoice.tax_amount:.2f}</p>
                <p>Discount: ${invoice.discount_amount:.2f}</p>
                <p><strong>Total: ${invoice.total_amount:.2f}</strong></p>
            </div>
            
            <div class="payment-info">
                <h3>Payment Information</h3>
                <p><strong>Amount Paid:</strong> ${invoice.paid_amount:.2f}</p>
                <p><strong>Payment Method:</strong> {receipt.payment_info.get('payment_method', 'N/A').title()}</p>
                <p><strong>Payment Date:</strong> {receipt.payment_info.get('payment_date', 'N/A')}</p>
                <p><strong>Balance Due:</strong> ${invoice.balance_due:.2f}</p>
            </div>
            
            <div style="margin-top: 40px; text-align: center; font-size: 12px; color: #666;">
                <p>Thank you for your payment!</p>
                <p>This receipt was generated electronically on {receipt.generated_at.strftime('%Y-%m-%d at %H:%M')}</p>
            </div>
        </body>
        </html>
        """
        
        return html

# API Router for Enhanced Invoice Management

invoice_router = APIRouter(prefix="/api/invoices", tags=["invoices"])

@invoice_router.post("/from-soap")
async def create_invoice_from_soap(
    encounter_id: str,
    patient_id: str,
    provider_id: str,
    plan_items: List[SOAPPlanItem]
):
    """Create invoice from SOAP note treatment plan"""
    invoice = SOAPInvoiceGenerator.create_invoice_from_soap(
        encounter_id, patient_id, provider_id, plan_items
    )
    # Save to database
    return invoice

@invoice_router.post("/{invoice_id}/payment")
async def process_payment(invoice_id: str, payment_data: PaymentRecord):
    """Process payment and handle inventory deductions"""
    # Process payment
    # Update invoice status
    # Deduct inventory for non-service items
    # Generate receipt
    pass

@invoice_router.post("/{invoice_id}/receipt")
async def generate_receipt(invoice_id: str, format_type: ReceiptFormat = ReceiptFormat.STANDARD):
    """Generate receipt for invoice"""
    pass

@invoice_router.get("/{invoice_id}/inventory-deductions")
async def get_inventory_deductions(invoice_id: str):
    """Get inventory deductions for invoice"""
    pass

@invoice_router.post("/templates")
async def create_invoice_template(template: InvoiceTemplate):
    """Create invoice template"""
    pass

@invoice_router.get("/templates")
async def get_invoice_templates():
    """Get all invoice templates"""
    pass