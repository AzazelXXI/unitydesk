"""
PDF Generator Service

This module provides functionality for generating PDF documents, particularly
for quotes and invoices related to customer service tickets.
"""
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from fpdf import FPDF  # You might need to install: pip install fpdf

# Configure logging
logger = logging.getLogger(__name__)

class QuotePDF(FPDF):
    """Custom PDF class with header and footer for quotes"""
    
    def __init__(self, company_name="CSA Platform", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_name = company_name
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        """Add custom header to each page"""
        # Logo
        if hasattr(self, 'include_logo') and self.include_logo:
            logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'logo.png')
            if os.path.exists(logo_path):
                self.image(logo_path, x=10, y=8, w=30)
        
        # Company name
        self.set_font('Arial', 'B', 15)
        self.cell(30)  # Move to the right after logo
        self.cell(0, 10, self.company_name, 0, 0, 'L')
        
        # Quote title
        self.set_font('Arial', 'B', 15)
        self.cell(-30)  # Adjust position
        self.cell(0, 10, 'QUOTE', 0, 0, 'R')
        
        # Line break
        self.ln(20)
    
    def footer(self):
        """Add custom footer to each page"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        
        # Page number
        page_text = f'Page {self.page_no()}/{{nb}}'
        self.cell(0, 10, page_text, 0, 0, 'C')
        
        # Date
        date_text = f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        self.cell(0, 10, date_text, 0, 0, 'R')


def generate_pdf_quote(ticket, file_path: str, include_logo: bool = True, include_details: bool = True) -> str:
    """
    Generate a PDF quote for a service ticket
    
    Args:
        ticket: The ServiceTicket object with all related data
        file_path: Where to save the generated PDF
        include_logo: Whether to include company logo
        include_details: Whether to include detailed step information
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        logger.info(f"Generating PDF quote for ticket {ticket.ticket_code}")
        
        # Create PDF object
        pdf = QuotePDF(orientation='P', unit='mm', format='A4')
        pdf.include_logo = include_logo
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Customer and Quote Information
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Client Information', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        # Client info
        if ticket.client:
            pdf.cell(0, 6, f'Client: {ticket.client.name}', 0, 1)
            if hasattr(ticket.client, 'address'):
                pdf.cell(0, 6, f'Address: {ticket.client.address}', 0, 1)
            if hasattr(ticket.client, 'email'):
                pdf.cell(0, 6, f'Email: {ticket.client.email}', 0, 1)
            if hasattr(ticket.client, 'phone'):
                pdf.cell(0, 6, f'Phone: {ticket.client.phone}', 0, 1)
        
        pdf.ln(5)
        
        # Quote info
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Quote Information', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'Quote Number: {ticket.ticket_code}', 0, 1)
        pdf.cell(0, 6, f'Date: {datetime.now().strftime("%Y-%m-%d")}', 0, 1)
        
        if ticket.sales_rep:
            pdf.cell(0, 6, f'Sales Rep: {ticket.sales_rep.first_name} {ticket.sales_rep.last_name}', 0, 1)
        
        pdf.ln(5)
        
        # Quote title/description
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Service Details', 0, 1)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 6, f'{ticket.title}', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, f'{ticket.description}')
        pdf.ln(5)
        
        # Line items (steps)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Quote Items', 0, 1)
        
        # Table header
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(90, 8, 'Description', 1, 0, 'L', 1)
        pdf.cell(25, 8, 'Quantity', 1, 0, 'C', 1)
        pdf.cell(35, 8, 'Unit Price', 1, 0, 'R', 1)
        pdf.cell(40, 8, 'Total', 1, 1, 'R', 1)
        
        # Table rows
        pdf.set_font('Arial', '', 10)
        
        if ticket.ticket_steps:
            for step in ticket.ticket_steps:
                step_name = step.step.name if step.step else "Unknown Step"
                
                # Handle long descriptions by wrapping text
                pdf.cell(90, 8, step_name, 1, 0, 'L')
                pdf.cell(25, 8, f"{step.quantity}", 1, 0, 'C')
                pdf.cell(35, 8, f"${step.unit_price:.2f}", 1, 0, 'R')
                pdf.cell(40, 8, f"${step.total_price:.2f}", 1, 1, 'R')
                
                # Add details if requested
                if include_details and step.step and step.step.description:
                    pdf.set_font('Arial', 'I', 9)
                    pdf.cell(10)  # Indent
                    pdf.multi_cell(180, 6, step.step.description)
                    pdf.set_font('Arial', '', 10)
        
        # Total
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(150, 8, 'Total', 1, 0, 'R', 1)
        pdf.cell(40, 8, f"${ticket.total_price:.2f}", 1, 1, 'R', 1)
        
        pdf.ln(10)
        
        # Terms and conditions
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Terms and Conditions', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, """
1. This quote is valid for 30 days from the date of issue.
2. Payment terms: 50% deposit required to begin work, balance due upon completion.
3. Estimated completion time may vary based on complexity and availability.
4. Additional charges may apply for work outside the scope of this quote.
5. All prices are exclusive of applicable taxes.
        """)
        
        # Save the PDF
        pdf.output(file_path)
        logger.info(f"PDF quote successfully generated and saved to {file_path}")
        
        return file_path
    
    except Exception as e:
        logger.error(f"Failed to generate PDF quote: {str(e)}")
        # Clean up any partially created file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
