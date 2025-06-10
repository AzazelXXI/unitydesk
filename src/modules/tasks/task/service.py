from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete, insert
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, datetime

from src.models.task import Task, TaskStatusEnum, TaskPriorityEnum
from src.models.project import Project
from src.models.user import User
from src.models.association_tables import (
    task_assignees,
    task_dependencies,
    project_members,
)
from .schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskAssignmentUpdate,
    TaskDependencyUpdate,
    TaskStatsResponse,
    UserSummary,
    ProjectSummary,
    TaskStatus,
    TaskPriority,
)
from .exceptions import (
    TaskNotFoundError,
    UnauthorizedTaskAccessError,
    TaskValidationError,
    CircularDependencyError,
    ProjectNotFoundError,
    TaskDependencyError,
    TaskAssignmentError,
)


class TaskService:

    @staticmethod
    async def create_task(
        task_data: TaskCreate, creator_id: int, db: AsyncSession
    ) -> TaskResponse:
        """Create a new task"""
        try:
            # Verify project exists and user has access
            project_result = await db.execute(
                select(Project).where(Project.id == task_data.project_id)
            )
            project = project_result.scalar_one_or_none()

            if not project:
                raise ProjectNotFoundError(task_data.project_id)

            # Check if user has access to project
            await TaskService._check_project_access(
                task_data.project_id, creator_id, db
            )

            # Convert schema to model
            task_dict = task_data.dict(exclude={"assignee_ids", "dependency_ids"})

            # Map enum values
            task_dict["status"] = TaskStatusEnum.NOT_STARTED
            task_dict["priority"] = TaskPriorityEnum(task_data.priority.value)

            # Create task
            task = Task(**task_dict)
            db.add(task)
            await db.flush()  # Get task ID

            # Add assignees
            if task_data.assignee_ids:
                await TaskService._assign_users_to_task(
                    task.id, task_data.assignee_ids, db
                )

            # Add dependencies
            if task_data.dependency_ids:
                await TaskService._add_task_dependencies(
                    task.id, task_data.dependency_ids, db
                )

            await db.commit()
            await db.refresh(task)

            return await TaskService._build_task_response(task, db)

        except Exception as e:
            await db.rollback()
            if isinstance(
                e, (ProjectNotFoundError, TaskValidationError, CircularDependencyError)
            ):
                raise
            raise TaskValidationError(f"Failed to create task: {str(e)}")

    @staticmethod
    async def get_task_by_id(
        task_id: int, user_id: int, db: AsyncSession
    ) -> TaskResponse:
        """Get task by ID with access control"""

        result = await db.execute(
            select(Task)
            .options(
                selectinload(Task.project),
                selectinload(Task.assignees),
                selectinload(Task.dependencies),
                selectinload(Task.dependent_tasks),
            )
            .where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise TaskNotFoundError(task_id)

        # Check access permission
        await TaskService._check_project_access(task.project_id, user_id, db)

        return await TaskService._build_task_response(task, db)

    @staticmethod
    async def get_tasks(
        user_id: int,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        due_date_from: Optional[date] = None,
        due_date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = None,
    ) -> List[TaskListResponse]:
        """Get tasks with filtering and access control"""

        # Build base query with joins
        query = select(Task).join(Project)

        # Apply project access filter
        project_access_filter = or_(
            Project.owner_id == user_id,
            Project.id.in_(
                select(project_members.c.project_id).where(
                    project_members.c.user_id == user_id
                )
            ),
        )
        query = query.where(project_access_filter)

        # Apply filters
        if project_id:
            query = query.where(Task.project_id == project_id)

        if status:
            query = query.where(Task.status == status)

        if priority:
            query = query.where(Task.priority == priority)

        if assignee_id:
            query = query.where(
                Task.id.in_(
                    select(task_assignees.c.task_id).where(
                        task_assignees.c.user_id == assignee_id
                    )
                )
            )

        if due_date_from:
            query = query.where(Task.due_date >= due_date_from)

        if due_date_to:
            query = query.where(Task.due_date <= due_date_to)

        # Add pagination
        query = query.offset(skip).limit(limit)
        query = query.order_by(Task.created_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()

        # Build response with project names and assignee counts
        task_responses = []
        for task in tasks:
            # Get project name
            project_result = await db.execute(
                select(Project.name).where(Project.id == task.project_id)
            )
            project_name = project_result.scalar_one_or_none()

            # Get assignee count
            assignee_count_result = await db.execute(
                select(func.count(task_assignees.c.user_id)).where(
                    task_assignees.c.task_id == task.id
                )
            )
            assignee_count = assignee_count_result.scalar() or 0

            task_response = TaskListResponse(
                id=task.id,
                name=task.name,
                status=TaskStatus(task.status.value),
                priority=TaskPriority(task.priority.value),
                due_date=task.due_date,
                project_id=task.project_id,
                project_name=project_name,
                assignee_count=assignee_count,
                estimated_hours=task.estimated_hours,
                actual_hours=task.actual_hours,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )
            task_responses.append(task_response)

        return task_responses

    @staticmethod
    async def update_task(
        task_id: int, task_data: TaskUpdate, user_id: int, db: AsyncSession
    ) -> TaskResponse:
        """Update task with access control"""

        # Get task and check access
        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()

        if not task:
            raise TaskNotFoundError(task_id)

        await TaskService._check_project_access(task.project_id, user_id, db)

        try:
            # Update fields
            update_data = task_data.dict(exclude_unset=True)

            for field, value in update_data.items():
                if field == "status" and value:
                    setattr(task, field, TaskStatusEnum(value))
                elif field == "priority" and value:
                    setattr(task, field, TaskPriorityEnum(value))
                else:
                    setattr(task, field, value)

            # Handle status-specific logic
            if task_data.status == "COMPLETED" and not task.completed_date:
                task.completed_date = datetime.utcnow()
            elif task_data.status and task_data.status != "COMPLETED":
                task.completed_date = None

            await db.commit()
            await db.refresh(task)

            return await TaskService._build_task_response(task, db)

        except Exception as e:
            await db.rollback()
            raise TaskValidationError(f"Failed to update task: {str(e)}")

    @staticmethod
    async def delete_task(task_id: int, user_id: int, db: AsyncSession):
        """Delete task with access control"""

        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()

        if not task:
            raise TaskNotFoundError(task_id)

        await TaskService._check_project_access(task.project_id, user_id, db)

        try:
            # Remove dependencies first
            await db.execute(
                delete(task_dependencies).where(
                    or_(
                        task_dependencies.c.task_id == task_id,
                        task_dependencies.c.depends_on_task_id == task_id,
                    )
                )
            )

            # Remove assignees
            await db.execute(
                delete(task_assignees).where(task_assignees.c.task_id == task_id)
            )

            # Delete task
            await db.delete(task)
            await db.commit()

        except Exception as e:
            await db.rollback()
            raise TaskValidationError(f"Failed to delete task: {str(e)}")

    @staticmethod
    async def update_task_assignments(
        task_id: int,
        assignment_data: TaskAssignmentUpdate,
        user_id: int,
        db: AsyncSession,
    ) -> TaskResponse:
        """Update task assignments"""

        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()

        if not task:
            raise TaskNotFoundError(task_id)

        await TaskService._check_project_access(task.project_id, user_id, db)

        try:
            # Remove existing assignments
            await db.execute(
                delete(task_assignees).where(task_assignees.c.task_id == task_id)
            )

            # Add new assignments
            if assignment_data.assignee_ids:
                await TaskService._assign_users_to_task(
                    task_id, assignment_data.assignee_ids, db
                )

            await db.commit()

            return await TaskService._build_task_response(task, db)

        except Exception as e:
            await db.rollback()
            raise TaskAssignmentError(f"Failed to update assignments: {str(e)}")

    @staticmethod
    async def update_task_dependencies(
        task_id: int,
        dependency_data: TaskDependencyUpdate,
        user_id: int,
        db: AsyncSession,
    ) -> TaskResponse:
        """Update task dependencies"""

        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()

        if not task:
            raise TaskNotFoundError(task_id)

        await TaskService._check_project_access(task.project_id, user_id, db)

        try:
            # Remove existing dependencies
            await db.execute(
                delete(task_dependencies).where(task_dependencies.c.task_id == task_id)
            )

            # Add new dependencies
            if dependency_data.dependency_ids:
                await TaskService._add_task_dependencies(
                    task_id, dependency_data.dependency_ids, db
                )

            await db.commit()

            return await TaskService._build_task_response(task, db)

        except Exception as e:
            await db.rollback()
            raise TaskDependencyError(f"Failed to update dependencies: {str(e)}")

    @staticmethod
    async def get_task_stats(
        user_id: int, project_id: Optional[int] = None, db: AsyncSession = None
    ) -> TaskStatsResponse:
        """Get task statistics for projects user has access to"""

        # Build base query with project access filter
        base_query = select(Task).join(Project)

        project_access_filter = or_(
            Project.owner_id == user_id,
            Project.id.in_(
                select(project_members.c.project_id).where(
                    project_members.c.user_id == user_id
                )
            ),
        )
        base_query = base_query.where(project_access_filter)

        if project_id:
            base_query = base_query.where(Task.project_id == project_id)

        # Get status counts
        status_results = await db.execute(
            select(Task.status, func.count(Task.id).label("count"))
            .select_from(Task)
            .join(Project)
            .where(project_access_filter)
            .where(Task.project_id == project_id if project_id else True)
            .group_by(Task.status)
        )

        status_counts = {row.status.value: row.count for row in status_results}

        # Get total counts
        total_result = await db.execute(
            select(func.count(Task.id))
            .select_from(Task)
            .join(Project)
            .where(project_access_filter)
            .where(Task.project_id == project_id if project_id else True)
        )
        total_tasks = total_result.scalar() or 0

        # Get overdue tasks
        overdue_result = await db.execute(
            select(func.count(Task.id))
            .select_from(Task)
            .join(Project)
            .where(project_access_filter)
            .where(Task.project_id == project_id if project_id else True)
            .where(Task.due_date < datetime.now())
            .where(Task.status != TaskStatusEnum.COMPLETED)
        )
        overdue_tasks = overdue_result.scalar() or 0

        # Get hours totals
        hours_result = await db.execute(
            select(
                func.sum(Task.estimated_hours).label("total_estimated"),
                func.sum(Task.actual_hours).label("total_actual"),
            )
            .select_from(Task)
            .join(Project)
            .where(project_access_filter)
            .where(Task.project_id == project_id if project_id else True)
        )
        hours_row = hours_result.first()

        return TaskStatsResponse(
            total_tasks=total_tasks,
            not_started=status_counts.get("Not Started", 0),
            in_progress=status_counts.get("In Progress", 0),
            completed=status_counts.get("Completed", 0),
            blocked=status_counts.get("Blocked", 0),
            cancelled=status_counts.get("Cancelled", 0),
            overdue_tasks=overdue_tasks,
            total_estimated_hours=hours_row.total_estimated if hours_row else None,
            total_actual_hours=hours_row.total_actual if hours_row else None,
        )

    # Helper methods
    @staticmethod
    async def _check_project_access(project_id: int, user_id: int, db: AsyncSession):
        """Check if user has access to project"""

        project_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()

        if not project:
            raise ProjectNotFoundError(project_id)

        # Check if user is project owner
        if project.owner_id == user_id:
            return True

        # Check if user is team member
        member_result = await db.execute(
            select(project_members).where(
                and_(
                    project_members.c.project_id == project_id,
                    project_members.c.user_id == user_id,
                )
            )
        )

        if not member_result.first():
            raise UnauthorizedTaskAccessError(f"No access to project {project_id}")

    @staticmethod
    async def _assign_users_to_task(
        task_id: int, user_ids: List[int], db: AsyncSession
    ):
        """Assign users to task"""

        # Verify users exist
        user_result = await db.execute(select(User.id).where(User.id.in_(user_ids)))
        existing_user_ids = [row.id for row in user_result]

        missing_users = set(user_ids) - set(existing_user_ids)
        if missing_users:
            raise TaskAssignmentError(f"Users not found: {missing_users}")

        # Insert assignments
        assignments = [{"task_id": task_id, "user_id": user_id} for user_id in user_ids]

        await db.execute(insert(task_assignees).values(assignments))

    @staticmethod
    async def _add_task_dependencies(
        task_id: int, dependency_ids: List[int], db: AsyncSession
    ):
        """Add task dependencies with circular dependency check"""

        for dep_id in dependency_ids:
            # Check if dependency task exists
            dep_result = await db.execute(select(Task.id).where(Task.id == dep_id))
            if not dep_result.scalar_one_or_none():
                raise TaskDependencyError(f"Dependency task {dep_id} not found")

            # Check for circular dependency
            if await TaskService._would_create_circular_dependency(task_id, dep_id, db):
                raise CircularDependencyError(task_id, dep_id)

        # Insert dependencies
        dependencies = [
            {"task_id": task_id, "depends_on_task_id": dep_id}
            for dep_id in dependency_ids
        ]

        await db.execute(insert(task_dependencies).values(dependencies))

    @staticmethod
    async def _would_create_circular_dependency(
        task_id: int, dependency_id: int, db: AsyncSession
    ) -> bool:
        """Check if adding dependency would create circular dependency"""

        # If dependency_id depends on task_id (directly or indirectly), it's circular
        visited = set()
        to_check = [dependency_id]

        while to_check:
            current = to_check.pop()
            if current == task_id:
                return True

            if current in visited:
                continue

            visited.add(current)

            # Get dependencies of current task
            deps_result = await db.execute(
                select(task_dependencies.c.depends_on_task_id).where(
                    task_dependencies.c.task_id == current
                )
            )

            to_check.extend([row.depends_on_task_id for row in deps_result])

        return False

    @staticmethod
    async def _build_task_response(task: Task, db: AsyncSession) -> TaskResponse:
        """Build complete task response with related data"""

        # Get project info
        project_result = await db.execute(
            select(Project.id, Project.name, Project.status).where(
                Project.id == task.project_id
            )
        )
        project_row = project_result.first()
        project_summary = (
            ProjectSummary(
                id=project_row.id,
                name=project_row.name,
                status=project_row.status.value,
            )
            if project_row
            else None
        )

        # Get assignees
        assignees_result = await db.execute(
            select(User.id, User.username, User.email, User.user_type)
            .join(task_assignees)
            .where(task_assignees.c.task_id == task.id)
        )
        assignees = [
            UserSummary(
                id=row.id,
                username=row.username,
                email=row.email,
                user_type=row.user_type,
            )
            for row in assignees_result
        ]

        # Get dependencies
        deps_result = await db.execute(
            select(task_dependencies.c.depends_on_task_id).where(
                task_dependencies.c.task_id == task.id
            )
        )
        dependencies = [row.depends_on_task_id for row in deps_result]

        # Get dependent tasks
        dependent_result = await db.execute(
            select(task_dependencies.c.task_id).where(
                task_dependencies.c.depends_on_task_id == task.id
            )
        )
        dependent_tasks = [row.task_id for row in dependent_result]

        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            status=TaskStatus(task.status.value),
            priority=TaskPriority(task.priority.value),
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            tags=task.tags,
            start_date=task.start_date,
            due_date=task.due_date,
            completed_date=task.completed_date,
            project_id=task.project_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            project=project_summary,
            assignees=assignees,
            dependencies=dependencies,
            dependent_tasks=dependent_tasks,
        )
