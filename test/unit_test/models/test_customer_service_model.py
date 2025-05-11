import pytest
from sqlalchemy.future import select
from sqlalchemy import text
from src.models.customer_service import (
    ServiceTicket, ServiceStep, TicketStep, QuoteDocument,
    TicketStatus, Priority, StepStatus, PricingModel, DocumentType
)
from src.models.user import User
from src.models.marketing_project import Client
import datetime
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_create_service_ticket(test_session):
    """Test creating a new service ticket"""
    # First create a user and client
    user = User(
        email="sales@example.com",
        username="salesrep",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    client = Client(
        company_name="Test Company",
        industry="Technology",
        website="https://example.com",
        contact_name="John Doe",
        contact_email="john@example.com",
        contact_phone="123-456-7890"
    )
    
    test_session.add_all([user, client])
    await test_session.flush()
    
    # Create a service ticket
    ticket = ServiceTicket(
        ticket_code="TKT12345",
        client_id=client.id,
        sales_rep_id=user.id,
        title="Server Setup",
        description="Set up a new web server",
        status=TicketStatus.NEW,
        priority=Priority.HIGH,
        estimated_completion=datetime.utcnow() + timedelta(days=7),
        total_price=1500.00
    )
    
    test_session.add(ticket)
    await test_session.commit()
    
    # Query the ticket
    stmt = select(ServiceTicket).where(ServiceTicket.ticket_code == "TKT12345")
    result = await test_session.execute(stmt)
    fetched_ticket = result.scalars().first()
    
    # Assert ticket was created with correct values
    assert fetched_ticket is not None
    assert fetched_ticket.ticket_code == "TKT12345"
    assert fetched_ticket.title == "Server Setup"
    assert fetched_ticket.status == TicketStatus.NEW
    assert fetched_ticket.priority == Priority.HIGH
    assert fetched_ticket.total_price == 1500.00
    
    # Clean up
    await test_session.delete(ticket)
    await test_session.delete(client)
    await test_session.delete(user)
    await test_session.commit()

@pytest.mark.asyncio
async def test_create_service_step(test_session):
    """Test creating a new service step"""
    # Create a service step
    step = ServiceStep(
        name="Server Installation",
        description="Install server software",
        order=1,
        is_active=True,
        estimated_duration_hours=2.5,
        pricing_model=PricingModel.FIXED,
        base_price=500.00
    )
    
    test_session.add(step)
    await test_session.commit()
    
    # Query the step
    stmt = select(ServiceStep).where(ServiceStep.name == "Server Installation")
    result = await test_session.execute(stmt)
    fetched_step = result.scalars().first()
    
    # Assert step was created with correct values
    assert fetched_step is not None
    assert fetched_step.name == "Server Installation"
    assert fetched_step.order == 1
    assert fetched_step.estimated_duration_hours == 2.5
    assert fetched_step.pricing_model == PricingModel.FIXED
    assert fetched_step.base_price == 500.00
    
    # Clean up
    await test_session.delete(step)
    await test_session.commit()

@pytest.mark.asyncio
async def test_ticket_step_relationship(test_session):
    """Test the relationship between tickets and steps"""
    # Create needed entities
    user = User(
        email="tech@example.com",
        username="techsupport",
        hashed_password="hashedpassword456",
        is_active=True,
        is_verified=True
    )
    
    client = Client(
        company_name="Test Client",
        industry="Retail",
        contact_email="client@example.com"
    )
    
    # Create a service ticket
    ticket = ServiceTicket(
        ticket_code="TKT67890",
        title="Network Configuration",
        status=TicketStatus.IN_PROGRESS,
        priority=Priority.MEDIUM,
        total_price=2000.00
    )
    
    # Create service steps
    step1 = ServiceStep(
        name="Network Analysis",
        description="Analyze current network setup",
        order=1,
        estimated_duration_hours=1.0,
        pricing_model=PricingModel.HOURLY,
        base_price=100.00
    )
    
    step2 = ServiceStep(
        name="Equipment Installation",
        description="Install new networking equipment",
        order=2,
        estimated_duration_hours=3.0,
        pricing_model=PricingModel.FIXED,
        base_price=800.00
    )
    
    test_session.add_all([user, client, step1, step2])
    await test_session.flush()
    
    # Set foreign keys after entities are created
    ticket.client_id = client.id
    ticket.sales_rep_id = user.id
    
    test_session.add(ticket)
    await test_session.flush()
    
    # Create ticket steps
    ticket_step1 = TicketStep(
        ticket_id=ticket.id,
        step_id=step1.id,
        status=StepStatus.COMPLETED,
        assigned_staff_id=user.id,
        quantity=1,
        unit_price=100.00,
        total_price=100.00,
        start_date=datetime.utcnow() - timedelta(days=1),
        completion_date=datetime.utcnow()
    )
    
    ticket_step2 = TicketStep(
        ticket_id=ticket.id,
        step_id=step2.id,
        status=StepStatus.IN_PROGRESS,
        assigned_staff_id=user.id,
        quantity=1,
        unit_price=800.00,
        total_price=800.00,
        start_date=datetime.utcnow()
    )
    
    test_session.add_all([ticket_step1, ticket_step2])
    await test_session.commit()
    
    # Query the ticket with steps using joinedload for eager loading
    stmt = select(ServiceTicket).options(joinedload(ServiceTicket.ticket_steps)).where(ServiceTicket.id == ticket.id)
    result = await test_session.execute(stmt)
    fetched_ticket = result.scalars().first()
    
    # Test relationships
    assert len(fetched_ticket.ticket_steps) == 2
    
    # Test the current_step property
    assert fetched_ticket.current_step.status == StepStatus.IN_PROGRESS
    assert fetched_ticket.current_step.step_id == step2.id
    
    # Clean up
    await test_session.delete(ticket_step1)
    await test_session.delete(ticket_step2)
    await test_session.delete(ticket)
    await test_session.delete(step1)
    await test_session.delete(step2)
    await test_session.delete(client)
    await test_session.delete(user)
    await test_session.commit()

@pytest.mark.asyncio
async def test_quote_document(test_session):
    """Test creating quote documents for a ticket"""
    # Create a user and client
    user = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password="hashedpassword789",
        is_active=True,
        is_verified=True
    )
    
    client = Client(
        company_name="Document Test Company",
        industry="Finance"
    )
    
    test_session.add_all([user, client])
    await test_session.flush()
    
    # Create a service ticket
    ticket = ServiceTicket(
        ticket_code="TKT-DOC1",
        client_id=client.id,
        sales_rep_id=user.id,
        title="Financial Software Setup",
        status=TicketStatus.NEW,
        priority=Priority.MEDIUM
    )
    test_session.add(ticket)
    await test_session.flush()
    
    # Lấy các giá trị enum từ database để sử dụng trong SQL
    result = await test_session.execute(
        text("SELECT unnest(enum_range(NULL::documenttype))")
    )
    enum_values = result.scalars().all()
    print(f"Database enum values: {enum_values}")
    
    if len(enum_values) < 2:
        pytest.skip("Not enough documenttype enum values for this test")
    
    # Sử dụng giá trị enum thực tế từ database
    now = datetime.utcnow()
    await test_session.execute(
        text("""
        INSERT INTO quote_documents
        (ticket_id, document_type, file_path, created_at, created_by_id, is_sent, sent_at)
        VALUES
        (:ticket_id, :doc_type, :pdf_path, :now, :user_id, false, null)
        """),
        {
            "ticket_id": ticket.id,
            "doc_type": enum_values[0],  # Sử dụng giá trị enum thực tế
            "pdf_path": "/path/to/quote.pdf",
            "now": now,
            "user_id": user.id
        }
    )
    
    sent_time = datetime.utcnow()
    await test_session.execute(
        text("""
        INSERT INTO quote_documents
        (ticket_id, document_type, file_path, created_at, created_by_id, is_sent, sent_at)
        VALUES
        (:ticket_id, :doc_type, :xlsx_path, :now, :user_id, true, :sent_time)
        """),
        {
            "ticket_id": ticket.id,
            "doc_type": enum_values[1],  # Sử dụng giá trị enum thực tế khác
            "xlsx_path": "/path/to/quote.xlsx",
            "now": now,
            "user_id": user.id,
            "sent_time": sent_time
        }
    )
    
    # Commit các thao tác
    await test_session.commit()
    
    # Kiểm tra kết quả
    result = await test_session.execute(
        text("SELECT document_type, is_sent, sent_at FROM quote_documents WHERE ticket_id = :ticket_id ORDER BY document_type"),
        {"ticket_id": ticket.id}
    )
    quotes = result.fetchall()
    
    # Kiểm tra kết quả
    assert len(quotes) == 2
    assert quotes[0][0] == enum_values[0]
    assert quotes[1][0] == enum_values[1]
    
    # Clean up
    await test_session.execute(
        text("DELETE FROM quote_documents WHERE ticket_id = :ticket_id"),
        {"ticket_id": ticket.id}
    )
    await test_session.delete(ticket)
    await test_session.delete(client)
    await test_session.delete(user)
    await test_session.commit()
