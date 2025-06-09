"""
Custom exceptions for the tasks module.
"""
from typing import Optional, Dict, Any


class TaskModuleException(Exception):
    """Base exception for all task module errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        result = {
            "error": self.__class__.__name__,
            "message": self.message
        }
        
        if self.error_code:
            result["error_code"] = self.error_code
        
        if self.details:
            result["details"] = self.details
        
        return result


class TaskNotFoundError(TaskModuleException):
    """Raised when a task is not found."""
    
    def __init__(self, task_id: int):
        super().__init__(
            f"Task with ID {task_id} not found",
            error_code="TASK_NOT_FOUND",
            details={"task_id": task_id}
        )


class TaskPermissionError(TaskModuleException):
    """Raised when user doesn't have permission to perform an action on a task."""
    
    def __init__(self, action: str, task_id: Optional[int] = None, user_id: Optional[int] = None):
        message = f"Permission denied for action '{action}'"
        if task_id:
            message += f" on task {task_id}"
        
        details = {"action": action}
        if task_id:
            details["task_id"] = task_id
        if user_id:
            details["user_id"] = user_id
        
        super().__init__(
            message,
            error_code="TASK_PERMISSION_DENIED",
            details=details
        )


class TaskValidationError(TaskModuleException):
    """Raised when task data validation fails."""
    
    def __init__(self, field: str, message: str, value: Any = None):
        details = {"field": field, "message": message}
        if value is not None:
            details["value"] = value
        
        super().__init__(
            f"Validation error for field '{field}': {message}",
            error_code="TASK_VALIDATION_ERROR",
            details=details
        )


class TaskDependencyError(TaskModuleException):
    """Raised when there's an issue with task dependencies."""
    
    def __init__(self, message: str, task_id: Optional[int] = None, depends_on_id: Optional[int] = None):
        details = {}
        if task_id:
            details["task_id"] = task_id
        if depends_on_id:
            details["depends_on_id"] = depends_on_id
        
        super().__init__(
            message,
            error_code="TASK_DEPENDENCY_ERROR",
            details=details
        )


class CircularDependencyError(TaskDependencyError):
    """Raised when adding a dependency would create a circular dependency."""
    
    def __init__(self, task_id: int, depends_on_id: int):
        super().__init__(
            f"Adding dependency from task {task_id} to task {depends_on_id} would create a circular dependency",
            task_id=task_id,
            depends_on_id=depends_on_id
        )
        self.error_code = "CIRCULAR_DEPENDENCY_ERROR"


class TaskAssignmentError(TaskModuleException):
    """Raised when there's an issue with task assignment."""
    
    def __init__(self, message: str, task_id: Optional[int] = None, user_id: Optional[int] = None):
        details = {}
        if task_id:
            details["task_id"] = task_id
        if user_id:
            details["user_id"] = user_id
        
        super().__init__(
            message,
            error_code="TASK_ASSIGNMENT_ERROR",
            details=details
        )


class ProjectNotFoundError(TaskModuleException):
    """Raised when a project is not found."""
    
    def __init__(self, project_id: int):
        super().__init__(
            f"Project with ID {project_id} not found",
            error_code="PROJECT_NOT_FOUND",
            details={"project_id": project_id}
        )


class UserNotFoundError(TaskModuleException):
    """Raised when a user is not found."""
    
    def __init__(self, user_id: int):
        super().__init__(
            f"User with ID {user_id} not found",
            error_code="USER_NOT_FOUND",
            details={"user_id": user_id}
        )


class InvalidDateRangeError(TaskValidationError):
    """Raised when date range is invalid (e.g., due date before start date)."""
    
    def __init__(self, start_date: str, due_date: str):
        super().__init__(
            "date_range",
            f"Due date ({due_date}) cannot be earlier than start date ({start_date})",
            {"start_date": start_date, "due_date": due_date}
        )


class TaskStatusTransitionError(TaskModuleException):
    """Raised when an invalid task status transition is attempted."""
    
    def __init__(self, current_status: str, new_status: str, task_id: Optional[int] = None):
        details = {
            "current_status": current_status,
            "new_status": new_status
        }
        if task_id:
            details["task_id"] = task_id
        
        super().__init__(
            f"Invalid status transition from '{current_status}' to '{new_status}'",
            error_code="INVALID_STATUS_TRANSITION",
            details=details
        )


class TaskConcurrencyError(TaskModuleException):
    """Raised when there's a concurrency conflict (e.g., task updated by another user)."""
    
    def __init__(self, task_id: int):
        super().__init__(
            f"Task {task_id} was modified by another user. Please refresh and try again.",
            error_code="TASK_CONCURRENCY_CONFLICT",
            details={"task_id": task_id}
        )


class TaskQuotaExceededError(TaskModuleException):
    """Raised when task creation would exceed project or user limits."""
    
    def __init__(self, limit_type: str, current_count: int, max_allowed: int):
        super().__init__(
            f"Task {limit_type} limit exceeded: {current_count}/{max_allowed}",
            error_code="TASK_QUOTA_EXCEEDED",
            details={
                "limit_type": limit_type,
                "current_count": current_count,
                "max_allowed": max_allowed
            }
        )


# Exception handler utilities
def handle_task_exception(exc: Exception) -> Dict[str, Any]:
    """
    Convert various exceptions to standardized error responses.
    
    Args:
        exc: Exception to handle
        
    Returns:
        Dictionary representation of the error
    """
    if isinstance(exc, TaskModuleException):
        return exc.to_dict()
    
    # Handle SQLAlchemy exceptions
    elif hasattr(exc, '__module__') and 'sqlalchemy' in exc.__module__:
        return {
            "error": "DatabaseError",
            "message": "A database error occurred",
            "error_code": "DATABASE_ERROR"
        }
    
    # Handle validation exceptions from Pydantic
    elif hasattr(exc, 'errors'):  # Pydantic ValidationError
        return {
            "error": "ValidationError",
            "message": "Request validation failed",
            "error_code": "VALIDATION_ERROR",
            "details": {"validation_errors": exc.errors()}
        }
    
    # Generic exception handling
    else:
        return {
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_SERVER_ERROR"
        }


def create_http_exception_from_task_exception(exc: TaskModuleException) -> tuple[int, Dict[str, Any]]:
    """
    Convert task module exception to HTTP status code and response body.
    
    Args:
        exc: TaskModuleException to convert
        
    Returns:
        Tuple of (status_code, response_body)
    """
    status_code_map = {
        "TASK_NOT_FOUND": 404,
        "PROJECT_NOT_FOUND": 404,
        "USER_NOT_FOUND": 404,
        "TASK_PERMISSION_DENIED": 403,
        "TASK_VALIDATION_ERROR": 400,
        "TASK_DEPENDENCY_ERROR": 400,
        "CIRCULAR_DEPENDENCY_ERROR": 400,
        "TASK_ASSIGNMENT_ERROR": 400,
        "INVALID_STATUS_TRANSITION": 400,
        "TASK_CONCURRENCY_CONFLICT": 409,
        "TASK_QUOTA_EXCEEDED": 429,
        "DATABASE_ERROR": 500,
        "INTERNAL_SERVER_ERROR": 500
    }
    
    status_code = status_code_map.get(exc.error_code, 500)
    response_body = exc.to_dict()
    
    return status_code, response_body
