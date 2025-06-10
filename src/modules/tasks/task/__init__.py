"""
Task management module for CSA-HELLO IT project management system.

This module provides complete CRUD operations for task management including:
- Task creation, reading, updating, and deletion
- Task assignment and dependency management
- Task filtering, searching, and pagination
- Task statistics and reporting
"""

from .routes import router
from .service import TaskService
from .schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskAssignmentUpdate,
    TaskDependencyUpdate,
    TaskStatsResponse,
    TaskStatus,
    TaskPriority,
)

__all__ = [
    "router",
    "TaskService",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskListResponse",
    "TaskAssignmentUpdate",
    "TaskDependencyUpdate",
    "TaskStatsResponse",
    "TaskStatus",
    "TaskPriority",
]
