from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from fastapi import HTTPException, status

from src.models.marketing_project import (
    MarketingProject, ProjectStatus, ProjectType, WorkflowStage, 
    WorkflowStep, MarketingTask, TaskStatus
)
from src.schemas.marketing_project import (
    MarketingProjectCreate, MarketingProjectUpdate, MarketingProjectRead,
    MarketingProjectReadBasic, ProjectTeamMember
)

# Configure logging
logger = logging.getLogger(__name__)

class ProjectController:
    """Controller for handling marketing project operations"""
    
    @staticmethod
    async def create_project(project_data: MarketingProjectCreate, db: AsyncSession) -> MarketingProject:
        """
        Create a new marketing project
        """
        try:
            # Create new project
            new_project = MarketingProject(
                name=project_data.name,
                description=project_data.description,
                project_type=project_data.project_type,
                status=project_data.status,
                current_stage=project_data.current_stage,
                client_id=project_data.client_id,
                client_brief=project_data.client_brief,
                start_date=project_data.start_date,
                target_end_date=project_data.target_end_date,
                actual_end_date=project_data.actual_end_date,
                estimated_budget=project_data.estimated_budget,
                actual_cost=project_data.actual_cost,
                owner_id=project_data.owner_id
            )
            
            db.add(new_project)
            await db.commit()
            await db.refresh(new_project)
            
            # Add team members if provided
            if project_data.team_members:
                for member in project_data.team_members:
                    await ProjectController._add_team_member(new_project.id, member, db)
            
            # Create workflow steps for the project
            await ProjectController._initialize_workflow(new_project.id, db)
            
            logger.info(f"Created new marketing project: {new_project.name}")
            
            # Return the project with detailed information
            return await ProjectController.get_project(new_project.id, db)
        except Exception as e:
            logger.error(f"Error creating marketing project: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create marketing project: {str(e)}"
            )
    
    @staticmethod
    async def _add_team_member(project_id: int, member_data: ProjectTeamMember, db: AsyncSession):
        """Helper method to add a team member to a project"""
        # This would be implemented based on your project-user relationship model
        # For simplicity, assuming you have a project_team_members table
        pass
    
    @staticmethod
    async def _initialize_workflow(project_id: int, db: AsyncSession):
        """Helper method to initialize workflow steps for a new project"""
        # Create all workflow steps for the project
        steps = [
            # Define all workflow steps based on your business process
            # Example:
            WorkflowStep(
                project_id=project_id,
                step_number=1,
                name="Project Initiation",
                description="Kick off the project and gather requirements",
                stage=WorkflowStage.INITIATION,
                status="pending"
            ),
            WorkflowStep(
                project_id=project_id,
                step_number=2,
                name="Strategy Development",
                description="Develop marketing strategy and approach",
                stage=WorkflowStage.PLANNING,
                status="pending"
            ),
            # Add more steps as needed
        ]
        
        for step in steps:
            db.add(step)
        
        await db.commit()
    
    @staticmethod
    async def get_projects(
        skip: int = 0,
        limit: int = 100,
        status: Optional[ProjectStatus] = None,
        project_type: Optional[ProjectType] = None,
        client_id: Optional[int] = None,
        search: Optional[str] = None,
        db: AsyncSession = None
    ) -> List[MarketingProject]:
        """
        Get all marketing projects with optional filtering
        """
        try:
            query = select(MarketingProject).options(
                joinedload(MarketingProject.client)
            ).offset(skip).limit(limit)
            
            # Apply filters if provided
            if status:
                query = query.filter(MarketingProject.status == status)
            if project_type:
                query = query.filter(MarketingProject.project_type == project_type)
            if client_id:
                query = query.filter(MarketingProject.client_id == client_id)
            if search:
                query = query.filter(MarketingProject.name.ilike(f"%{search}%"))
            
            result = await db.execute(query)
            projects = result.scalars().unique().all()
            
            # For each project, calculate progress and task stats
            for project in projects:
                project.task_stats = await ProjectController._calculate_task_stats(project.id, db)
                project.workflow_progress = await ProjectController._calculate_workflow_progress(project.id, db)
            
            return projects
        except Exception as e:
            logger.error(f"Error fetching projects: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch projects: {str(e)}"
            )
    
    @staticmethod
    async def get_project(project_id: int, db: AsyncSession) -> MarketingProject:
        """
        Get a specific marketing project by ID
        """
        try:
            query = select(MarketingProject).filter(
                MarketingProject.id == project_id
            ).options(
                joinedload(MarketingProject.client)
            )
            
            result = await db.execute(query)
            project = result.scalars().unique().first()
            
            if not project:
                logger.warning(f"Marketing project with ID {project_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Marketing project with ID {project_id} not found"
                )
            
            # Calculate additional data
            project.task_stats = await ProjectController._calculate_task_stats(project_id, db)
            project.workflow_progress = await ProjectController._calculate_workflow_progress(project_id, db)
            
            # Get team members
            # This would be implemented based on your project-user relationship model
            project.team_members = []
            
            return project
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching project {project_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch project: {str(e)}"
            )
    
    @staticmethod
    async def update_project(project_id: int, project_data: MarketingProjectUpdate, db: AsyncSession) -> MarketingProject:
        """
        Update a marketing project
        """
        try:
            # Get the project
            query = select(MarketingProject).filter(MarketingProject.id == project_id)
            result = await db.execute(query)
            project = result.scalars().first()
            
            if not project:
                logger.warning(f"Marketing project with ID {project_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Marketing project with ID {project_id} not found"
                )
            
            # Update project attributes
            update_data = project_data.dict(exclude_unset=True)
            
            # Handle status transitions
            if "status" in update_data and update_data["status"] != project.status:
                # Handle status change logic
                # For example, if changing to COMPLETED, set actual_end_date
                if update_data["status"] == ProjectStatus.COMPLETED and not project.actual_end_date:
                    update_data["actual_end_date"] = datetime.now()
            
            for key, value in update_data.items():
                setattr(project, key, value)
            
            await db.commit()
            await db.refresh(project)
            
            logger.info(f"Updated marketing project {project_id}: {project.name}")
            
            # Return the updated project with details
            return await ProjectController.get_project(project_id, db)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update project: {str(e)}"
            )
    
    @staticmethod
    async def delete_project(project_id: int, db: AsyncSession) -> None:
        """
        Delete a marketing project
        """
        try:
            # Get the project
            query = select(MarketingProject).filter(MarketingProject.id == project_id)
            result = await db.execute(query)
            project = result.scalars().first()
            
            if not project:
                logger.warning(f"Marketing project with ID {project_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Marketing project with ID {project_id} not found"
                )
            
            # Delete the project
            await db.delete(project)
            await db.commit()
            
            logger.info(f"Deleted marketing project {project_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete project: {str(e)}"
            )
    
    @staticmethod
    async def _calculate_task_stats(project_id: int, db: AsyncSession) -> Dict[str, int]:
        """Helper method to calculate task statistics for a project"""
        try:
            # Count tasks by status
            task_stats = {}
            
            # Query to count tasks by status
            for task_status in TaskStatus:
                query = select(func.count()).select_from(MarketingTask).filter(
                    MarketingTask.project_id == project_id,
                    MarketingTask.status == task_status
                )
                result = await db.execute(query)
                count = result.scalar()
                task_stats[task_status.name] = count
            
            # Add total count
            query = select(func.count()).select_from(MarketingTask).filter(
                MarketingTask.project_id == project_id
            )
            result = await db.execute(query)
            total = result.scalar()
            task_stats["TOTAL"] = total
            
            return task_stats
        except Exception as e:
            logger.error(f"Error calculating task stats for project {project_id}: {str(e)}")
            return {}
    
    @staticmethod
    async def _calculate_workflow_progress(project_id: int, db: AsyncSession) -> float:
        """Helper method to calculate workflow progress percentage for a project"""
        try:
            # Get all workflow steps for the project
            query = select(WorkflowStep).filter(WorkflowStep.project_id == project_id)
            result = await db.execute(query)
            steps = result.scalars().all()
            
            if not steps:
                return 0.0
            
            # Count completed steps
            completed = sum(1 for step in steps if step.status == "completed")
            total = len(steps)
            
            # Calculate progress percentage
            progress = (completed / total) * 100 if total > 0 else 0
            
            return progress
        except Exception as e:
            logger.error(f"Error calculating workflow progress for project {project_id}: {str(e)}")
            return 0.0
