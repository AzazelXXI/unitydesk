from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Enum, Integer, DateTime, Float, Table, Index
from sqlalchemy.orm import relationship, backref
import enum
from datetime import datetime

from src.database import Base
from src.models_backup.base import RootModel
from src.models_backup.customer_service import ServiceTicket


# Forward declaration for ServiceTicket to avoid circular imports
# This will be resolved at SQLAlchemy mapper initialization time
ServiceTicket = None


class ProjectStatus(str, enum.Enum):
    """Status of a marketing project"""
    DRAFT = "draft"               # Initial planning stage
    APPROVED = "approved"         # Plan approved by client
    IN_PROGRESS = "in_progress"   # Project is being executed
    ON_HOLD = "on_hold"           # Project temporarily paused
    COMPLETED = "completed"       # Project finished
    CANCELLED = "cancelled"       # Project terminated


class ProjectType(str, enum.Enum):
    """Types of marketing projects"""
    CONTENT_CREATION = "content_creation"       # Content marketing projects
    BRAND_BUILDING = "brand_building"           # Brand development projects
    VIDEO_PRODUCTION = "video_production"       # Video/TVC production projects
    SOCIAL_MEDIA = "social_media"               # Social media campaigns
    ADVERTISING = "advertising"                 # Digital advertising campaigns
    MARKET_RESEARCH = "market_research"         # Market research projects
    INTEGRATED_CAMPAIGN = "integrated_campaign" # Combined marketing activities


class WorkflowStage(str, enum.Enum):
    """Stages in the marketing project workflow"""
    INITIATION = "initiation"                   # Project kickoff (step 1)
    RESEARCH = "research"                       # Customer research (steps 2-3)
    PLANNING = "planning"                       # Project planning (steps 4-6)
    EXECUTION = "execution"                     # Content creation & ads (steps 7-10)
    MONITORING = "monitoring"                   # Monitoring progress (steps 11-12)
    EVALUATION = "evaluation"                   # Review & lookback (steps 13-14)


class TaskPriority(str, enum.Enum):
    """Priority levels for marketing tasks"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, enum.Enum):
    """Status of marketing tasks"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


# Association table for project team members
project_team_association = Table(
    "project_team_association",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("marketing_projects.id", ondelete="CASCADE")),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("role", String(100)),  # Role in the project: project manager, creative, etc.
    Column("joined_at", DateTime, default=datetime.utcnow),
)


class MarketingProject(Base, RootModel):
    """Marketing project model for agency work"""
    __tablename__ = "marketing_projects"
    __table_args__ = (
        # Composite index for status-based filtering with dates (common query pattern)
        # This will speed up queries that filter projects by status and date range
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )
    
    name = Column(String(255), nullable=False, index=True)  # Added index for name searches
    description = Column(Text, nullable=True)
    project_type = Column(Enum(ProjectType), nullable=False, index=True)  # Added index for filtering by type
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, index=True)  # Added index for status filtering
    current_stage = Column(Enum(WorkflowStage), default=WorkflowStage.INITIATION, index=True)  # Added index for stage filtering
    
    # Client information
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)  # Added ondelete and index
    client_brief = Column(Text, nullable=True)  # Original client requirements
    
    # Dates and timeline
    start_date = Column(DateTime, nullable=True, index=True)  # Added index for date filtering
    target_end_date = Column(DateTime, nullable=True, index=True)  # Added index for deadline queries
    actual_end_date = Column(DateTime, nullable=True)
    
    # Budget information
    estimated_budget = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    
    # Project owner
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)  # Added ondelete and index
    
    # Relationships with optimized loading strategies
    owner = relationship("User", foreign_keys=[owner_id], lazy="joined")  # Eager load owner with project
    client = relationship("Client", back_populates="projects", lazy="joined")  # Eager load client with project
    team_members = relationship(
        "User", 
        secondary=project_team_association, 
        backref=backref("assigned_projects", lazy="selectin"),  # Optimized backref loading
        lazy="selectin"  # Efficient loading for collections
    )
    tasks = relationship(
        "MarketingTask", 
        back_populates="project", 
        cascade="all, delete-orphan", 
        lazy="selectin",  # Efficient loading for collections
        order_by="MarketingTask.due_date"  # Default ordering by due date
    )
    assets = relationship(
        "MarketingAsset", 
        back_populates="project", 
        cascade="all, delete-orphan",
        lazy="selectin"  # Efficient loading for collections
    )
    workflow_steps = relationship(
        "WorkflowStep", 
        back_populates="project", 
        cascade="all, delete-orphan",
        lazy="selectin",  # Efficient loading for collections
        order_by="WorkflowStep.step_number"  # Default ordering by step number
    )
    reports = relationship(
        "AnalyticsReport", 
        back_populates="project", 
        cascade="all, delete-orphan",
        lazy="selectin"  # Efficient loading for collections
    )


class Client(Base, RootModel):
    """Client model for marketing agency"""
    __tablename__ = "clients"
    __table_args__ = (
        # Index for client search by company name (frequent operation)
        Index('idx_client_company_name', 'company_name'),
        # Index for industry filtering
        Index('idx_client_industry', 'industry'),
    )
    
    company_name = Column(String(255), nullable=False, index=True)
    industry = Column(String(100), nullable=True, index=True)
    website = Column(String(255), nullable=True)
    logo_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Primary contact information
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True, index=True)  # Index for email searches
    contact_phone = Column(String(50), nullable=True)
      # Relationships with optimized loading
    projects = relationship(
        "MarketingProject", 
        back_populates="client",
        lazy="selectin",  # Efficient loading for collections
        order_by="desc(MarketingProject.created_at)"  # Order by newest first
    )
    contacts = relationship(
        "ClientContact", 
        back_populates="client", 
        cascade="all, delete-orphan",
        lazy="selectin"  # Efficient loading for collections
    )
    service_tickets = relationship(
        "ServiceTicket",
        back_populates="client",
        lazy="selectin"  # Efficient loading for collections
    )


class ClientContact(Base, RootModel):
    """Additional contacts for clients"""
    __tablename__ = "client_contacts"
    
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    position = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    is_primary = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    # Relationship
    client = relationship("Client", back_populates="contacts")


class WorkflowStep(Base, RootModel):
    """Steps in the marketing project workflow"""
    __tablename__ = "workflow_steps"
    __table_args__ = (
        # Composite index for finding steps by project and stage
        Index('idx_workflow_project_stage', 'project_id', 'stage'),
        # Composite index for step ordering within a project
        Index('idx_workflow_project_step_number', 'project_id', 'step_number'),
        # Index for status filtering
        Index('idx_workflow_status', 'status')
    )
    
    project_id = Column(Integer, ForeignKey("marketing_projects.id", ondelete="CASCADE"), index=True)
    step_number = Column(Integer, nullable=False)  # 1-14 based on workflow
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    stage = Column(Enum(WorkflowStage), nullable=False, index=True)
    status = Column(String(50), default="pending", index=True)  # pending, in_progress, completed, skipped
    start_date = Column(DateTime, nullable=True, index=True)  # Index for date filtering
    end_date = Column(DateTime, nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    
    # Relationships with optimized loading
    project = relationship("MarketingProject", back_populates="workflow_steps", lazy="joined")  # Always load the parent project
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], lazy="joined")  # Always load the assigned user
    tasks = relationship(
        "MarketingTask", 
        back_populates="workflow_step",
        lazy="selectin",  # Efficient loading for collections
        order_by="MarketingTask.priority.desc()"  # Order by priority (highest first)
    )


class MarketingTask(Base, RootModel):
    """Tasks within marketing projects"""
    __tablename__ = "marketing_tasks"
    
    project_id = Column(Integer, ForeignKey("marketing_projects.id", ondelete="CASCADE"))
    workflow_step_id = Column(Integer, ForeignKey("workflow_steps.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(100), nullable=True)  # research, content, production, advertising, analytics
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Dates
    due_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    
    # Assignment
    creator_id = Column(Integer, ForeignKey("users.id"))
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Parent-child relationship for subtasks
    parent_task_id = Column(Integer, ForeignKey("marketing_tasks.id"), nullable=True)
    
    # Estimated and actual hours
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    
    # Completion tracking
    completion_percentage = Column(Integer, default=0)
      # Relationships
    project = relationship("MarketingProject", back_populates="tasks")
    workflow_step = relationship("WorkflowStep", back_populates="tasks")
    creator = relationship("User", foreign_keys=[creator_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    parent_task = relationship("MarketingTask", remote_side="MarketingTask.id", backref="subtasks")
    comments = relationship("MarketingTaskComment", back_populates="task", cascade="all, delete-orphan")
    assets = relationship("MarketingAsset", back_populates="related_task")


class MarketingTaskComment(Base, RootModel):
    """Comments on marketing tasks"""
    __tablename__ = "marketing_task_comments"
    
    task_id = Column(Integer, ForeignKey("marketing_tasks.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    
    # Relationships
    task = relationship("MarketingTask", back_populates="comments")
    user = relationship("User")


class AssetType(str, enum.Enum):
    """Types of marketing assets"""
    BRIEF = "brief"                # Client brief
    RESEARCH = "research"          # Market/customer research
    CONTENT_PLAN = "content_plan"  # Content planning document
    SCRIPT = "script"              # Video/TVC script
    DESIGN = "design"              # Graphic design files
    VIDEO = "video"                # Video files
    AUDIO = "audio"                # Audio files
    IMAGE = "image"                # Image files
    DOCUMENT = "document"          # Text documents
    PRESENTATION = "presentation"  # Presentations
    REPORT = "report"              # Analytics or performance reports
    OTHER = "other"                # Other asset types


class MarketingAsset(Base, RootModel):
    """Digital assets for marketing projects"""
    __tablename__ = "marketing_assets"
    
    project_id = Column(Integer, ForeignKey("marketing_projects.id", ondelete="CASCADE"))
    related_task_id = Column(Integer, ForeignKey("marketing_tasks.id", ondelete="SET NULL"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    
    # File information
    file_path = Column(String(255), nullable=True)  # Path in storage system
    file_url = Column(String(255), nullable=True)   # URL for access
    file_size = Column(Integer, nullable=True)      # Size in bytes
    mime_type = Column(String(100), nullable=True)  # MIME type of the file
    
    # Versioning
    version = Column(String(20), default="1.0")
    is_final = Column(Boolean, default=False)
    
    # Creator and approval
    creator_id = Column(Integer, ForeignKey("users.id"))
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Client sharing
    shared_with_client = Column(Boolean, default=False)
    client_feedback = Column(Text, nullable=True)
    
    # Relationships
    project = relationship("MarketingProject", back_populates="assets")
    related_task = relationship("MarketingTask", back_populates="assets")
    creator = relationship("User", foreign_keys=[creator_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])


class ReportType(str, enum.Enum):
    """Types of marketing analytics reports"""
    PERFORMANCE = "performance"           # Campaign performance report
    BUDGET = "budget"                     # Budget tracking report
    PROGRESS = "progress"                 # Project progress report
    MARKET_RESEARCH = "market_research"   # Market research findings
    SOCIAL_MEDIA = "social_media"         # Social media performance
    SEO = "seo"                           # SEO performance report
    ADVERTISING = "advertising"           # Advertising campaign report
    FINAL = "final"                       # Final project report


class AnalyticsReport(Base, RootModel):
    """Analytics and reporting for marketing projects"""
    __tablename__ = "analytics_reports"
    
    project_id = Column(Integer, ForeignKey("marketing_projects.id", ondelete="CASCADE"))
    report_type = Column(Enum(ReportType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Report content
    content = Column(Text, nullable=True)
    insights = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    
    # Report period
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    # Report status
    is_draft = Column(Boolean, default=True)
    
    # Creator and approver
    creator_id = Column(Integer, ForeignKey("users.id"))
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # File information if report is stored as file
    file_path = Column(String(255), nullable=True)
    file_url = Column(String(255), nullable=True)
    
    # Metrics - stored as JSON string or in related tables for complex reports
    metrics = Column(Text, nullable=True)  # JSON string of metrics
    
    # Relationships
    project = relationship("MarketingProject", back_populates="reports")
    creator = relationship("User", foreign_keys=[creator_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
