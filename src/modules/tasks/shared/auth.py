"""
Authentication and authorization utilities for the tasks module.
"""
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.project import Project
from src.models.association_tables import project_members


def get_current_user_id() -> int:
    """
    Get current authenticated user ID.
    This is a placeholder - implement based on your authentication system.
    """
    # TODO: Implement actual authentication logic
    # This could involve JWT token validation, session checking, etc.
    return 1  # Mock user ID


def verify_user_permissions(user: User, required_roles: List[str]) -> bool:
    """
    Verify if user has required permissions.
    
    Args:
        user: User object
        required_roles: List of required user types/roles
        
    Returns:
        bool: True if user has required permissions
    """
    if not user:
        return False
    
    return user.user_type in required_roles


def check_project_membership(db: Session, user_id: int, project_id: int) -> bool:
    """
    Check if user is a member of the specified project.
    
    Args:
        db: Database session
        user_id: User ID to check
        project_id: Project ID to check membership for
        
    Returns:
        bool: True if user is project member
    """
    # Check if user is project owner
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == user_id
    ).first()
    
    if project:
        return True
    
    # Check if user is project member
    membership = db.execute(
        project_members.select().where(
            (project_members.c.project_id == project_id) &
            (project_members.c.user_id == user_id)
        )
    ).first()
    
    return membership is not None


def check_admin_or_project_access(db: Session, user: User, project_id: int) -> bool:
    """
    Check if user is admin or has access to the project.
    
    Args:
        db: Database session
        user: User object
        project_id: Project ID to check access for
        
    Returns:
        bool: True if user has access
    """
    # System admin has access to everything
    if user.user_type == "system_admin":
        return True
    
    # Project managers have access to all projects (in this implementation)
    if user.user_type == "project_manager":
        return True
    
    # Check project membership for other users
    return check_project_membership(db, user.id, project_id)


def require_authentication():
    """
    Dependency that requires user authentication.
    Raises HTTPException if user is not authenticated.
    """
    def _require_auth() -> User:
        # TODO: Implement actual authentication check
        # This should validate JWT token, session, etc.
        user = User()
        user.id = get_current_user_id()
        user.username = "admin"
        user.email = "admin@example.com"
        user.user_type = "system_admin"
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    return _require_auth


def require_role(required_roles: List[str]):
    """
    Dependency factory that requires specific user roles.
    
    Args:
        required_roles: List of required user types/roles
        
    Returns:
        Dependency function that validates user role
    """
    def _require_role(user: User = require_authentication()) -> User:
        if not verify_user_permissions(user, required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}"
            )
        return user
    
    return _require_role


def require_project_access(project_id_param: str = "project_id"):
    """
    Dependency factory that requires project access.
    
    Args:
        project_id_param: Name of the path parameter containing project ID
        
    Returns:
        Dependency function that validates project access
    """
    def _require_project_access(
        db: Session,
        user: User = require_authentication()
    ) -> User:
        # This would need to extract project_id from path parameters
        # Implementation depends on how you handle path parameters in FastAPI
        # For now, this is a placeholder
        project_id = 1  # TODO: Extract from path parameters
        
        if not check_admin_or_project_access(db, user, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project"
            )
        
        return user
    
    return _require_project_access


# Common role requirements
require_admin = require_role(["system_admin"])
require_manager = require_role(["system_admin", "project_manager"])
require_leader = require_role(["system_admin", "project_manager", "team_leader"])


class AuthContext:
    """Authentication context helper class."""
    
    def __init__(self, user: User, db: Session):
        self.user = user
        self.db = db
    
    def is_admin(self) -> bool:
        """Check if current user is admin."""
        return self.user.user_type == "system_admin"
    
    def is_manager(self) -> bool:
        """Check if current user is manager or admin."""
        return self.user.user_type in ["system_admin", "project_manager"]
    
    def is_leader(self) -> bool:
        """Check if current user is team leader, manager, or admin."""
        return self.user.user_type in ["system_admin", "project_manager", "team_leader"]
    
    def can_access_project(self, project_id: int) -> bool:
        """Check if user can access project."""
        return check_admin_or_project_access(self.db, self.user, project_id)
    
    def can_manage_project(self, project_id: int) -> bool:
        """Check if user can manage project."""
        if self.is_admin():
            return True
        
        # Check if user is project owner
        project = self.db.query(Project).filter(
            Project.id == project_id,
            Project.owner_id == self.user.id
        ).first()
        
        return project is not None
    
    def get_accessible_projects(self) -> List[int]:
        """Get list of project IDs user can access."""
        if self.is_admin() or self.is_manager():
            # Admin and managers can access all projects
            projects = self.db.query(Project.id).all()
            return [p.id for p in projects]
        
        # Get projects where user is owner or member
        owned_projects = self.db.query(Project.id).filter(
            Project.owner_id == self.user.id
        ).all()
        
        member_projects = self.db.execute(
            project_members.select().where(
                project_members.c.user_id == self.user.id
            )
        ).fetchall()
        
        project_ids = [p.id for p in owned_projects]
        project_ids.extend([p.project_id for p in member_projects])
        
        return list(set(project_ids))  # Remove duplicates
