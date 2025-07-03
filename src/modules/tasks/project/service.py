from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException

from src.models.project import Project
from src.models.user import User
from src.models.association_tables import project_members
from .schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from .exceptions import ProjectNotFoundError, UnauthorizedProjectAccessError


class ProjectService:

    @staticmethod
    async def create_project(
        project_data: ProjectCreate, owner_id: str, db: AsyncSession
    ) -> ProjectResponse:
        """Create a new project"""
        try:
            # Create project instance
            project = Project(
                **project_data.dict(exclude={"team_members"}),
                owner_id=owner_id,
                status="PLANNING",
                progress=0.0,
            )

            db.add(project)
            await db.commit()
            await db.refresh(project)

            # Add team members if provided
            if project_data.team_members:
                await ProjectService._add_team_members(
                    project.id, project_data.team_members, db
                )

            return ProjectResponse.from_orm(project)

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to create project: {str(e)}"
            )

    @staticmethod
    async def get_projects(
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        db: AsyncSession = None,
    ) -> List[ProjectResponse]:
        """Get projects accessible to user"""
        query = select(Project).where(
            or_(
                Project.owner_id == user_id,
                Project.team_leader_id == user_id,
                Project.id.in_(
                    select(project_members.c.project_id).where(
                        project_members.c.user_id == user_id
                    )
                ),
            )
        )

        if status_filter:
            query = query.where(Project.status == status_filter)

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        projects = result.scalars().all()

        return [ProjectResponse.from_orm(project) for project in projects]

    @staticmethod
    async def get_project_by_id(
        project_id: str, user_id: str, db: AsyncSession
    ) -> ProjectResponse:
        """Get project by ID with access control"""
        project = await ProjectService._get_project_with_access_check(
            project_id, user_id, db
        )
        return ProjectResponse.from_orm(project)

    @staticmethod
    async def update_project(
        project_id: str, project_data: ProjectUpdate, user_id: str, db: AsyncSession
    ) -> ProjectResponse:
        """Update project (only owner can update)"""
        project = await ProjectService._get_project_with_access_check(
            project_id, user_id, db, require_owner=True
        )

        # Update fields
        update_data = project_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        try:
            await db.commit()
            await db.refresh(project)
            return ProjectResponse.from_orm(project)
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to update project: {str(e)}"
            )

    @staticmethod
    async def delete_project(project_id: str, user_id: str, db: AsyncSession):
        """Delete project (only owner can delete)"""
        project = await ProjectService._get_project_with_access_check(
            project_id, user_id, db, require_owner=True
        )

        try:
            await db.delete(project)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to delete project: {str(e)}"
            )

    @staticmethod
    async def _get_project_with_access_check(
        project_id: str, user_id: str, db: AsyncSession, require_owner: bool = False
    ) -> Project:
        """Helper method to get project with access control"""
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise ProjectNotFoundError(project_id)

        # Check access permissions
        if require_owner:
            if project.owner_id != user_id:
                raise UnauthorizedProjectAccessError(project_id)
        else:
            # Check if user has any access (owner, team leader, or team member)
            has_access = (
                project.owner_id == user_id or project.team_leader_id == user_id
            )

            if not has_access:
                # Check team membership
                member_result = await db.execute(
                    select(project_members).where(
                        and_(
                            project_members.c.project_id == project_id,
                            project_members.c.user_id == user_id,
                        )
                    )
                )
                has_access = member_result.first() is not None

            if not has_access:
                raise UnauthorizedProjectAccessError(project_id)

        return project
