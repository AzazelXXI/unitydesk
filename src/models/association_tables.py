from sqlalchemy import Column, ForeignKey, Table, Integer, UUID
from .base import Base

# This file use to define association Many-To-Many relationship

project_teams_table = Table(
    "project_teams",
    Base.metadata,
    Column(
        "project_id", UUID(as_uuid=True), ForeignKey("projects.id"), primary_key=True
    ),
    Column("team_id", UUID(as_uuid=True), ForeignKey("teams.id"), primary_key=True),
)

task_attachment_table = Table(
    "task_attachments",
    Base.metadata,
    Column("task_id", UUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True),
    Column(
        "attachment_id",
        UUID(as_uuid=True),
        ForeignKey("attachments.id"),
        primary_key=True,
    ),
)
