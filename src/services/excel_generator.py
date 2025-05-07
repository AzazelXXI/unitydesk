"""
Excel Generator Service

This module provides functionality for generating Excel documents, particularly
for quotes and invoices related to customer service tickets.
"""
import os
from datetime import datetime
import logging
from typing import Dict, Any, List, Optional
import xlsxwriter  # You might need to install: pip install XlsxWriter

# Configure logging
logger = logging.getLogger(__name__)

def generate_excel_quote(ticket, file_path: str, include_logo: bool = True, include_details: bool = True) -> str:
    """
    Generate an Excel quote for a service ticket
    
    Args:
        ticket: The ServiceTicket object with all related data
        file_path: Where to save the generated Excel file
        include_logo: Whether to include company logo
        include_details: Whether to include detailed step information
        
    Returns:
        str: Path to the generated Excel file
    """
    try:
        logger.info(f"Generating Excel quote for ticket {ticket.ticket_code}")
        
        # Create workbook and add a worksheet
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet('Quote')
        
        # Set column widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 12)
        worksheet.set_column('E:E', 15)
        
        # Create formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Arial'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'border': 1,
            'bg_color': '#EEEEEE',
            'font_name': 'Arial'
        })
        
        section_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'font_name': 'Arial'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'font_name': 'Arial'
        })
        
        money_format = workbook.add_format({
            'border': 1,
            'num_format': '$#,##0.00',
            'font_name': 'Arial'
        })
        
        bold_money_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '$#,##0.00',
            'bg_color': '#EEEEEE',
            'font_name': 'Arial'
        })
        
        info_label_format = workbook.add_format({
            'bold': True,
            'font_name': 'Arial'
        })
        
        info_value_format = workbook.add_format({
            'font_name': 'Arial'
        })
        
        # Add company logo
        if include_logo:
            logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'logo.png')
            if os.path.exists(logo_path):
                worksheet.insert_image('A1', logo_path, {'x_scale': 0.5, 'y_scale': 0.5})
        
        # Add title
        worksheet.merge_range('C1:E1', 'SERVICE QUOTE', title_format)
        worksheet.merge_range('C2:E2', f'Quote # {ticket.ticket_code}', section_format)
        worksheet.merge_range('C3:E3', f'Date: {datetime.now().strftime("%Y-%m-%d")}', info_value_format)
        
        # Add client information
        row = 5
        worksheet.write(row, 0, 'Client Information:', section_format)
        row += 1
        
        if ticket.client:
            worksheet.write(row, 0, 'Name:', info_label_format)
            worksheet.write(row, 1, ticket.client.name, info_value_format)
            row += 1
            
            if hasattr(ticket.client, 'email'):
                worksheet.write(row, 0, 'Email:', info_label_format)
                worksheet.write(row, 1, ticket.client.email, info_value_format)
                row += 1
            
            if hasattr(ticket.client, 'phone'):
                worksheet.write(row, 0, 'Phone:', info_label_format)
                worksheet.write(row, 1, ticket.client.phone, info_value_format)
                row += 1
            
            if hasattr(ticket.client, 'address'):
                worksheet.write(row, 0, 'Address:', info_label_format)
                worksheet.write(row, 1, ticket.client.address, info_value_format)
                row += 1
        
        row += 1
        
        # Add service information
        worksheet.write(row, 0, 'Service Details:', section_format)
        row += 1
        
        worksheet.write(row, 0, 'Title:', info_label_format)
        worksheet.merge_range(f'B{row+1}:E{row+1}', ticket.title, info_value_format)
        row += 1
        
        worksheet.write(row, 0, 'Description:', info_label_format)
        worksheet.merge_range(f'B{row+1}:E{row+1}', ticket.description, info_value_format)
        row += 2
        
        if ticket.sales_rep:
            worksheet.write(row, 0, 'Sales Rep:', info_label_format)
            rep_name = f"{ticket.sales_rep.first_name} {ticket.sales_rep.last_name}"
            worksheet.write(row, 1, rep_name, info_value_format)
            row += 1
        
        row += 1
        
        # Add quote items
        worksheet.write(row, 0, 'Quote Items:', section_format)
        row += 1
        
        # Table header
        worksheet.write(row, 0, 'Item', header_format)
        worksheet.merge_range(f'B{row+1}:C{row+1}', 'Description', header_format)
        worksheet.write(row, 3, 'Unit Price', header_format)
        worksheet.write(row, 4, 'Total', header_format)
        row += 1
        
        # Table rows
        item_num = 1
        if ticket.ticket_steps:
            for step in ticket.ticket_steps:
                step_name = step.step.name if step.step else "Unknown Step"
                
                worksheet.write(row, 0, f"Item {item_num}", cell_format)
                worksheet.merge_range(f'B{row+1}:C{row+1}', step_name, cell_format)
                worksheet.write(row, 3, step.unit_price, money_format)
                worksheet.write(row, 4, step.total_price, money_format)
                row += 1
                
                # Add details if requested
                if include_details and step.step and step.step.description:
                    worksheet.merge_range(f'B{row+1}:E{row+1}', step.step.description, info_value_format)
                    row += 1
                
                item_num += 1
        
        # Add total
        worksheet.merge_range(f'A{row+1}:D{row+1}', 'TOTAL', header_format)
        worksheet.write(row, 4, ticket.total_price, bold_money_format)
        row += 2
        
        # Add terms and conditions
        worksheet.write(row, 0, 'Terms and Conditions:', section_format)
        row += 1
        worksheet.merge_range(f'A{row+1}:E{row+1}', '1. This quote is valid for 30 days from the date of issue.', info_value_format)
        row += 1
        worksheet.merge_range(f'A{row+1}:E{row+1}', '2. Payment terms: 50% deposit required to begin work, balance due upon completion.', info_value_format)
        row += 1
        worksheet.merge_range(f'A{row+1}:E{row+1}', '3. Estimated completion time may vary based on complexity and availability.', info_value_format)
        row += 1
        worksheet.merge_range(f'A{row+1}:E{row+1}', '4. Additional charges may apply for work outside the scope of this quote.', info_value_format)
        row += 1
        worksheet.merge_range(f'A{row+1}:E{row+1}', '5. All prices are exclusive of applicable taxes.', info_value_format)
        
        # Close the workbook
        workbook.close()
        logger.info(f"Excel quote successfully generated and saved to {file_path}")
        
        return file_path
    
    except Exception as e:
        logger.error(f"Failed to generate Excel quote: {str(e)}")
        # Clean up any partially created file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
