from pydantic import BaseModel, Field, validator, condecimal
from typing import List, Optional, Union
from datetime import datetime
from uuid import UUID

from src.models_backup.customer_service import (
    TicketStatus,
    Priority,
    StepStatus,
    PricingModel,
    DocumentType,
)


# Base schemas
class ServiceStepBase(BaseModel):
    name: str
    description: Optional[str] = None
    order: int
    estimated_duration_hours: float = Field(ge=0)
    pricing_model: PricingModel
    base_price: condecimal(max_digits=10, decimal_places=2) = Field(ge=0)
    is_active: bool = True


class ServiceTicketBase(BaseModel):
    title: str
    description: Optional[str] = None
    client_id: int
    sales_rep_id: int
    priority: Priority = Priority.MEDIUM
    estimated_completion: Optional[datetime] = None


class TicketStepBase(BaseModel):
    ticket_id: int
    step_id: int
    assigned_staff_id: Optional[int] = None
    quantity: int = Field(ge=1, default=1)
    unit_price: condecimal(max_digits=10, decimal_places=2) = Field(ge=0)
    notes: Optional[str] = None


class QuoteDocumentBase(BaseModel):
    ticket_id: int
    document_type: DocumentType
    created_by_id: int


# Create schemas
class ServiceStepCreate(ServiceStepBase):
    pass


class ServiceTicketCreate(ServiceTicketBase):
    pass


class TicketStepCreate(TicketStepBase):
    pass


class QuoteDocumentCreate(QuoteDocumentBase):
    pass


# Update schemas
class ServiceStepUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    estimated_duration_hours: Optional[float] = Field(None, ge=0)
    pricing_model: Optional[PricingModel] = None
    base_price: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(
        None, ge=0
    )
    is_active: Optional[bool] = None


class ServiceTicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[Priority] = None
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None


class TicketStepUpdate(BaseModel):
    assigned_staff_id: Optional[int] = None
    quantity: Optional[int] = Field(None, ge=1)
    unit_price: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(
        None, ge=0
    )
    status: Optional[StepStatus] = None
    notes: Optional[str] = None


class QuoteDocumentUpdate(BaseModel):
    is_sent: Optional[bool] = None
    sent_at: Optional[datetime] = None


# Read schemas
class ServiceStepRead(ServiceStepBase):
    id: int

    class Config:
        from_attributes = True


class UserBasic(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class ClientBasic(BaseModel):
    id: int
    company_name: str
    contact_name: Optional[str] = None

    class Config:
        from_attributes = True


class TicketStepRead(TicketStepBase):
    id: int
    status: StepStatus
    total_price: float
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    assigned_staff: Optional[UserBasic] = None
    step: ServiceStepRead

    class Config:
        from_attributes = True


class QuoteDocumentRead(QuoteDocumentBase):
    id: int
    file_path: str
    created_at: datetime
    is_sent: bool
    sent_at: Optional[datetime] = None
    created_by: UserBasic

    class Config:
        from_attributes = True


class ServiceTicketRead(ServiceTicketBase):
    id: int
    ticket_code: str
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    total_price: float
    actual_completion: Optional[datetime] = None
    client: ClientBasic
    sales_rep: UserBasic

    class Config:
        from_attributes = True


class ServiceTicketDetailRead(ServiceTicketRead):
    ticket_steps: List[TicketStepRead] = []
    quotes: List[QuoteDocumentRead] = []

    class Config:
        from_attributes = True


# Special schemas
class CompleteStepRequest(BaseModel):
    notes: Optional[str] = None
    actual_hours: Optional[float] = Field(None, ge=0)


class GenerateQuoteRequest(BaseModel):
    document_type: DocumentType = DocumentType.PDF
    include_logo: bool = True
    include_details: bool = True
