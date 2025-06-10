from fastapi import HTTPException, status


class TaskNotFoundError(HTTPException):
    def __init__(self, task_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )


class UnauthorizedTaskAccessError(HTTPException):
    def __init__(self, task_id: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have permission to access task {task_id}"
        )


class TaskValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Task validation error: {message}"
        )


class CircularDependencyError(HTTPException):
    def __init__(self, task_id: int, dependency_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create circular dependency between task {task_id} and task {dependency_id}"
        )


class ProjectNotFoundError(HTTPException):
    def __init__(self, project_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )


class TaskDependencyError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task dependency error: {message}"
        )


class TaskAssignmentError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task assignment error: {message}"
        )
