import pytest
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

from src.models.marketing_project import (
    MarketingProject, Client, ClientContact, WorkflowStep, MarketingTask,
    MarketingTaskComment, MarketingAsset, AnalyticsReport, 
    ProjectStatus, ProjectType, WorkflowStage, TaskPriority, TaskStatus, AssetType, ReportType
)
from src.models.user import User

@pytest.mark.asyncio
async def test_create_marketing_project(test_session):
    """Test creating a new marketing project"""
    # Create owner user
    owner = User(
        email="project_owner@example.com",
        username="project_owner",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    test_session.add(owner)
    await test_session.flush()
    
    # Create a client
    client = Client(
        company_name="Acme Corp",
        industry="Technology",
        website="https://acmecorp.example.com",
        contact_name="John Doe",
        contact_email="john@acmecorp.example.com",
        contact_phone="555-123-4567"
    )
    
    test_session.add(client)
    await test_session.flush()
    
    # Create a marketing project
    project = MarketingProject(
        name="Website Redesign Campaign",
        description="Complete website redesign with new branding",
        project_type=ProjectType.BRAND_BUILDING,
        status=ProjectStatus.DRAFT,
        current_stage=WorkflowStage.INITIATION,
        client_id=client.id,
        client_brief="Need modern website design with improved UX",
        start_date=datetime.utcnow(),
        target_end_date=datetime.utcnow() + timedelta(days=60),
        estimated_budget=50000.0,
        owner_id=owner.id
    )
    
    test_session.add(project)
    await test_session.commit()
    
    # Query the project with eager loading of relationships
    stmt = select(MarketingProject).where(MarketingProject.id == project.id).options(
        joinedload(MarketingProject.owner),
        joinedload(MarketingProject.client)
    )
    result = await test_session.execute(stmt)
    fetched_project = result.scalars().first()
    
    # Assert project was created with correct values
    assert fetched_project is not None
    assert fetched_project.name == "Website Redesign Campaign"
    assert fetched_project.project_type == ProjectType.BRAND_BUILDING
    assert fetched_project.status == ProjectStatus.DRAFT
    assert fetched_project.current_stage == WorkflowStage.INITIATION
    assert fetched_project.client.company_name == "Acme Corp"
    assert fetched_project.owner.username == "project_owner"
    assert fetched_project.estimated_budget == 50000.0
    
    # Clean up
    await test_session.delete(project)
    await test_session.delete(client)
    await test_session.delete(owner)
    await test_session.commit()

@pytest.mark.asyncio
async def test_client_contact_relationship(test_session):
    """Test client and client contacts relationship"""
    # Create a client
    client = Client(
        company_name="XYZ Industries",
        industry="Manufacturing",
        website="https://xyz.example.com",
        contact_name="Primary Contact",
        contact_email="primary@xyz.example.com",
        contact_phone="555-987-6543"
    )
    
    test_session.add(client)
    await test_session.flush()
    
    # Add additional contacts
    primary_contact = ClientContact(
        client_id=client.id,
        name="Jane Smith",
        position="Marketing Director",
        email="jane@xyz.example.com",
        phone="555-111-2222",
        is_primary=True,
        notes="Main decision maker"
    )
    
    secondary_contact = ClientContact(
        client_id=client.id,
        name="Bob Johnson",
        position="IT Manager",
        email="bob@xyz.example.com",
        phone="555-333-4444",
        is_primary=False,
        notes="Technical contact"
    )
    
    test_session.add_all([primary_contact, secondary_contact])
    await test_session.commit()
    
    # Query the client with eager loading of contacts
    stmt = select(Client).where(Client.id == client.id).options(
        joinedload(Client.contacts)
    )
    result = await test_session.execute(stmt)
    fetched_client = result.scalars().first()
    
    # Assert client contacts are correctly associated
    assert fetched_client is not None
    assert len(fetched_client.contacts) == 2
    
    # Check contacts details
    contacts = {c.name: c for c in fetched_client.contacts}
    assert "Jane Smith" in contacts
    assert "Bob Johnson" in contacts
    assert contacts["Jane Smith"].is_primary == True
    assert contacts["Bob Johnson"].is_primary == False
    assert contacts["Jane Smith"].position == "Marketing Director"
    
    # Clean up
    await test_session.delete(client)  # Should cascade delete contacts
    await test_session.commit()

@pytest.mark.asyncio
async def test_workflow_steps_and_tasks(test_session):
    """Test creating workflow steps and tasks for a marketing project"""
    # Create owner and team members
    owner = User(
        email="project_manager@example.com",
        username="pm_user",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    team_member = User(
        email="team_member@example.com",
        username="designer1",
        hashed_password="hashedpassword456",
        is_active=True,
        is_verified=True
    )
    
    test_session.add_all([owner, team_member])
    await test_session.flush()
    
    # Create a client
    client = Client(
        company_name="ABC Marketing",
        industry="Retail",
        contact_name="Alice Cooper",
        contact_email="alice@abc.example.com"
    )
    
    test_session.add(client)
    await test_session.flush()
    
    # Create a marketing project
    project = MarketingProject(
        name="Holiday Campaign 2023",
        description="Q4 marketing campaign for holiday season",
        project_type=ProjectType.INTEGRATED_CAMPAIGN,
        status=ProjectStatus.IN_PROGRESS,
        current_stage=WorkflowStage.PLANNING,
        client_id=client.id,
        owner_id=owner.id,
        start_date=datetime.utcnow(),
        target_end_date=datetime.utcnow() + timedelta(days=90)
    )
    
    test_session.add(project)
    await test_session.flush()
    
    # Create workflow steps
    step1 = WorkflowStep(
        project_id=project.id,
        step_number=1,
        name="Project Kickoff",
        description="Initial meeting with client",
        stage=WorkflowStage.INITIATION,
        status="completed",
        assigned_to_id=owner.id,
        start_date=datetime.utcnow() - timedelta(days=5),
        end_date=datetime.utcnow() - timedelta(days=4)
    )
    
    step2 = WorkflowStep(
        project_id=project.id,
        step_number=2,
        name="Market Research",
        description="Research target audience",
        stage=WorkflowStage.RESEARCH,
        status="completed",
        assigned_to_id=team_member.id,
        start_date=datetime.utcnow() - timedelta(days=3),
        end_date=datetime.utcnow() - timedelta(days=1)
    )
    
    step3 = WorkflowStep(
        project_id=project.id,
        step_number=3,
        name="Campaign Planning",
        description="Define campaign strategy and goals",
        stage=WorkflowStage.PLANNING,
        status="in_progress",
        assigned_to_id=owner.id,
        start_date=datetime.utcnow(),
        end_date=None
    )
    
    test_session.add_all([step1, step2, step3])
    await test_session.flush()
    
    # Create tasks
    task1 = MarketingTask(
        project_id=project.id,
        workflow_step_id=step3.id,
        title="Define Campaign Objectives",
        description="Establish clear goals and KPIs",
        task_type="planning",
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        due_date=datetime.utcnow() + timedelta(days=2),
        creator_id=owner.id,
        assignee_id=owner.id,
        estimated_hours=4.0
    )
    
    task2 = MarketingTask(
        project_id=project.id,
        workflow_step_id=step3.id,
        title="Create Content Calendar",
        description="Plan content delivery schedule",
        task_type="planning",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        due_date=datetime.utcnow() + timedelta(days=5),
        creator_id=owner.id,
        assignee_id=team_member.id,
        estimated_hours=6.0
    )
    
    # Create a task comment
    test_session.add_all([task1, task2])
    await test_session.flush()
    
    comment = MarketingTaskComment(
        task_id=task1.id,
        user_id=owner.id,
        content="Let's focus on conversion rate and engagement metrics."
    )
    
    test_session.add(comment)
    await test_session.commit()
    
    # Query the project with eager loading of workflow steps and tasks
    stmt = select(MarketingProject).where(MarketingProject.id == project.id).options(
        joinedload(MarketingProject.workflow_steps),
        joinedload(MarketingProject.tasks).joinedload(MarketingTask.comments)
    )
    result = await test_session.execute(stmt)
    fetched_project = result.scalars().first()
    
    # Assert workflow steps and tasks are correctly created
    assert fetched_project is not None
    assert len(fetched_project.workflow_steps) == 3
    assert len(fetched_project.tasks) == 2
    
    # Check workflow step progression
    steps = sorted(fetched_project.workflow_steps, key=lambda s: s.step_number)
    assert steps[0].name == "Project Kickoff"
    assert steps[0].status == "completed"
    assert steps[2].name == "Campaign Planning"
    assert steps[2].status == "in_progress"
    
    # Check tasks and comments
    tasks = {t.title: t for t in fetched_project.tasks}
    assert "Define Campaign Objectives" in tasks
    assert "Create Content Calendar" in tasks
    assert tasks["Define Campaign Objectives"].priority == TaskPriority.HIGH
    assert len(tasks["Define Campaign Objectives"].comments) == 1
    assert tasks["Define Campaign Objectives"].comments[0].content == "Let's focus on conversion rate and engagement metrics."
    
    # Clean up
    await test_session.delete(project)  # Should cascade delete steps and tasks
    await test_session.delete(client)
    await test_session.delete(owner)
    await test_session.delete(team_member)
    await test_session.commit()

@pytest.mark.asyncio
async def test_marketing_assets_and_reports(test_session):
    """Test creating marketing assets and analytics reports"""
    # Create users
    owner = User(
        email="asset_creator@example.com",
        username="creator",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True
    )
    
    approver = User(
        email="approver@example.com",
        username="approver",
        hashed_password="hashedpassword789",
        is_active=True,
        is_verified=True
    )
    
    test_session.add_all([owner, approver])
    await test_session.flush()
    
    # Create a client and project
    client = Client(
        company_name="Global Retail",
        industry="Retail",
        contact_name="Contact Person",
        contact_email="contact@global.example.com"
    )
    
    test_session.add(client)
    await test_session.flush()
    
    project = MarketingProject(
        name="Spring Collection Launch",
        description="Marketing campaign for spring collection",
        project_type=ProjectType.ADVERTISING,
        status=ProjectStatus.IN_PROGRESS,
        current_stage=WorkflowStage.EXECUTION,
        client_id=client.id,
        owner_id=owner.id
    )
    
    test_session.add(project)
    await test_session.flush()
    
    # Create a task
    task = MarketingTask(
        project_id=project.id,
        title="Design Campaign Banner",
        description="Create main banner for the campaign",
        status=TaskStatus.DONE,
        creator_id=owner.id,
        assignee_id=owner.id
    )
    
    test_session.add(task)
    await test_session.flush()
    
    # Create marketing assets
    asset1 = MarketingAsset(
        project_id=project.id,
        related_task_id=task.id,
        name="Campaign Banner Design",
        description="Main banner for spring campaign",
        asset_type=AssetType.DESIGN,
        file_path="/assets/spring_banner.psd",
        file_url="https://example.com/assets/spring_banner.jpg",
        file_size=2048576,
        mime_type="image/jpeg",
        version="1.0",
        is_final=True,
        creator_id=owner.id,
        approved_by_id=approver.id,
        approved_at=datetime.utcnow(),
        shared_with_client=True
    )
    
    asset2 = MarketingAsset(
        project_id=project.id,
        name="Campaign Strategy Brief",
        description="Strategy document outlining campaign approach",
        asset_type=AssetType.BRIEF,
        file_path="/assets/strategy_brief.docx",
        file_url="https://example.com/assets/strategy_brief.pdf",
        file_size=512000,
        mime_type="application/pdf",
        version="2.1",
        is_final=True,
        creator_id=owner.id,
        approved_by_id=approver.id,
        approved_at=datetime.utcnow(),
        shared_with_client=True
    )
    
    test_session.add_all([asset1, asset2])
    await test_session.flush()
    
    # Create analytics report
    report = AnalyticsReport(
        project_id=project.id,
        report_type=ReportType.ADVERTISING,
        title="Mid-Campaign Performance Report",
        description="Analysis of campaign performance after first two weeks",
        content="The campaign is performing well with 15% higher engagement than projected.",
        insights="Mobile users are engaging more than desktop users. Female demographic showing 20% higher conversion.",
        recommendations="Increase mobile ad spend by 10%. Create more content targeting female audience.",
        period_start=datetime.utcnow() - timedelta(days=14),
        period_end=datetime.utcnow(),
        is_draft=False,
        creator_id=owner.id,
        metrics="{\"impressions\": 250000, \"clicks\": 12500, \"conversions\": 3750}"
    )
    
    test_session.add(report)
    await test_session.commit()
    
    # Query the project with eager loading
    stmt = select(MarketingProject).where(MarketingProject.id == project.id).options(
        joinedload(MarketingProject.assets),
        joinedload(MarketingProject.reports)
    )
    result = await test_session.execute(stmt)
    fetched_project = result.scalars().first()
    
    # Assert assets and reports are correctly associated
    assert fetched_project is not None
    assert len(fetched_project.assets) == 2
    assert len(fetched_project.reports) == 1
    
    # Check asset details
    assets = {a.name: a for a in fetched_project.assets}
    assert "Campaign Banner Design" in assets
    assert "Campaign Strategy Brief" in assets
    assert assets["Campaign Banner Design"].asset_type == AssetType.DESIGN
    assert assets["Campaign Banner Design"].is_final == True
    assert assets["Campaign Strategy Brief"].version == "2.1"
    
    # Check report details
    report = fetched_project.reports[0]
    assert report.title == "Mid-Campaign Performance Report"
    assert report.report_type == ReportType.ADVERTISING
    assert report.is_draft == False
    assert "higher engagement than projected" in report.content
    
    # Clean up
    await test_session.delete(project)  # Should cascade delete assets and reports
    await test_session.delete(client)
    await test_session.delete(owner)
    await test_session.delete(approver)
    await test_session.commit()

@pytest.mark.asyncio
async def test_project_team_association(test_session):
    """Test adding team members to a marketing project"""
    # Create users
    project_manager = User(
        email="pm@example.com",
        username="projectmanager",
        hashed_password="hashedpassword111",
        is_active=True,
        is_verified=True
    )
    
    designer = User(
        email="designer@example.com",
        username="designer",
        hashed_password="hashedpassword222",
        is_active=True,
        is_verified=True
    )
    
    copywriter = User(
        email="copywriter@example.com",
        username="copywriter",
        hashed_password="hashedpassword333",
        is_active=True,
        is_verified=True
    )
    
    test_session.add_all([project_manager, designer, copywriter])
    await test_session.flush()
    
    # Create a project
    project = MarketingProject(
        name="Product Launch Campaign",
        description="New product line launch",
        project_type=ProjectType.INTEGRATED_CAMPAIGN,
        owner_id=project_manager.id
    )
    
    test_session.add(project)
    await test_session.flush()
    
    # Add team members using raw SQL due to many-to-many association table
    from sqlalchemy import text
    
    # Add project manager
    await test_session.execute(
        text("""
        INSERT INTO project_team_association 
        (project_id, user_id, role, joined_at) 
        VALUES (:project_id, :user_id, :role, :joined_at)
        """),
        {
            "project_id": project.id,
            "user_id": project_manager.id,
            "role": "Project Manager",
            "joined_at": datetime.utcnow()
        }
    )
    
    # Add designer
    await test_session.execute(
        text("""
        INSERT INTO project_team_association 
        (project_id, user_id, role, joined_at) 
        VALUES (:project_id, :user_id, :role, :joined_at)
        """),
        {
            "project_id": project.id,
            "user_id": designer.id,
            "role": "Lead Designer",
            "joined_at": datetime.utcnow()
        }
    )
    
    # Add copywriter
    await test_session.execute(
        text("""
        INSERT INTO project_team_association 
        (project_id, user_id, role, joined_at) 
        VALUES (:project_id, :user_id, :role, :joined_at)
        """),
        {
            "project_id": project.id,
            "user_id": copywriter.id,
            "role": "Content Writer",
            "joined_at": datetime.utcnow()
        }
    )
    
    await test_session.commit()
    
    # Query the project with eager loading of team members
    stmt = select(MarketingProject).where(MarketingProject.id == project.id).options(
        joinedload(MarketingProject.team_members)
    )
    result = await test_session.execute(stmt)
    fetched_project = result.scalars().first()
    
    # Assert team members are correctly associated
    assert fetched_project is not None
    assert len(fetched_project.team_members) == 3
    
    # Check team member usernames
    team_usernames = [member.username for member in fetched_project.team_members]
    assert "projectmanager" in team_usernames
    assert "designer" in team_usernames
    assert "copywriter" in team_usernames
    
    # Clean up
    # First remove the association table entries
    await test_session.execute(
        text("DELETE FROM project_team_association WHERE project_id = :project_id"),
        {"project_id": project.id}
    )
    
    await test_session.delete(project)
    await test_session.delete(project_manager)
    await test_session.delete(designer)
    await test_session.delete(copywriter)
    await test_session.commit()
