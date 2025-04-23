from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Enum, Integer, DateTime, Float, Table
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from src.database import Base
from src.models.base import BaseModel


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


class MarketingProject(Base, BaseModel):
    """Marketing project model for agency work"""
    __tablename__ = "marketing_projects"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    project_type = Column(Enum(ProjectType), nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    current_stage = Column(Enum(WorkflowStage), default=WorkflowStage.INITIATION)
    
    # Client information
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    client_brief = Column(Text, nullable=True)  # Original client requirements
    
    # Dates and timeline
    start_date = Column(DateTime, nullable=True)
    target_end_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)
    
    # Budget information
    estimated_budget = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    
    # Project owner
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    client = relationship("Client", back_populates="projects")
    team_members = relationship("User", secondary=project_team_association, backref="assigned_projects")
    tasks = relationship("MarketingTask", back_populates="project", cascade="all, delete-orphan")
    assets = relationship("MarketingAsset", back_populates="project", cascade="all, delete-orphan")
    workflow_steps = relationship("WorkflowStep", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("AnalyticsReport", back_populates="project", cascade="all, delete-orphan")


class Client(Base, BaseModel):
    """Client model for marketing agency"""
    __tablename__ = "clients"
    
    company_name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    logo_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Primary contact information
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Relationships
    projects = relationship("MarketingProject", back_populates="client")
    contacts = relationship("ClientContact", back_populates="client", cascade="all, delete-orphan")


class ClientContact(Base, BaseModel):
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


class WorkflowStep(Base, BaseModel):
    """Steps in the marketing project workflow"""
    __tablename__ = "workflow_steps"
    
    project_id = Column(Integer, ForeignKey("marketing_projects.id", ondelete="CASCADE"))
    step_number = Column(Integer, nullable=False)  # 1-14 based on workflow
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    stage = Column(Enum(WorkflowStage), nullable=False)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, skipped
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    project = relationship("MarketingProject", back_populates="workflow_steps")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    tasks = relationship("MarketingTask", back_populates="workflow_step")


class MarketingTask(Base, BaseModel):
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
    parent_task = relationship("MarketingTask", remote_side=[id], backref="subtasks")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    assets = relationship("MarketingAsset", back_populates="related_task")


class TaskComment(Base, BaseModel):
    """Comments on marketing tasks"""
    __tablename__ = "task_comments"
    
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


class MarketingAsset(Base, BaseModel):
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


class AnalyticsReport(Base, BaseModel):
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
