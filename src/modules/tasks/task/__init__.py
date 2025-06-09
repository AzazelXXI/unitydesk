"""
Task management module for CSA-HELLO IT project management system.

This module provides complete CRUD operations for task management including:
- Task creation, reading, updating, and deletion
- Task assignment and dependency management
- Task filtering, searching, and pagination
- Task statistics and reporting
"""

from .routes import router as task_router
from .service import TaskService
from .schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    TaskQueryParams, TaskStatsResponse, TaskStatus, TaskPriority
)
from .dependencies import (
    get_task_service, verify_task_access, TaskPermissions
)

__all__ = [
    "task_router",
    "TaskService", 
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskListResponse",
    "TaskQueryParams",
    "TaskStatsResponse",
    "TaskStatus",
    "TaskPriority",
    "get_task_service",
    "verify_task_access",
    "TaskPermissions"
]