from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, func
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import os
import uuid
from fastapi import HTTPException, status
import re

from src.models.customer_service import (
    ServiceTicket, ServiceStep, TicketStep, QuoteDocument, 
    TicketStatus, StepStatus, DocumentType
)
from src.schemas.customer_service import (
    ServiceTicketCreate, ServiceTicketUpdate, 
    ServiceStepCreate, ServiceStepUpdate,
    TicketStepCreate, TicketStepUpdate,
    QuoteDocumentCreate
)
from src.services.pdf_generator import generate_pdf_quote
from src.services.excel_generator import generate_excel_quote
from src.controllers.task_controller import TaskController

# Configure logging
logger = logging.getLogger(__name__)

class CustomerServiceController:
    """Controller for handling customer service operations"""
    
    @staticmethod
    async def generate_ticket_code() -> str:
        """
        Generate a unique ticket code in the format YYMM-XXXX
        where XX is year, MM is month, and XXXX is a sequential number
        """
        now = datetime.now()
        year_month = now.strftime("%y%m")  # Format: YYMM
        
        # Get the highest ticket number for the current year-month
        async def get_highest_ticket_number(db):
            pattern = f"{year_month}-%"
            query = select(ServiceTicket.ticket_code).filter(
                ServiceTicket.ticket_code.like(pattern)
            ).order_by(desc(ServiceTicket.ticket_code))
            
            result = await db.execute(query)
            latest_code = result.scalar_one_or_none()
            
            if not latest_code:
                return 0
                
            # Extract the sequential number
            match = re.search(r'-(\d+)$', latest_code)
            if match:
                return int(match.group(1))
            return 0
        
        # Format: YYMM-XXXX
        return f"{year_month}-{sequence_number:04d}"
    
    @staticmethod
    async def create_service_ticket(
        ticket_data: ServiceTicketCreate,
        db: AsyncSession
    ) -> ServiceTicket:
        """
        Create a new service ticket
        """
        try:
            # Generate ticket code
            ticket_code = await CustomerServiceController.generate_ticket_code(db)
            
            # Create ticket
            new_ticket = ServiceTicket(
                ticket_code=ticket_code,
                client_id=ticket_data.client_id,
                sales_rep_id=ticket_data.sales_rep_id,
                title=ticket_data.title,
                description=ticket_data.description,
                priority=ticket_data.priority,
                estimated_completion=ticket_data.estimated_completion,
                status=TicketStatus.NEW
            )
            
            db.add(new_ticket)
            await db.commit()
            await db.refresh(new_ticket)
            
            logger.info(f"Created new service ticket: {new_ticket.ticket_code}")
            
            # Initialize first step automatically
            await CustomerServiceController.initialize_first_step(new_ticket.id, db)
            
            # Return the ticket with all related info
            return await CustomerServiceController.get_service_ticket(new_ticket.id, db)
        except Exception as e:
            logger.error(f"Error creating service ticket: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create service ticket: {str(e)}"
            )
    
    @staticmethod
    async def initialize_first_step(ticket_id: int, db: AsyncSession) -> None:
        """
        Initialize the first step for a new ticket
        """
        try:
            # Get the first active step in the service process
            query = select(ServiceStep).filter(
                ServiceStep.is_active == True
            ).order_by(ServiceStep.order).limit(1)
            
            result = await db.execute(query)
            first_step = result.scalar_one_or_none()
            
            if not first_step:
                logger.warning("No active service steps found to initialize")
                return
            
            # Create ticket step
            new_ticket_step = TicketStep(
                ticket_id=ticket_id,
                step_id=first_step.id,
                status=StepStatus.PENDING,
                unit_price=first_step.base_price,
                total_price=first_step.base_price  # Initial price is base price × quantity=1
            )
            
            db.add(new_ticket_step)
            await db.commit()
            
            logger.info(f"Initialized first step '{first_step.name}' for ticket {ticket_id}")
        except Exception as e:
            logger.error(f"Error initializing first step for ticket {ticket_id}: {str(e)}")
            await db.rollback()
            raise
    
    @staticmethod
    async def get_service_tickets(
        client_id: Optional[int] = None,
        status: Optional[TicketStatus] = None,
        sales_rep_id: Optional[int] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = None
    ) -> List[ServiceTicket]:
        """
        Get service tickets with optional filtering
        """
        try:
            query = select(ServiceTicket).options(
                joinedload(ServiceTicket.client),
                joinedload(ServiceTicket.sales_rep)
            )
            
            # Apply filters
            if client_id:
                query = query.filter(ServiceTicket.client_id == client_id)
            if status:
                query = query.filter(ServiceTicket.status == status)
            if sales_rep_id:
                query = query.filter(ServiceTicket.sales_rep_id == sales_rep_id)
            if search:
                query = query.filter(
                    (ServiceTicket.title.ilike(f"%{search}%")) |
                    (ServiceTicket.ticket_code.ilike(f"%{search}%"))
                )
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            query = query.order_by(desc(ServiceTicket.created_at))
            
            result = await db.execute(query)
            tickets = result.scalars().unique().all()
            
            return tickets
        except Exception as e:
            logger.error(f"Error fetching service tickets: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch service tickets: {str(e)}"
            )
    
    @staticmethod
    async def get_service_ticket(ticket_id: int, db: AsyncSession) -> ServiceTicket:
        """
        Get a specific service ticket with all related data
        """
        try:
            query = select(ServiceTicket).filter(
                ServiceTicket.id == ticket_id
            ).options(
                joinedload(ServiceTicket.client),
                joinedload(ServiceTicket.sales_rep),
                joinedload(ServiceTicket.ticket_steps).joinedload(TicketStep.step),
                joinedload(ServiceTicket.ticket_steps).joinedload(TicketStep.assigned_staff),
                joinedload(ServiceTicket.quotes).joinedload(QuoteDocument.created_by)
            )
            
            result = await db.execute(query)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                logger.warning(f"Service ticket with ID {ticket_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Service ticket with ID {ticket_id} not found"
                )
            
            return ticket
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching service ticket {ticket_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch service ticket: {str(e)}"
            )
    
    @staticmethod
    async def update_service_ticket(
        ticket_id: int,
        ticket_data: ServiceTicketUpdate,
        db: AsyncSession
    ) -> ServiceTicket:
        """
        Update a service ticket
        """
        try:
            # Get the ticket
            query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
            result = await db.execute(query)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                logger.warning(f"Service ticket with ID {ticket_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Service ticket with ID {ticket_id} not found"
                )
            
            # Update ticket attributes
            update_data = ticket_data.dict(exclude_unset=True)
            
            # Special handling for status changes
            if "status" in update_data and update_data["status"] != ticket.status:
                if update_data["status"] == TicketStatus.COMPLETED and not ticket.actual_completion:
                    update_data["actual_completion"] = datetime.utcnow()
            
            # Apply updates
            for key, value in update_data.items():
                setattr(ticket, key, value)
            
            await db.commit()
            await db.refresh(ticket)
            
            logger.info(f"Updated service ticket {ticket_id}")
            
            # Return the updated ticket with all related info
            return await CustomerServiceController.get_service_ticket(ticket_id, db)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating service ticket {ticket_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update service ticket: {str(e)}"
            )
    
    @staticmethod
    async def delete_service_ticket(ticket_id: int, db: AsyncSession) -> None:
        """
        Delete a service ticket
        """
        try:
            # Get the ticket
            query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
            result = await db.execute(query)
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                logger.warning(f"Service ticket with ID {ticket_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Service ticket with ID {ticket_id} not found"
                )
            
            # Check if there are any completed steps
            has_completed_steps = any(step.status == StepStatus.COMPLETED for step in ticket.ticket_steps)
            if has_completed_steps:
                logger.warning(f"Cannot delete ticket {ticket_id} with completed steps")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete ticket with completed steps"
                )
                
            # Delete the ticket and related records (cascade will handle ticket_steps and quotes)
            await db.delete(ticket)
            await db.commit()
            
            logger.info(f"Deleted service ticket {ticket_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting service ticket {ticket_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete service ticket: {str(e)}"
            )
    
    @staticmethod
    async def create_service_step(
        step_data: ServiceStepCreate,
        db: AsyncSession
    ) -> ServiceStep:
        """
        Create a new service step definition
        """
        try:
            # Create the step
            new_step = ServiceStep(
                name=step_data.name,
                description=step_data.description,
                order=step_data.order,
                is_active=step_data.is_active,
                estimated_duration_hours=step_data.estimated_duration_hours,
                pricing_model=step_data.pricing_model,
                base_price=step_data.base_price
            )
            
            db.add(new_step)
            await db.commit()
            await db.refresh(new_step)
            
            logger.info(f"Created new service step: {new_step.name}")
            
            return new_step
        except Exception as e:
            logger.error(f"Error creating service step: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create service step: {str(e)}"
            )
    
    @staticmethod
    async def get_service_steps(
        is_active: Optional[bool] = None,
        db: AsyncSession = None
    ) -> List[ServiceStep]:
        """
        Get all service steps with optional filtering
        """
        try:
            query = select(ServiceStep)
            
            if is_active is not None:
                query = query.filter(ServiceStep.is_active == is_active)
            
            query = query.order_by(ServiceStep.order)
            
            result = await db.execute(query)
            steps = result.scalars().all()
            
            return steps
        except Exception as e:
            logger.error(f"Error fetching service steps: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch service steps: {str(e)}"
            )
    
    @staticmethod
    async def update_service_step(
        step_id: int,
        step_data: ServiceStepUpdate,
        db: AsyncSession
    ) -> ServiceStep:
        """
        Update a service step
        """
        try:
            # Get the step
            query = select(ServiceStep).filter(ServiceStep.id == step_id)
            result = await db.execute(query)
            step = result.scalar_one_or_none()
            
            if not step:
                logger.warning(f"Service step with ID {step_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Service step with ID {step_id} not found"
                )
            
            # Update step attributes
            update_data = step_data.dict(exclude_unset=True)
            
            for key, value in update_data.items():
                setattr(step, key, value)
            
            await db.commit()
            await db.refresh(step)
            
            logger.info(f"Updated service step {step_id}")
            
            return step
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating service step {step_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update service step: {str(e)}"
            )
    
    @staticmethod
    async def add_step_to_ticket(
        ticket_id: int,
        step_data: TicketStepCreate,
        db: AsyncSession
    ) -> TicketStep:
        """
        Add a step to an existing ticket
        """
        try:
            # Verify the ticket exists
            ticket_query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
            ticket_result = await db.execute(ticket_query)
            ticket = ticket_result.scalar_one_or_none()
            
            if not ticket:
                logger.warning(f"Service ticket with ID {ticket_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Service ticket with ID {ticket_id} not found"
                )
            
            # Verify the step exists
            step_query = select(ServiceStep).filter(ServiceStep.id == step_data.step_id)
            step_result = await db.execute(step_query)
            step = step_result.scalar_one_or_none()
            
            if not step:
                logger.warning(f"Service step with ID {step_data.step_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Service step with ID {step_data.step_id} not found"
                )
            
            # Check if step is already added to the ticket
            existing_query = select(TicketStep).filter(
                TicketStep.ticket_id == ticket_id,
                TicketStep.step_id == step_data.step_id
            )
            existing_result = await db.execute(existing_query)
            existing_step = existing_result.scalar_one_or_none()
            
            if existing_step:
                logger.warning(f"Step {step_data.step_id} already exists for ticket {ticket_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Step already exists for this ticket"
                )
            
            # Calculate total price
            total_price = step_data.unit_price * step_data.quantity
            
            # Create the ticket step
            new_ticket_step = TicketStep(
                ticket_id=ticket_id,
                step_id=step_data.step_id,
                assigned_staff_id=step_data.assigned_staff_id,
                quantity=step_data.quantity,
                unit_price=step_data.unit_price,
                total_price=total_price,
                notes=step_data.notes,
                status=StepStatus.PENDING
            )
            
            db.add(new_ticket_step)
            
            # Update the total price of the ticket
            ticket.total_price += total_price
            
            await db.commit()
            await db.refresh(new_ticket_step)
            
            logger.info(f"Added step {step_data.step_id} to ticket {ticket_id}")
            
            # Return the step with related info
            return await CustomerServiceController.get_ticket_step(ticket_id, new_ticket_step.id, db)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding step to ticket {ticket_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add step to ticket: {str(e)}"
            )
    
    @staticmethod
    async def get_ticket_step(
        ticket_id: int,
        step_id: int,
        db: AsyncSession
    ) -> TicketStep:
        """
        Get a specific ticket step with all related data
        """
        try:
            query = select(TicketStep).filter(
                TicketStep.ticket_id == ticket_id,
                TicketStep.id == step_id
            ).options(
                joinedload(TicketStep.step),
                joinedload(TicketStep.assigned_staff)
            )
            
            result = await db.execute(query)
            ticket_step = result.scalar_one_or_none()
            
            if not ticket_step:
                logger.warning(f"Step with ID {step_id} not found for ticket {ticket_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Step with ID {step_id} not found for ticket {ticket_id}"
                )
            
            return ticket_step
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching step {step_id} for ticket {ticket_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch ticket step: {str(e)}"
            )
    
    @staticmethod
    async def update_ticket_step(
        ticket_id: int,
        step_id: int,
        step_data: TicketStepUpdate,
        db: AsyncSession
    ) -> TicketStep:
        """
        Update a ticket step
        """
        try:
            # Get the ticket step
            query = select(TicketStep).filter(
                TicketStep.ticket_id == ticket_id,
                TicketStep.id == step_id
            )
            result = await db.execute(query)
            ticket_step = result.scalar_one_or_none()
            
            if not ticket_step:
                logger.warning(f"Step with ID {step_id} not found for ticket {ticket_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Step with ID {step_id} not found for ticket {ticket_id}"
                )
            
            # Update step attributes
            update_data = step_data.dict(exclude_unset=True)
            
            # If quantity or unit_price is updated, recalculate total_price
            if "quantity" in update_data or "unit_price" in update_data:
                quantity = update_data.get("quantity", ticket_step.quantity)
                unit_price = update_data.get("unit_price", ticket_step.unit_price)
                
                # Update the ticket total price
                old_total = ticket_step.total_price
                new_total = quantity * unit_price
                
                # Get the ticket
                ticket_query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
                ticket_result = await db.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if ticket:
                    ticket.total_price += (new_total - old_total)
                
                update_data["total_price"] = new_total
            
            # If status is changed to IN_PROGRESS, set start_date
            if "status" in update_data:
                if update_data["status"] == StepStatus.IN_PROGRESS and not ticket_step.start_date:
                    update_data["start_date"] = datetime.utcnow()
                
                # If status is changed to COMPLETED, set completion_date
                if update_data["status"] == StepStatus.COMPLETED and not ticket_step.completion_date:
                    update_data["completion_date"] = datetime.utcnow()
                    
                    # Check if this is the last step
                    await CustomerServiceController._check_next_step(ticket_id, ticket_step, db)
            
            # Apply updates
            for key, value in update_data.items():
                setattr(ticket_step, key, value)
            
            await db.commit()
            await db.refresh(ticket_step)
            
            logger.info(f"Updated step {step_id} for ticket {ticket_id}")
            
            # Return the updated step with related info
            return await CustomerServiceController.get_ticket_step(ticket_id, step_id, db)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating step {step_id} for ticket {ticket_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update ticket step: {str(e)}"
            )
    
    @staticmethod
    async def _check_next_step(ticket_id: int, completed_step: TicketStep, db: AsyncSession) -> None:
        """
        Check for the next step and create a task for the assigned staff
        """
        try:
            # Get the current step definition
            current_step_query = select(ServiceStep).filter(
                ServiceStep.id == completed_step.step_id
            )
            current_step_result = await db.execute(current_step_query)
            current_step = current_step_result.scalar_one_or_none()
            
            if not current_step:
                return
            
            # Find the next step in order
            next_step_query = select(ServiceStep).filter(
                ServiceStep.order > current_step.order,
                ServiceStep.is_active == True
            ).order_by(ServiceStep.order).limit(1)
            
            next_step_result = await db.execute(next_step_query)
            next_step = next_step_result.scalar_one_or_none()
            
            if not next_step:
                # This was the last step - update the ticket status to COMPLETED
                ticket_query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
                ticket_result = await db.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if ticket:
                    ticket.status = TicketStatus.COMPLETED
                    ticket.actual_completion = datetime.utcnow()
                    await db.commit()
                return
            
            # Check if the next step is already added to the ticket
            existing_query = select(TicketStep).filter(
                TicketStep.ticket_id == ticket_id,
                TicketStep.step_id == next_step.id
            )
            existing_result = await db.execute(existing_query)
            existing_step = existing_result.scalar_one_or_none()
            
            if existing_step:
                # Next step already exists - just update the ticket status if needed
                ticket_query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
                ticket_result = await db.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if ticket and ticket.status == TicketStatus.NEW:
                    ticket.status = TicketStatus.IN_PROGRESS
                    await db.commit()
                return
            
            # Add the next step to the ticket
            new_ticket_step = TicketStep(
                ticket_id=ticket_id,
                step_id=next_step.id,
                status=StepStatus.PENDING,
                unit_price=next_step.base_price,
                total_price=next_step.base_price
            )
            
            db.add(new_ticket_step)
            
            # Update the ticket
            ticket_query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
            ticket_result = await db.execute(ticket_query)
            ticket = ticket_result.scalar_one_or_none()
            
            if ticket:
                if ticket.status == TicketStatus.NEW:
                    ticket.status = TicketStatus.IN_PROGRESS
                
                ticket.total_price += next_step.base_price
            
            await db.commit()
            await db.refresh(new_ticket_step)
            
            logger.info(f"Added next step {next_step.name} to ticket {ticket_id}")
            
            # Create a task for the staff assigned to the next step
            # This depends on the task controller implementation
            # TaskController.create_task(...)
        except Exception as e:
            logger.error(f"Error processing next step for ticket {ticket_id}: {str(e)}")
            raise
    
    @staticmethod
    async def complete_step(
        ticket_id: int,
        step_id: int,
        notes: Optional[str],
        db: AsyncSession
    ) -> TicketStep:
        """
        Mark a ticket step as completed and trigger the next step
        """
        try:
            # Update the step status
            step_update = TicketStepUpdate(
                status=StepStatus.COMPLETED,
                notes=notes
            )
            
            return await CustomerServiceController.update_ticket_step(
                ticket_id, step_id, step_update, db
            )
        except Exception as e:
            logger.error(f"Error completing step {step_id} for ticket {ticket_id}: {str(e)}")
            raise
    
    @staticmethod
    async def generate_quote(
        ticket_id: int,
        document_type: DocumentType,
        created_by_id: int,
        include_logo: bool = True,
        include_details: bool = True,
        db: AsyncSession
    ) -> QuoteDocument:
        """
        Generate a quote document (PDF or Excel) for a ticket
        """
        try:
            # Get the ticket with all necessary details
            ticket = await CustomerServiceController.get_service_ticket(ticket_id, db)
            
            # Create file path for the quote
            upload_dir = f"uploads/quotes/{ticket_id}"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            file_name = f"quote_{ticket.ticket_code}_{uuid.uuid4()}"
            
            if document_type == DocumentType.PDF:
                file_path = f"{upload_dir}/{file_name}.pdf"
                # In a real implementation, this would call a PDF generator
                # generate_pdf_quote(ticket, file_path, include_logo, include_details)
                # For now we create an empty file
                with open(file_path, "w") as f:
                    f.write(f"Quote for {ticket.ticket_code}")
            else:  # XLSX
                file_path = f"{upload_dir}/{file_name}.xlsx"
                # In a real implementation, this would call an Excel generator
                # generate_excel_quote(ticket, file_path, include_logo, include_details)
                # For now we create an empty file
                with open(file_path, "w") as f:
                    f.write(f"Quote for {ticket.ticket_code}")
            
            # Create quote document record
            new_quote = QuoteDocument(
                ticket_id=ticket_id,
                document_type=document_type,
                file_path=file_path,
                created_by_id=created_by_id,
                is_sent=False
            )
            
            db.add(new_quote)
            await db.commit()
            await db.refresh(new_quote)
            
            logger.info(f"Generated {document_type} quote for ticket {ticket_id}")
            
            return new_quote
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating quote for ticket {ticket_id}: {str(e)}")
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate quote: {str(e)}"
            )
    
    @staticmethod
    async def update_quote_document(
        quote_id: int,
        is_sent: bool,
        db: AsyncSession
    ) -> QuoteDocument:
        """
        Mark a quote document as sent
        """
        try:
            # Get the quote document
            query = select(QuoteDocument).filter(QuoteDocument.id == quote_id)
            result = await db.execute(query)
            quote = result.scalar_one_or_none()
            
            if not quote:
                logger.warning(f"Quote document with ID {quote_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Quote document with ID {quote_id} not found"
                )
            
            # Update sent status
            quote.is_sent = is_sent
            if is_sent and not quote.sent_at:
                quote.sent_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(quote)
            
            logger.info(f"Updated quote document {quote_id} sent status to {is_sent}")
            
            return quote
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating quote document {quote_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update quote document: {str(e)}"
            )
