from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from src.database import get_db
from src.controllers.client_controller import ClientController
from src.schemas.marketing_project import (
    ClientCreate, ClientUpdate, ClientRead,
    ClientContactCreate, ClientContactUpdate, ClientContactRead
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/clients",
    tags=["clients"],
    responses={404: {"description": "Not found"}}
)


@router.post("/", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(client_data: ClientCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new client for the marketing agency
    """
    return await ClientController.create_client(client_data, db)


@router.get("/", response_model=List[ClientRead])
async def get_clients(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    industry: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all clients with optional filtering
    """
    return await ClientController.get_clients(skip, limit, search, industry, db)


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific client by ID
    """
    return await ClientController.get_client(client_id, db)


@router.put("/{client_id}", response_model=ClientRead)
async def update_client(client_id: int, client_data: ClientUpdate, db: AsyncSession = Depends(get_db)):
    """
    Update a client's information
    """
    return await ClientController.update_client(client_id, client_data, db)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a client
    """
    await ClientController.delete_client(client_id, db)


@router.post("/{client_id}/contacts", response_model=ClientContactRead)
async def create_client_contact(
    client_id: int, 
    contact_data: ClientContactCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new contact for a client
    """
    return await ClientController.create_client_contact(client_id, contact_data, db)


@router.get("/{client_id}/contacts", response_model=List[ClientContactRead])
async def get_client_contacts(client_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all contacts for a client
    """
    return await ClientController.get_client_contacts(client_id, db)


@router.get("/{client_id}/contacts/{contact_id}", response_model=ClientContactRead)
async def get_client_contact(client_id: int, contact_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific contact for a client
    """
    return await ClientController.get_client_contact(client_id, contact_id, db)


@router.put("/{client_id}/contacts/{contact_id}", response_model=ClientContactRead)
async def update_client_contact(
    client_id: int,
    contact_id: int,
    contact_data: ClientContactUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a client contact
    """
    return await ClientController.update_client_contact(client_id, contact_id, contact_data, db)


@router.delete("/{client_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_contact(client_id: int, contact_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a client contact
    """
    await ClientController.delete_client_contact(client_id, contact_id, db)
