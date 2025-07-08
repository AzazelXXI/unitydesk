# Association table for comment attachments
from sqlalchemy import Table, Column, Integer, ForeignKey
from .base import Base

comment_attachments = Table(
    "comment_attachments",
    Base.metadata,
    Column("comment_id", Integer, ForeignKey("comments.id"), primary_key=True),
    Column("attachment_id", Integer, ForeignKey("attachments.id"), primary_key=True),
)
from sqlalchemy import Column, ForeignKey, Table, Integer, String, DateTime
from datetime import datetime
from .base import Base

# Association tables for Many-To-Many relationships

# Project members - replaces project_teams
project_members = Table(
    "project_members",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("joined_at", DateTime, default=datetime.utcnow),
)

# Task assignees - many users can be assigned to one task
task_assignees = Table(
    "task_assignees",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("assigned_at", DateTime, default=datetime.utcnow),
)

# Task attachments - many tasks can have many attachments
task_attachments = Table(
    "task_attachments",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("attachment_id", Integer, ForeignKey("attachments.id"), primary_key=True),
    Column("attached_at", DateTime, default=datetime.utcnow),
)

# Task dependencies - a task can depend on other tasks
task_dependencies = Table(
    "task_dependencies",
    Base.metadata,
    Column(
        "task_id", Integer, ForeignKey("tasks.id"), primary_key=True
    ),  # The task that depends
    Column(
        "depends_on_task_id", Integer, ForeignKey("tasks.id"), primary_key=True
    ),  # The task it depends on
    Column("created_at", DateTime, default=datetime.utcnow),
)
