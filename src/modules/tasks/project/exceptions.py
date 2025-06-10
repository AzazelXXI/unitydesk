from fastapi import HTTPException, status


class ProjectNotFoundError(HTTPException):
    def __init__(self, project_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )


class UnauthorizedProjectAccessError(HTTPException):
    def __init__(self, project_id: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have permission to access project {project_id}",
        )


class ProjectValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Project validation error: {message}",
        )
