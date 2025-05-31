from sqlalchemy import Column, Integer, String, Text, Float, Numeric, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from src.models_backup.base import Base

class TicketStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class StepStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class PricingModel(str, enum.Enum):
    FIXED = "fixed"
    PER_UNIT = "per_unit"
    HOURLY = "hourly"
    CUSTOM = "custom"

class DocumentType(str, enum.Enum):
    PDF = "pdf"
    XLSX = "xlsx"

class ServiceTicket(Base):
    """Model for customer service tickets"""
    __tablename__ = "service_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_code = Column(String(10), unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    sales_rep_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TicketStatus), default=TicketStatus.NEW, nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    estimated_completion = Column(DateTime, nullable=True)
    actual_completion = Column(DateTime, nullable=True)
    total_price = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Relationships
    client = relationship("Client", back_populates="service_tickets")
    sales_rep = relationship("User", foreign_keys=[sales_rep_id])
    ticket_steps = relationship("TicketStep", back_populates="ticket", cascade="all, delete-orphan")
    quotes = relationship("QuoteDocument", back_populates="ticket", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ServiceTicket {self.ticket_code}: {self.title}>"
    
    @property
    def current_step(self):
        """Return the current active step of the ticket"""
        for step in self.ticket_steps:
            if step.status in [StepStatus.PENDING, StepStatus.IN_PROGRESS]:
                return step
        return None

class ServiceStep(Base):
    """Model for service steps definition"""
    __tablename__ = "service_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    estimated_duration_hours = Column(Float, default=1.0, nullable=False)
    pricing_model = Column(Enum(PricingModel), default=PricingModel.FIXED, nullable=False)
    base_price = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Relationships
    ticket_steps = relationship("TicketStep", back_populates="step")
    
    __table_args__ = (
        UniqueConstraint('order', name='unique_step_order'),
    )
    
    def __repr__(self):
        return f"<ServiceStep {self.id}: {self.name}>"

class TicketStep(Base):
    """Model for steps assigned to a specific ticket"""
    __tablename__ = "ticket_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("service_tickets.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("service_steps.id"), nullable=False)
    status = Column(Enum(StepStatus), default=StepStatus.PENDING, nullable=False)
    assigned_staff_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), default=0, nullable=False)
    total_price = Column(Numeric(10, 2), default=0, nullable=False)
    start_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    ticket = relationship("ServiceTicket", back_populates="ticket_steps")
    step = relationship("ServiceStep", back_populates="ticket_steps")
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id])
    
    __table_args__ = (
        UniqueConstraint('ticket_id', 'step_id', name='unique_ticket_step'),
    )
    
    def __repr__(self):
        return f"<TicketStep {self.id}: Ticket {self.ticket_id} - Step {self.step_id}>"

class QuoteDocument(Base):
    """Model for quote documents generated for tickets"""
    __tablename__ = "quote_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("service_tickets.id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    file_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    ticket = relationship("ServiceTicket", back_populates="quotes")
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    def __repr__(self):
        return f"<QuoteDocument {self.id}: Ticket {self.ticket_id} - {self.document_type}>"
