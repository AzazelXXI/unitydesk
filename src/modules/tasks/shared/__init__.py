"""
Shared utilities and common components for the tasks module.
"""

from .auth import *
from .pagination import *
from .exceptions import *
from .validators import *

__all__ = [
    # Auth utilities
    "get_current_user_id",
    "verify_user_permissions",
    "check_project_membership",
    
    # Pagination utilities
    "PaginationParams",
    "PaginatedResponse",
    "paginate_query",
    
    # Exception handling
    "TaskModuleException",
    "TaskNotFoundError",
    "TaskPermissionError",
    "TaskValidationError",
    
    # Validators
    "validate_date_range",
    "validate_task_assignees",
    "validate_task_dependencies",
]
