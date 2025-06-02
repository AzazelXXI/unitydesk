from sqlalchemy import Column, ForeignKey, Table, Integer, UUID, String
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

# team_members_table = Table(
#     "team_members",
#     Base.metadata,
#     Column("team_id", UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
#     Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
#     Column("role", String(50), default="Member", nullable=False)  # Ví dụ: "Leader", "Member"
# )
