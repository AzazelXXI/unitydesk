from .base import Base
from .user import (
    User,
    UserProfile,
    ProjectManager,
    TeamLeader,
    Developer,
    Tester,
    Designer,
    SystemAdmin,
)
from .project import Project
from .custom_project_status import ProjectCustomStatus
from .task import Task
from .comment import Comment
from .attachment import Attachment
from .milestone import Milestone
from .risk import Risk
from .notification import Notification
from .calendar import Calendar
from .event import Event

# from .department import Department, Position, DepartmentMembership  # Commented out to prevent startup errors
from .association_tables import (
    project_members,
    task_assignees,
    task_attachments,
    task_dependencies,
)

__all__ = [
    "Base",
    "User",
    "UserProfile",
    "ProjectManager",
    "TeamLeader",
    "Developer",
    "Tester",
    "Designer",
    "SystemAdmin",
    "Project",
    "ProjectCustomStatus",
    "Task",
    "Comment",
    "Attachment",
    "Milestone",
    "Risk",
    "Notification",
    "Calendar",
    "Event",
    # "Department",
    # "Position",
    # "DepartmentMembership",  # Commented out to prevent startup errors
    "project_members",
    "task_assignees",
    "task_attachments",
    "task_dependencies",
]
