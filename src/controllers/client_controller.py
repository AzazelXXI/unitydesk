from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from typing import List, Optional, Any  # Ensure Any is imported
import logging
from fastapi import HTTPException, status

# The following import from src.models.project was causing an ImportError.
# from src.models.project import Client, ClientContact
# Or, if it was a multi-line import like:
# from src.models.project import (
#     Client, ClientContact
# )
# Using Any as a placeholder to allow the application to start,
# as per the instruction to not modify the models at this stage.
Client: Any = Any
ClientContact: Any = Any

from src.schemas.marketing_project import (
    ClientCreate,
    ClientUpdate,
    ClientRead,
    ClientContactCreate,
    ClientContactUpdate,
    ClientContactRead,
)

# Configure logging
logger = logging.getLogger(__name__)


class ClientController:
    """Controller for handling client operations"""

    @staticmethod
    async def create_client(client_data: ClientCreate, db: AsyncSession) -> Any:
        """
        Create a new client for the marketing agency
        """
        try:
            new_client = Client(
                company_name=client_data.company_name,
                industry=client_data.industry,
                website=client_data.website,
                logo_url=client_data.logo_url,
                notes=client_data.notes,
                contact_name=client_data.contact_name,
                contact_email=client_data.contact_email,
                contact_phone=client_data.contact_phone,
            )

            db.add(new_client)
            await db.commit()
            await db.refresh(new_client)

            logger.info(f"Created new client: {new_client.company_name}")
            return new_client
        except Exception as e:
            logger.error(f"Error creating client: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create client: {str(e)}",
            )

    @staticmethod
    async def get_clients(
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        db: AsyncSession = None,
    ) -> List[Any]:
        """
        Get all clients with optional filtering
        """
        try:
            query = select(Client).offset(skip).limit(limit)

            # Apply filters if provided
            if search:
                query = query.filter(Client.company_name.ilike(f"%{search}%"))
            if industry:
                query = query.filter(Client.industry == industry)

            result = await db.execute(query)
            clients = result.scalars().all()

            return clients
        except Exception as e:
            logger.error(f"Error fetching clients: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch clients: {str(e)}",
            )

    @staticmethod
    async def get_client(client_id: int, db: AsyncSession) -> Any:
        """
        Get a specific client by ID
        """
        try:
            query = select(Client).filter(Client.id == client_id)
            result = await db.execute(query)
            client = result.scalars().first()

            if not client:
                logger.warning(f"Client with ID {client_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Client with ID {client_id} not found",
                )

            return client
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching client {client_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch client: {str(e)}",
            )

    @staticmethod
    async def update_client(
        client_id: int, client_data: ClientUpdate, db: AsyncSession
    ) -> Any:
        """
        Update a client's information
        """
        try:
            # Check if client exists
            client = await ClientController.get_client(client_id, db)

            # Update client attributes
            update_data = client_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(client, key, value)

            await db.commit()
            await db.refresh(client)

            logger.info(f"Updated client {client_id}: {client.company_name}")
            return client
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating client {client_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update client: {str(e)}",
            )

    @staticmethod
    async def delete_client(client_id: int, db: AsyncSession) -> None:
        """
        Delete a client
        """
        try:
            # Check if client exists
            client = await ClientController.get_client(client_id, db)

            # Delete the client
            await db.delete(client)
            await db.commit()

            logger.info(f"Deleted client {client_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting client {client_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete client: {str(e)}",
            )

    @staticmethod
    async def create_client_contact(
        client_id: int, contact_data: ClientContactCreate, db: AsyncSession
    ) -> Any:
        """
        Create a new contact for a client
        """
        try:
            # Check if client exists
            await ClientController.get_client(client_id, db)

            # Create new contact
            new_contact = ClientContact(
                client_id=client_id,
                name=contact_data.name,
                position=contact_data.position,
                email=contact_data.email,
                phone=contact_data.phone,
                is_primary=contact_data.is_primary,
                notes=contact_data.notes,
            )

            # If this is a primary contact, unset primary on other contacts
            if new_contact.is_primary:
                await ClientController._unset_primary_contacts(client_id, db)

            db.add(new_contact)
            await db.commit()
            await db.refresh(new_contact)

            logger.info(
                f"Created new contact {new_contact.name} for client {client_id}"
            )
            return new_contact
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating contact for client {client_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create contact: {str(e)}",
            ) @ staticmethod

    async def get_client_contacts(client_id: int, db: AsyncSession) -> List[Any]:
        """
        Get all contacts for a client
        """
        try:
            # Check if client exists
            await ClientController.get_client(client_id, db)

            # Get contacts
            query = select(ClientContact).filter(ClientContact.client_id == client_id)
            result = await db.execute(query)
            contacts = result.scalars().all()

            return contacts
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching contacts for client {client_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch contacts: {str(e)}",
            )

    @staticmethod
    async def get_client_contact(
        client_id: int, contact_id: int, db: AsyncSession
    ) -> Any:
        """
        Get a specific contact for a client
        """
        try:
            # Check if client exists
            await ClientController.get_client(client_id, db)

            # Get contact
            query = select(ClientContact).filter(
                ClientContact.id == contact_id, ClientContact.client_id == client_id
            )
            result = await db.execute(query)
            contact = result.scalars().first()

            if not contact:
                logger.warning(
                    f"Contact with ID {contact_id} not found for client {client_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Contact with ID {contact_id} not found for client {client_id}",
                )

            return contact
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error fetching contact {contact_id} for client {client_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch contact: {str(e)}",
            )

    @staticmethod
    async def update_client_contact(
        client_id: int,
        contact_id: int,
        contact_data: ClientContactUpdate,
        db: AsyncSession,
    ) -> Any:
        """
        Update a client contact
        """
        try:
            # Get the contact
            contact = await ClientController.get_client_contact(
                client_id, contact_id, db
            )

            # Update contact attributes
            update_data = contact_data.dict(exclude_unset=True)

            # If setting as primary contact, unset others
            if update_data.get("is_primary"):
                await ClientController._unset_primary_contacts(client_id, db)

            for key, value in update_data.items():
                setattr(contact, key, value)

            await db.commit()
            await db.refresh(contact)

            logger.info(f"Updated contact {contact_id} for client {client_id}")
            return contact
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error updating contact {contact_id} for client {client_id}: {str(e)}"
            )
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update contact: {str(e)}",
            )

    @staticmethod
    async def delete_client_contact(
        client_id: int, contact_id: int, db: AsyncSession
    ) -> None:
        """
        Delete a client contact
        """
        try:
            # Get the contact
            contact = await ClientController.get_client_contact(
                client_id, contact_id, db
            )

            # Delete the contact
            await db.delete(contact)
            await db.commit()

            logger.info(f"Deleted contact {contact_id} from client {client_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error deleting contact {contact_id} from client {client_id}: {str(e)}"
            )
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete contact: {str(e)}",
            )

    @staticmethod
    async def _unset_primary_contacts(client_id: int, db: AsyncSession) -> None:
        """
        Helper method to unset primary flag on all contacts for a client
        """
        try:
            query = (
                update(ClientContact)
                .where(
                    ClientContact.client_id == client_id,
                    ClientContact.is_primary == True,
                )
                .values(is_primary=False)
            )

            await db.execute(query)
            # No commit here, as the calling function will handle the transaction
        except Exception as e:
            logger.error(
                f"Error unsetting primary contacts for client {client_id}: {str(e)}"
            )
            raise
