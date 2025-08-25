# ClinicHub PDF Generation Utilities - Latest Working Version
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import base64

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for ClinicHub documents"""
        self.styles.add(ParagraphStyle(
            name='ClinicHubHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.blue
        ))
        
        self.styles.add(ParagraphStyle(
            name='ClinicHubSubHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.darkblue
        ))
    
    def generate_receipt_pdf(self, receipt_data: dict) -> bytes:
        """Generate receipt PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Build content
        content = []
        
        # Header
        content.append(Paragraph("🏥 ClinicHub", self.styles['ClinicHubHeader']))
        content.append(Paragraph("PAYMENT RECEIPT", self.styles['ClinicHubSubHeader']))
        content.append(Spacer(1, 20))
        
        # Receipt details
        receipt_info = [
            ['Receipt Number:', receipt_data.get('receipt_number', 'N/A')],
            ['Date:', datetime.now().strftime('%B %d, %Y')],
            ['Patient ID:', receipt_data.get('patient_id', 'N/A')],
            ['Payment Method:', receipt_data.get('payment_method', 'Cash').title()]
        ]
        
        info_table = Table(receipt_info, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))
        
        content.append(info_table)
        content.append(Spacer(1, 30))
        
        # Services table
        services_data = [['Service', 'Amount']]
        for service in receipt_data.get('services', []):
            services_data.append([service.get('description', ''), f"${service.get('amount', 0):.2f}"])
        
        # Add totals
        services_data.append(['', ''])  # Spacer
        services_data.append(['Subtotal:', f"${receipt_data.get('amount', 0):.2f}"])
        services_data.append(['Tax:', f"${receipt_data.get('tax_amount', 0):.2f}"])
        services_data.append(['Total:', f"${receipt_data.get('total_amount', 0):.2f}"])
        
        services_table = Table(services_data, colWidths=[4*inch, 1.5*inch])
        services_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,-3), (-1,-1), 'Helvetica-Bold'),
            ('LINEBELOW', (0,0), (-1,0), 2, colors.black),
            ('LINEABOVE', (0,-3), (-1,-3), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        
        content.append(services_table)
        
        # Build PDF
        doc.build(content)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_paystub_pdf(self, payroll_data: dict) -> bytes:
        """Generate employee paystub PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        content = []
        
        # Header
        content.append(Paragraph("🏥 ClinicHub", self.styles['ClinicHubHeader']))
        content.append(Paragraph("EMPLOYEE PAYSTUB", self.styles['ClinicHubSubHeader']))
        content.append(Spacer(1, 20))
        
        # Employee info
        emp_info = [
            ['Employee:', payroll_data.get('employee_name', 'N/A')],
            ['Employee ID:', payroll_data.get('employee_id', 'N/A')],
            ['Pay Period:', f"{payroll_data.get('period_start', '')} - {payroll_data.get('period_end', '')}"],
            ['Pay Date:', payroll_data.get('pay_date', datetime.now().strftime('%Y-%m-%d'))]
        ]
        
        emp_table = Table(emp_info, colWidths=[2*inch, 3*inch])
        emp_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        
        content.append(emp_table)
        content.append(Spacer(1, 30))
        
        # Earnings and deductions
        earnings_data = [
            ['EARNINGS', 'HOURS', 'RATE', 'AMOUNT'],
            ['Regular Pay', str(payroll_data.get('regular_hours', 0)), 
             f"${payroll_data.get('hourly_rate', 0):.2f}", 
             f"${payroll_data.get('regular_pay', 0):.2f}"],
            ['Overtime Pay', str(payroll_data.get('overtime_hours', 0)), 
             f"${payroll_data.get('overtime_rate', 0):.2f}", 
             f"${payroll_data.get('overtime_pay', 0):.2f}"],
            ['', '', 'Gross Pay:', f"${payroll_data.get('gross_pay', 0):.2f}"]
        ]
        
        earnings_table = Table(earnings_data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch])
        earnings_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('LINEBELOW', (0,0), (-1,0), 2, colors.black),
            ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
        ]))
        
        content.append(earnings_table)
        content.append(Spacer(1, 20))
        
        # Deductions
        deductions_data = [
            ['DEDUCTIONS', 'AMOUNT'],
            ['Federal Tax', f"${payroll_data.get('federal_tax', 0):.2f}"],
            ['State Tax', f"${payroll_data.get('state_tax', 0):.2f}"],
            ['Social Security', f"${payroll_data.get('social_security', 0):.2f}"],
            ['Medicare', f"${payroll_data.get('medicare', 0):.2f}"],
            ['Total Deductions:', f"${payroll_data.get('total_deductions', 0):.2f}"],
            ['', ''],
            ['NET PAY:', f"${payroll_data.get('net_pay', 0):.2f}"]
        ]
        
        deductions_table = Table(deductions_data, colWidths=[3*inch, 2*inch])
        deductions_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,-2), (-1,-1), 'Helvetica-Bold'),
            ('LINEBELOW', (0,0), (-1,0), 2, colors.black),
            ('LINEABOVE', (0,-2), (-1,-2), 1, colors.black),
            ('ALIGN', (1,1), (1,-1), 'RIGHT'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('FONTSIZE', (0,-1), (-1,-1), 14),
        ]))
        
        content.append(deductions_table)
        
        doc.build(content)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_clinical_report_pdf(self, report_data: dict) -> bytes:
        """Generate clinical quality report PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        content = []
        
        # Header
        content.append(Paragraph("🏥 ClinicHub Clinical Quality Report", self.styles['ClinicHubHeader']))
        content.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        content.append(Spacer(1, 30))
        
        # Quality measures summary
        measures_data = [['Quality Measure', 'Target', 'Current', 'Status']]
        for measure in report_data.get('measures', []):
            status = "✅ Met" if measure.get('current_value', 0) >= measure.get('target_value', 0) else "❌ Not Met"
            measures_data.append([
                measure.get('name', ''),
                f"{measure.get('target_value', 0)}%",
                f"{measure.get('current_value', 0)}%",
                status
            ])
        
        measures_table = Table(measures_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        measures_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('LINEBELOW', (0,0), (-1,0), 2, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ]))
        
        content.append(measures_table)
        
        doc.build(content)
        buffer.seek(0)
        return buffer.getvalue()

# Export utilities
def export_to_base64(pdf_bytes: bytes) -> str:
    """Convert PDF bytes to base64 for API response"""
    return base64.b64encode(pdf_bytes).decode('utf-8')

async def get_database():
    pass