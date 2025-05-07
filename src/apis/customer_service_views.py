from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
from datetime import datetime

from src.database import get_db
from src.controllers.customer_service_controller import CustomerServiceController
from src.models.customer_service import TicketStatus, DocumentType
from src.schemas.customer_service import (
    ServiceTicketCreate, ServiceTicketUpdate, ServiceTicketRead, ServiceTicketDetailRead,
    ServiceStepCreate, ServiceStepUpdate, ServiceStepRead,
    TicketStepCreate, TicketStepUpdate, TicketStepRead,
    QuoteDocumentRead, GenerateQuoteRequest, CompleteStepRequest
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/customer-service",
    tags=["customer service"],
    responses={404: {"description": "Not found"}}
)

# ==================== Service Ticket Endpoints ====================

@router.post("/tickets", response_model=ServiceTicketDetailRead, status_code=status.HTTP_201_CREATED)
async def create_service_ticket(
    ticket_data: ServiceTicketCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new service ticket
    """
    return await CustomerServiceController.create_service_ticket(ticket_data, db)


@router.get("/tickets", response_model=List[ServiceTicketRead])
async def get_service_tickets(
    client_id: Optional[int] = None,
    status: Optional[TicketStatus] = None,
    sales_rep_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get service tickets with optional filtering
    """
    return await CustomerServiceController.get_service_tickets(
        client_id, status, sales_rep_id, search, skip, limit, db
    )


@router.get("/tickets/{ticket_id}", response_model=ServiceTicketDetailRead)
async def get_service_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific service ticket with all related data
    """
    return await CustomerServiceController.get_service_ticket(ticket_id, db)


@router.put("/tickets/{ticket_id}", response_model=ServiceTicketDetailRead)
async def update_service_ticket(
    ticket_id: int,
    ticket_data: ServiceTicketUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a service ticket
    """
    return await CustomerServiceController.update_service_ticket(ticket_id, ticket_data, db)


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a service ticket
    """
    await CustomerServiceController.delete_service_ticket(ticket_id, db)


# ==================== Service Step Definition Endpoints ====================

@router.post("/steps", response_model=ServiceStepRead, status_code=status.HTTP_201_CREATED)
async def create_service_step(
    step_data: ServiceStepCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new service step definition
    """
    return await CustomerServiceController.create_service_step(step_data, db)


@router.get("/steps", response_model=List[ServiceStepRead])
async def get_service_steps(
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all service steps with optional filtering
    """
    return await CustomerServiceController.get_service_steps(is_active, db)


@router.put("/steps/{step_id}", response_model=ServiceStepRead)
async def update_service_step(
    step_id: int,
    step_data: ServiceStepUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a service step
    """
    return await CustomerServiceController.update_service_step(step_id, step_data, db)


# ==================== Ticket Steps Endpoints ====================

@router.post("/tickets/{ticket_id}/steps", response_model=TicketStepRead)
async def add_step_to_ticket(
    ticket_id: int,
    step_data: TicketStepCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Add a step to an existing ticket
    """
    return await CustomerServiceController.add_step_to_ticket(ticket_id, step_data, db)


@router.get("/tickets/{ticket_id}/steps/{step_id}", response_model=TicketStepRead)
async def get_ticket_step(
    ticket_id: int,
    step_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific ticket step
    """
    return await CustomerServiceController.get_ticket_step(ticket_id, step_id, db)


@router.put("/tickets/{ticket_id}/steps/{step_id}", response_model=TicketStepRead)
async def update_ticket_step(
    ticket_id: int,
    step_id: int,
    step_data: TicketStepUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a ticket step
    """
    return await CustomerServiceController.update_ticket_step(ticket_id, step_id, step_data, db)


@router.post("/tickets/{ticket_id}/steps/{step_id}/complete", response_model=TicketStepRead)
async def complete_step(
    ticket_id: int,
    step_id: int,
    data: CompleteStepRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a ticket step as completed and trigger the next step
    """
    return await CustomerServiceController.complete_step(ticket_id, step_id, data.notes, db)


# ==================== Quote Generation Endpoints ====================

@router.post("/tickets/{ticket_id}/generate-quote", response_model=QuoteDocumentRead)
async def generate_quote(
    ticket_id: int,
    request: GenerateQuoteRequest,
    created_by_id: int = Query(..., description="ID of user creating the quote"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a quote document (PDF or Excel) for a ticket
    """
    return await CustomerServiceController.generate_quote(
        ticket_id, request.document_type, created_by_id, 
        request.include_logo, request.include_details, db
    )


@router.put("/quotes/{quote_id}/mark-sent", response_model=QuoteDocumentRead)
async def mark_quote_sent(
    quote_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a quote document as sent
    """
    return await CustomerServiceController.update_quote_document(quote_id, True, db)
