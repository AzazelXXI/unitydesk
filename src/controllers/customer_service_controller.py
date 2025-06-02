from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, func
from typing import List, Optional, Dict, Any
import re
from datetime import datetime
import os
import uuid
from fastapi import HTTPException, status

# Commented out imports as per the code change suggestion
# from src.models.customer_service import ( # Changed path
#     ServiceTicket, ServiceStep, TicketStep, QuoteDocument,
#     TicketStatus, StepStatus, DocumentType
# )
# from src.schemas.customer_service import (
#     ServiceTicketCreate, ServiceTicketUpdate,
#     ServiceStepCreate, ServiceStepUpdate,
#     TicketStepCreate, TicketStepUpdate,
#     QuoteDocumentCreate
# )
# from src.services.pdf_generator import generate_pdf_quote
# from src.services.excel_generator import generate_excel_quote
# from src.controllers.task_controller import TaskController

# Configure logging
# logger = logging.getLogger(__name__)


class CustomerServiceController:
    """Controller for handling customer service operations"""

    @staticmethod
    async def generate_ticket_code(db: AsyncSession) -> str:
        """
        Generate a unique ticket code in the format YYMM-XXXX
        where XX is year, MM is month, and XXXX is a sequential number
        """
        now = datetime.now()
        year_month = now.strftime("%y%m")  # Format: YYMM

        # Get the highest ticket number for the current year-month
        pattern = f"{year_month}-%"
        # query = select(ServiceTicket.ticket_code).filter(
        #     ServiceTicket.ticket_code.like(pattern)
        # ).order_by(desc(ServiceTicket.ticket_code))

        # result = await db.execute(query)
        # latest_code = result.scalar_one_or_none()

        # if not latest_code:
        #     sequence_number = 1
        # else:
        #     # Extract the sequential number
        #     match = re.search(r'-(\d+)$', latest_code)
        #     if match:
        #         sequence_number = int(match.group(1)) + 1
        #     else:
        #         sequence_number = 1

        # # Format: YYMM-XXXX
        # return f"{year_month}-{sequence_number:04d}"
        return ""

    @staticmethod
    async def get_service_tickets(
        db: AsyncSession,
        client_id: Optional[int] = None,
        status: Optional[Any] = None,  # TicketStatus
        sales_rep_id: Optional[int] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Any]:  # List[ServiceTicket]
        """
        Get service tickets with optional filtering
        """
        # try:
        #     query = select(ServiceTicket).options(
        #         joinedload(ServiceTicket.client),
        #         joinedload(ServiceTicket.sales_rep)
        #     )
        #
        #     # Apply filters
        #     if client_id:
        #         query = query.filter(ServiceTicket.client_id == client_id)
        #     if status:
        #         query = query.filter(ServiceTicket.status == status)
        #     if sales_rep_id:
        #         query = query.filter(ServiceTicket.sales_rep_id == sales_rep_id)
        #     if search:
        #         query = query.filter(
        #             (ServiceTicket.title.ilike(f"%{search}%")) |
        #             (ServiceTicket.ticket_code.ilike(f"%{search}%"))
        #         )
        #
        #     # Apply pagination
        #     query = query.offset(skip).limit(limit)
        #     query = query.order_by(desc(ServiceTicket.created_at))
        #
        #     result = await db.execute(query)
        #     tickets = result.scalars().unique().all()
        #
        #     return tickets
        # except Exception as e:
        #     # logger.error(f"Error fetching service tickets: {str(e)}")
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"Failed to fetch service tickets: {str(e)}"
        #     )
        return []

    @staticmethod
    async def get_service_ticket(
        ticket_id: int, db: AsyncSession
    ) -> Any:  # ServiceTicket
        """
        Get a specific service ticket with all related data
        """
        # try:
        #     query = select(ServiceTicket).filter(
        #         ServiceTicket.id == ticket_id
        #     ).options(
        #         joinedload(ServiceTicket.client),
        #         joinedload(ServiceTicket.sales_rep),
        #         joinedload(ServiceTicket.ticket_steps).joinedload(TicketStep.step),
        #         joinedload(ServiceTicket.ticket_steps).joinedload(TicketStep.assigned_staff),
        #         joinedload(ServiceTicket.quotes).joinedload(QuoteDocument.created_by)
        #     )
        #
        #     result = await db.execute(query)
        #     ticket = result.scalar_one_or_none()
        #
        #     if not ticket:
        #         # logger.warning(f"Service ticket with ID {ticket_id} not found")
        #         raise HTTPException(
        #             status_code=status.HTTP_404_NOT_FOUND,
        #             detail=f"Service ticket with ID {ticket_id} not found"
        #         )
        #
        #     return ticket
        # except HTTPException:
        #     raise
        # except Exception as e:
        #     # logger.error(f"Error fetching service ticket {ticket_id}: {str(e)}")
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"Failed to fetch service ticket: {str(e)}"
        #     )
        return None

    @staticmethod
    async def create_service_ticket(
        ticket_data: Any, db: AsyncSession  # ServiceTicketCreate
    ) -> Any:  # ServiceTicket
        """
        Create a new service ticket
        """
        # try:
        #     # Generate ticket code
        #     ticket_code = await CustomerServiceController.generate_ticket_code(db)
        #
        #     # Create ticket
        #     new_ticket = ServiceTicket(
        #         ticket_code=ticket_code,
        #         client_id=ticket_data.client_id,
        #         sales_rep_id=ticket_data.sales_rep_id,
        #         title=ticket_data.title,
        #         description=ticket_data.description,
        #         priority=ticket_data.priority,
        #         estimated_completion=ticket_data.estimated_completion,
        #         status=TicketStatus.NEW
        #     )
        #
        #     db.add(new_ticket)
        #     await db.commit()
        #     await db.refresh(new_ticket)
        #
        #     # logger.info(f"Created new service ticket: {new_ticket.ticket_code}")
        #
        #     # Initialize first step automatically
        #     await CustomerServiceController.initialize_first_step(new_ticket.id, db)
        #
        #     # Return the ticket with all related info
        #     return await CustomerServiceController.get_service_ticket(new_ticket.id, db)
        # except Exception as e:
        #     # logger.error(f"Error creating service ticket: {str(e)}")
        #     await db.rollback()
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"Failed to create service ticket: {str(e)}"
        #     )
        return None

    @staticmethod
    async def initialize_first_step(ticket_id: int, db: AsyncSession) -> None:
        """
        Initialize the first step for a new ticket
        """
        # try:
        #     # Get the first active step in the service process
        #     query = select(ServiceStep).filter(
        #         ServiceStep.is_active == True
        #     ).order_by(ServiceStep.order).limit(1)
        #
        #     result = await db.execute(query)
        #     first_step = result.scalar_one_or_none()
        #
        #     if not first_step:
        #         # logger.warning("No active service steps found to initialize")
        #         return
        #
        #     # Create ticket step
        #     new_ticket_step = TicketStep(
        #         ticket_id=ticket_id,
        #         step_id=first_step.id,
        #         status=StepStatus.PENDING,
        #         unit_price=first_step.base_price,
        #         total_price=first_step.base_price  # Initial price is base price × quantity=1
        #     )
        #
        #     db.add(new_ticket_step)
        #     await db.commit()
        #
        #     # logger.info(f"Initialized first step '{first_step.name}' for ticket {ticket_id}")
        # except Exception as e:
        #     # logger.error(f"Error initializing first step for ticket {ticket_id}: {str(e)}")
        #     await db.rollback()
        #     raise
        pass

    @staticmethod
    async def update_service_ticket(
        ticket_id: int, ticket_data: Any, db: AsyncSession  # ServiceTicketUpdate
    ) -> Any:  # ServiceTicket
        """
        Update a service ticket
        """
        # try:
        #     # Get the ticket
        #     query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
        #     result = await db.execute(query)
        #     ticket = result.scalar_one_or_none()
        #
        #     if not ticket:
        #         # logger.warning(f"Service ticket with ID {ticket_id} not found")
        #         raise HTTPException(
        #             status_code=status.HTTP_404_NOT_FOUND,
        #             detail=f"Service ticket with ID {ticket_id} not found"
        #         )
        #
        #     # Update ticket attributes
        #     update_data = ticket_data.dict(exclude_unset=True)
        #
        #     # Special handling for status changes
        #     if "status" in update_data and update_data["status"] != ticket.status:
        #         if update_data["status"] == TicketStatus.COMPLETED and not ticket.actual_completion:
        #             update_data["actual_completion"] = datetime.utcnow()
        #
        #     # Apply updates
        #     for key, value in update_data.items():
        #         setattr(ticket, key, value)
        #
        #     await db.commit()
        #     await db.refresh(ticket)
        #
        #     # logger.info(f"Updated service ticket {ticket_id}")
        #
        #     # Return the updated ticket with all related info
        #     return await CustomerServiceController.get_service_ticket(ticket_id, db)
        # except HTTPException:
        #     raise
        # except Exception as e:
        #     # logger.error(f"Error updating service ticket {ticket_id}: {str(e)}")
        #     await db.rollback()
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"Failed to update service ticket: {str(e)}"
        #     )
        return None

    @staticmethod
    async def delete_service_ticket(ticket_id: int, db: AsyncSession) -> None:
        """
        Delete a service ticket
        """
        # try:
        #     # Get the ticket
        #     query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
        #     result = await db.execute(query)
        #     ticket = result.scalar_one_or_none()
        #
        #     if not ticket:
        #         # logger.warning(f"Service ticket with ID {ticket_id} not found")
        #         raise HTTPException(
        #             status_code=status.HTTP_404_NOT_FOUND,
        #             detail=f"Service ticket with ID {ticket_id} not found"
        #         )
        #
        #     # Check if there are any completed steps
        #     has_completed_steps = any(step.status == StepStatus.COMPLETED for step in ticket.ticket_steps)
        #     if has_completed_steps:
        #         # logger.warning(f"Cannot delete ticket {ticket_id} with completed steps")
        #         raise HTTPException(
        #             status_code=status.HTTP_400_BAD_REQUEST,
        #             detail=f"Cannot delete ticket with completed steps"
        #         )
        #
        #     # Delete the ticket and related records (cascade will handle ticket_steps and quotes)
        #     await db.delete(ticket)
        #     await db.commit()
        #
        #     # logger.info(f"Deleted service ticket {ticket_id}")
        # except HTTPException:
        #     raise
        # except Exception as e:
        #     # logger.error(f"Error deleting service ticket {ticket_id}: {str(e)}")
        #     await db.rollback()
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"Failed to delete service ticket: {str(e)}"
        #     )
        pass

    @staticmethod
    async def create_service_step(
        step_data: Any, db: AsyncSession  # ServiceStepCreate
    ) -> Any:  # ServiceStep
        """
        Create a new service step definition
        """
        # try:
        #     # Create the step
        #     new_step = ServiceStep(
        #         name=step_data.name,
        #         description=step_data.description,
        #         order=step_data.order,
        #         is_active=step_data.is_active,
        #         estimated_duration_hours=step_data.estimated_duration_hours,
        #         pricing_model=step_data.pricing_model,
        #         base_price=step_data.base_price
        #     )
        #
        #     db.add(new_step)
        #     await db.commit()
        #     await db.refresh(new_step)
        #
        #     # logger.info(f"Created new service step: {new_step.name}")
        #
        #     return new_step
        # except Exception as e:
        #     # logger.error(f"Error creating service step: {str(e)}")
        #     await db.rollback()
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"Failed to create service step: {str(e)}"
        #     )
        return None

    @staticmethod
    async def get_service_steps(
        db: AsyncSession, is_active: Optional[bool] = None
    ) -> List[Any]:  # List[ServiceStep]
        """
        Get all service steps with optional filtering
        """
        # try:
        #     query = select(ServiceStep)
        #
        #     if is_active is not None:
        #         query = query.filter(ServiceStep.is_active == is_active)
        #
        #     query = query.order_by(ServiceStep.order)
        #
        #     result = await db.execute(query)
        #     steps = result.scalars().all()
        #
        #     return steps
        # except Exception as e:
        #     # logger.error(f"Error fetching service steps: {str(e)}")
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"Failed to fetch service steps: {str(e)}"
        #     )
        return []

    @staticmethod
    async def update_service_step(
        step_id: int, step_data: Any, db: AsyncSession  # ServiceStepUpdate
    ) -> Any:  # ServiceStep
        """
        Update a service step
        """
        # try:
        #     # Get the step
        #     query = select(ServiceStep).filter(ServiceStep.id == step_id)
        #     result = await db.execute(query)
        #     step = result.scalar_one_or_none()
        #
        #     if not step:
        #         # logger.warning(f"Service step with ID {step_id} not found")
        #         raise HTTPException(
        #             status_code=status.HTTP_404_NOT_FOUND,
        #             detail=f"Service step with ID {step_id} not found"
        #         )
        #
        #     # Update step attributes
        #     update_data = step_data.dict(exclude_unset=True)
        #
        #     for key, value in update_data.items():
        #         setattr(step, key, value)
        #
        #     await db.commit()
        #     await db.refresh(step)
        #
        #     # logger.info(f"Updated service step {step_id}")
        #
        #     return step
        # except HTTPException:
        #     raise
        # except Exception as e:
        #     # logger.error(f"Error updating service step {step_id}: {str(e)}")
        #     await db.rollback()
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"Failed to update service step: {str(e)}"
        #     )
        return None

    @staticmethod
    async def add_step_to_ticket(
        ticket_id: int, step_data: Any, db: AsyncSession  # TicketStepCreate
    ) -> Any:  # TicketStep
        """
        Add a step to an existing ticket
        """
        # try:
        #     # Verify the ticket exists
        #     ticket_query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
        #     ticket_result = await db.execute(ticket_query)
        #     ticket = ticket_result.scalar_one_or_none()
        #
        #     if not ticket:
        #         # logger.warning(f"Service ticket with ID {ticket_id} not found")
        #         raise HTTPException(
        #             status_code=status.HTTP_404_NOT_FOUND,
        #             detail=f"Service ticket with ID {ticket_id} not found"
        #         )
        #
        #     # Verify the step exists
        #     step_query = select(ServiceStep).filter(ServiceStep.id == step_data.step_id)
        #     step_result = await db.execute(step_query)
        #     step = step_result.scalar_one_or_none()
        #
        #     if not step:
        #         # logger.warning(f"Service step with ID {step_data.step_id} not found")
        #         raise HTTPException(
        #             status_code=status.HTTP_404_NOT_FOUND,
        #             detail=f"Service step with ID {step_data.step_id} not found"
        #         )
        #
        #     # Check if step is already added to the ticket
        #     existing_query = select(TicketStep).filter(
        #         TicketStep.ticket_id == ticket_id,
        #         TicketStep.step_id == step_data.step_id
        #     )
        #     existing_result = await db.execute(existing_query)
        #     existing_step = existing_result.scalar_one_or_none()
        #
        #     if existing_step:
        #         # logger.warning(f"Step {step_data.step_id} already exists for ticket {ticket_id}")
        #         raise HTTPException(
        #             status_code=status.HTTP_400_BAD_REQUEST,
        #             detail=f"Step already exists for this ticket"
        #         )
        #
        #     # Calculate total price
        #     total_price = step_data.unit_price * step_data.quantity
        #
        #     # Create the ticket step
        #     new_ticket_step = TicketStep(
        #         ticket_id=ticket_id,
        #         step_id=step_data.step_id,
        #         assigned_staff_id=step_data.assigned_staff_id,
        #         quantity=step_data.quantity,
        #         unit_price=step_data.unit_price,
        #         total_price=total_price,
        #         notes=step_data.notes,
        #         status=StepStatus.PENDING
        #     )
        #
        #     db.add(new_ticket_step)
        #
        #     # Update the total price of the ticket
        #     ticket.total_price += total_price
        #
        #     await db.commit()
        #     await db.refresh(new_ticket_step)
        #
        #     # logger.info(f"Added step {step_data.step_id} to ticket {ticket_id}")
        #
        #     # Return the step with related info
        #     return await CustomerServiceController.get_ticket_step(ticket_id, new_ticket_step.id, db)
        # except HTTPException:
        #     raise
        # except Exception as e:
        #     # logger.error(f"Error adding step to ticket {ticket_id}: {str(e)}")
        #     await db.rollback()
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"Failed to add step to ticket: {str(e)}"
        #     )
        return None


#
#     @staticmethod
#     async def get_ticket_step(ticket_id: int, step_id: int, db: AsyncSession) -> Any: # TicketStep
#         """
#         Get a specific step for a ticket
#         """
#         # try:
#         #     query = select(TicketStep).filter(
#         #         TicketStep.ticket_id == ticket_id,
#         #         TicketStep.id == step_id
#         #     ).options(
#         #         joinedload(TicketStep.step),
#         #         joinedload(TicketStep.assigned_staff)
#         #     )
#         #
#         #     result = await db.execute(query)
#         #     ticket_step = result.scalar_one_or_none()
#         #
#         #     if not ticket_step:
#         #         # logger.warning(f"Ticket step {step_id} for ticket {ticket_id} not found")
#         #         raise HTTPException(
#         #             status_code=status.HTTP_404_NOT_FOUND,
#         #             detail=f"Ticket step not found"
#         #         )
#         #
#         #     return ticket_step
#         # except HTTPException:
#         #     raise
#         # except Exception as e:
#         #     # logger.error(f"Error fetching ticket step {step_id} for ticket {ticket_id}: {str(e)}")
#         #     raise HTTPException(
#         #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         #         detail=f"Failed to fetch ticket step: {str(e)}"
#         #     )
#         return None
#
#     @staticmethod
#     async def update_ticket_step(
#         ticket_id: int,
#         step_id: int,
#         step_data: Any, # TicketStepUpdate
#         db: AsyncSession
#     ) -> Any: # TicketStep
#         """
#         Update a step for a ticket
#         """
#         # try:
#         #     # Get the ticket step
#         #     query = select(TicketStep).filter(
#         #         TicketStep.ticket_id == ticket_id,
#         #         TicketStep.id == step_id
#         #     )
#         #     result = await db.execute(query)
#         #     ticket_step = result.scalar_one_or_none()
#         #
#         #     if not ticket_step:
#         #         # logger.warning(f"Ticket step {step_id} for ticket {ticket_id} not found")
#         #         raise HTTPException(
#         #             status_code=status.HTTP_404_NOT_FOUND,
#         #             detail=f"Ticket step not found"
#         #         )
#         #
#         #     # Update ticket step attributes
#         #     update_data = step_data.dict(exclude_unset=True)
#         #
#         #     # Recalculate total price if quantity or unit_price changes
#         #     old_total_price = ticket_step.total_price
#         #     if "quantity" in update_data or "unit_price" in update_data:
#         #         quantity = update_data.get("quantity", ticket_step.quantity)
#         #         unit_price = update_data.get("unit_price", ticket_step.unit_price)
#         #         update_data["total_price"] = quantity * unit_price
#         #
#         #     # Handle status changes
#         #     if "status" in update_data and update_data["status"] != ticket_step.status:
#         #         if update_data["status"] == StepStatus.IN_PROGRESS and not ticket_step.start_date:
#         #             update_data["start_date"] = datetime.utcnow()
#         #         elif update_data["status"] == StepStatus.COMPLETED and not ticket_step.completion_date:
#         #             update_data["completion_date"] = datetime.utcnow()
#         #
#         #     # Apply updates
#         #     for key, value in update_data.items():
#         #         setattr(ticket_step, key, value)
#         #
#         #     # Update the total price of the ticket
#         #     ticket_query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
#         #     ticket_result = await db.execute(ticket_query)
#         #     ticket = ticket_result.scalar_one_or_none()
#         #
#         #     if ticket:
#         #         ticket.total_price = (ticket.total_price - old_total_price) + ticket_step.total_price
#         #
#         #     await db.commit()
#         #     await db.refresh(ticket_step)
#         #
#         #     # logger.info(f"Updated step {step_id} for ticket {ticket_id}")
#         #
#         #     # Check for next step if current step is completed
#         #     if ticket_step.status == StepStatus.COMPLETED:
#         #         await CustomerServiceController._check_next_step(ticket_id, ticket_step, db)
#         #
#         #     # Return the updated step with related info
#         #     return await CustomerServiceController.get_ticket_step(ticket_id, step_id, db)
#         # except HTTPException:
#         #     raise
#         # except Exception as e:
#         #     # logger.error(f"Error updating ticket step {step_id} for ticket {ticket_id}: {str(e)}")
#         #     await db.rollback()
#         #     raise HTTPException(
#         #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         #         detail=f"Failed to update ticket step: {str(e)}"
#         #     )
#         return None
#
#     @staticmethod
#     async def _check_next_step(ticket_id: int, completed_step: Any, db: AsyncSession) -> None: # completed_step: TicketStep
#         """
#         Check if there's a next step in the service process and add it to the ticket.
#         Also updates ticket status if all steps are completed.
#         """
#         # try:
#         #     # Get current step details to find its order
#         #     current_step_query = select(ServiceStep).filter(
#         #         ServiceStep.id == completed_step.step_id
#         #     )
#         #     current_step_result = await db.execute(current_step_query)
#         #     current_step = current_step_result.scalar_one_or_none()
#
#         #     if not current_step:
#         #         # logger.warning(f"Current step details not found for step ID {completed_step.step_id}")
#         #         return
#
#         #     # Find the next active step by order
#         #     next_step_query = select(ServiceStep).filter(
#         #         ServiceStep.order > current_step.order,
#         #         ServiceStep.is_active == True
#         #     ).order_by(ServiceStep.order).limit(1)
#         #
#         #     next_step_result = await db.execute(next_step_query)
#         #     next_step = next_step_result.scalar_one_or_none()
#
#         #     if not next_step:
#         #         # All steps completed, update ticket status to COMPLETED
#         #         ticket_query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
#         #         ticket_result = await db.execute(ticket_query)
#         #         ticket = ticket_result.scalar_one_or_none()
#         #         if ticket:
#         #             ticket.status = TicketStatus.COMPLETED
#         #             if not ticket.actual_completion:
#         #                 ticket.actual_completion = datetime.utcnow()
#         #             # logger.info(f"All steps completed for ticket {ticket_id}. Status updated to COMPLETED.")
#         #         await db.commit()
#         #         return
#
#         #     # Check if this next step is already on the ticket (e.g., manually added)
#         #     existing_query = select(TicketStep).filter(
#         #         TicketStep.ticket_id == ticket_id,
#         #         TicketStep.step_id == next_step.id
#         #     )
#         #     existing_result = await db.execute(existing_query)
#         #     existing_ticket_step = existing_result.scalar_one_or_none()
#
#         #     if existing_ticket_step:
#         #         # logger.info(f"Next step {next_step.name} already exists for ticket {ticket_id}.")
#         #         return
#
#         #     # Add the next step to the ticket
#         #     new_ticket_step_data = TicketStepCreate(
#         #         step_id=next_step.id,
#         #         assigned_staff_id=None, # Or some default logic
#         #         quantity=1, # Default quantity
#         #         unit_price=next_step.base_price,
#         #         notes=f"Automatically added as next step after '{current_step.name}'",
#         #         status=StepStatus.PENDING
#         #     )
#         #     await CustomerServiceController.add_step_to_ticket(ticket_id, new_ticket_step_data, db)
#         #     # logger.info(f"Automatically added next step '{next_step.name}' to ticket {ticket_id}")
#         #
#         #     # Update ticket status to IN_PROGRESS if it was NEW
#         #     ticket_query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
#         #     ticket_result = await db.execute(ticket_query)
#         #     ticket = ticket_result.scalar_one_or_none()
#         #     if ticket and ticket.status == TicketStatus.NEW:
#         #         ticket.status = TicketStatus.IN_PROGRESS
#         #         await db.commit()
#         #         # logger.info(f"Ticket {ticket_id} status updated to IN_PROGRESS.")
#         #
#         # except Exception as e:
#         #     # logger.error(f"Error checking/adding next step for ticket {ticket_id}: {str(e)}")
#         #     # Don't re-raise, as this is an internal helper
#         #     pass # Or log more verbosely
#         pass
#
#     @staticmethod
#     async def remove_step_from_ticket(ticket_id: int, step_id: int, db: AsyncSession) -> None:
#         """
#         Remove a step from a ticket, if it's not completed
#         """
#         # try:
#         #     # Get the ticket step
#         #     query = select(TicketStep).filter(
#         #         TicketStep.ticket_id == ticket_id,
#         #         TicketStep.id == step_id
#         #     )
#         #     result = await db.execute(query)
#         #     ticket_step = result.scalar_one_or_none()
#         #
#         #     if not ticket_step:
#         #         # logger.warning(f"Ticket step {step_id} for ticket {ticket_id} not found")
#         #         raise HTTPException(
#         #             status_code=status.HTTP_404_NOT_FOUND,
#         #             detail=f"Ticket step not found"
#         #         )
#         #
#         #     # Prevent deletion of completed steps
#         #     if ticket_step.status == StepStatus.COMPLETED:
#         #         # logger.warning(f"Cannot remove completed step {step_id} from ticket {ticket_id}")
#         #         raise HTTPException(
#         #             status_code=status.HTTP_400_BAD_REQUEST,
#         #             detail=f"Cannot remove a completed step"
#         #         )
#         #
#         #     # Update the total price of the ticket
#         #     ticket_query = select(ServiceTicket).filter(ServiceTicket.id == ticket_id)
#         #     ticket_result = await db.execute(ticket_query)
#         #     ticket = ticket_result.scalar_one_or_none()
#         #
#         #     if ticket:
#         #         ticket.total_price -= ticket_step.total_price
#         #
#         #     await db.delete(ticket_step)
#         #     await db.commit()
#         #
#         #     # logger.info(f"Removed step {step_id} from ticket {ticket_id}")
#         # except HTTPException:
#         #     raise
#         # except Exception as e:
#         #     # logger.error(f"Error removing step {step_id} from ticket {ticket_id}: {str(e)}")
#         #     await db.rollback()
#         #     raise HTTPException(
#         #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         #         detail=f"Failed to remove step from ticket: {str(e)}"
#         #     )
#         pass
#
#     @staticmethod
#     async def complete_ticket_step_and_create_task(
#         ticket_id: int,
#         step_id: int,
#         user_id: int, # User completing the step
#         db: AsyncSession
#     ) -> Any: # TicketStep
#         """
#         Mark a ticket step as completed and create a follow-up task.
#         This is a conceptual example; task creation logic might be more complex.
#         """
#         # try:
#         #     # Mark step as completed
#         #     step_update_data = Any(status=StepStatus.COMPLETED) # TicketStepUpdate
#         #     completed_step = await CustomerServiceController.update_ticket_step(
#         #         ticket_id, step_id, step_update_data, db
#         #     )
#
#         #     # Create a follow-up task (example)
#         #     task_data = {
#         #         "title": f"Follow-up for completed step: {completed_step.step.name} on Ticket #{ticket_id}",
#         #         "description": f"Step '{completed_step.step.name}' (ID: {completed_step.id}) was completed for Service Ticket ID {ticket_id}. Please review and take necessary actions.",
#         #         "assigned_to_id": user_id, # Assign to the user who completed the step, or a manager
#         #         "due_date": datetime.utcnow() + timedelta(days=1), # Example: due next day
#         #         "priority": "Medium",
#         #         "status": "Open",
#         #         "project_id": None # Or link to a relevant project if applicable
#         #     }
#         #     # await TaskController.create_task(task_data, db, user_id) # Assuming TaskController is available
#         #     # logger.info(f"Created follow-up task for completed step {step_id} of ticket {ticket_id}")
#
#         #     return completed_step
#         # except HTTPException:
#         #     raise
#         # except Exception as e:
#         #     # logger.error(f"Error completing step and creating task for ticket {ticket_id}, step {step_id}: {str(e)}")
#         #     await db.rollback()
#         #     raise HTTPException(
#         #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         #         detail=f"Failed to complete step and create task: {str(e)}"
#         #     )
#         return None
#
#     @staticmethod
#     async def generate_quote_document(
#         ticket_id: int,
#         document_type: Any, # DocumentType
#         created_by_id: int,
#         db: AsyncSession,
#         file_storage_path: str = "./quote_documents"
#     ) -> Any: # QuoteDocument
#         """
#         Generate a quote document (PDF or Excel) for a service ticket
#         """
#         # try:
#         #     ticket = await CustomerServiceController.get_service_ticket(ticket_id, db)
#         #     if not ticket:
#         #         raise HTTPException(status_code=404, detail="Ticket not found")
#
#         #     # Ensure the directory exists
#         #     os.makedirs(file_storage_path, exist_ok=True)
#         #
#         #     file_name = f"quote_{ticket.ticket_code}_{uuid.uuid4()}.{document_type.value.lower()}"
#         #     file_path = os.path.join(file_storage_path, file_name)
#
#         #     # Prepare data for the quote
#         #     quote_data = {
#         #         "ticket_code": ticket.ticket_code,
#         #         "client_name": ticket.client.name if ticket.client else "N/A",
#         #         "sales_rep_name": ticket.sales_rep.username if ticket.sales_rep else "N/A",
#         #         "created_at": ticket.created_at.strftime("%Y-%m-%d"),
#         #         "items": [
#         #             {
#         #                 "name": ts.step.name,
#         #                 "description": ts.step.description,
#         #                 "quantity": ts.quantity,
#         #                 "unit_price": ts.unit_price,
#         #                 "total_price": ts.total_price
#         #             } for ts in ticket.ticket_steps
#         #         ],
#         #         "total_amount": sum(ts.total_price for ts in ticket.ticket_steps)
#         #     }
#
#         #     if document_type == DocumentType.PDF:
#         #         # generate_pdf_quote(file_path, quote_data)
#         #         pass # Placeholder as actual generation is commented out
#         #     elif document_type == DocumentType.EXCEL:
#         #         # generate_excel_quote(file_path, quote_data)
#         #         pass # Placeholder
#         #     else:
#         #         raise HTTPException(status_code=400, detail="Unsupported document type")
#
#         #     # Save quote document record
#         #     new_quote_data = QuoteDocumentCreate(
#         #         ticket_id=ticket_id,
#         #         file_path=file_path,
#         #         document_type=document_type,
#         #         created_by_id=created_by_id
#         #     )
#         #     new_quote = QuoteDocument(**new_quote_data.dict())
#         #     db.add(new_quote)
#         #     await db.commit()
#         #     await db.refresh(new_quote)
#
#         #     # logger.info(f"Generated {document_type.value} quote for ticket {ticket_id} at {file_path}")
#         #     return new_quote
#         # except HTTPException:
#         #     raise
#         # except Exception as e:
#         #     # logger.error(f"Error generating quote for ticket {ticket_id}: {str(e)}")
#         #     await db.rollback()
#         #     raise HTTPException(
#         #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         #         detail=f"Failed to generate quote: {str(e)}"
#         #     )
#         return None
#
#     @staticmethod
#     async def get_quote_document(quote_id: int, db: AsyncSession) -> Any: # QuoteDocument
#         """
#         Get a specific quote document
#         """
#         # try:
#         #     query = select(QuoteDocument).filter(QuoteDocument.id == quote_id).options(
#         #         joinedload(QuoteDocument.created_by)
#         #     )
#         #     result = await db.execute(query)
#         #     quote = result.scalar_one_or_none()
#         #     if not quote:
#         #         raise HTTPException(status_code=404, detail="Quote document not found")
#         #     return quote
#         # except HTTPException:
#         #     raise
#         # except Exception as e:
#         #     # logger.error(f"Error fetching quote document {quote_id}: {str(e)}")
#         #     raise HTTPException(
#         #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         #         detail=f"Failed to fetch quote document: {str(e)}"
#         #     )
#         return None
