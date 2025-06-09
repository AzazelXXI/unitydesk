"""
Task service layer for business logic and database operations.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, case, select
from sqlalchemy.exc import IntegrityError

from src.models.task import Task
from src.models.user import User
from src.models.project import Project
from src.models.association_tables import task_assignees, task_dependencies
from .schemas import TaskCreate, TaskUpdate, TaskQueryParams, TaskStatsResponse


class TaskService:
    """Service class for task-related business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task_data: TaskCreate, created_by_id: int) -> Task:
        """Create a new task."""
        # Validate project exists and user has access
        project_result = await self.db.execute(
            select(Project).filter(Project.id == task_data.project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        # Create task instance
        task_dict = task_data.model_dump(exclude={"assignee_ids", "dependency_ids"})
        task = Task(
            **task_dict,
            created_by_id=created_by_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(task)
        await self.db.flush()  # Get the task ID

        # Add assignees if provided
        if task_data.assignee_ids:
            await self._assign_users_to_task(task.id, task_data.assignee_ids)

        # Add dependencies if provided
        if task_data.dependency_ids:
            await self._add_task_dependencies(task.id, task_data.dependency_ids)

        await self.db.commit()
        await self.db.refresh(task)

        return await self._load_task_with_relations(task.id)

    async def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get a task by ID with all related data."""
        return await self._load_task_with_relations(task_id)

    async def update_task(
        self, task_id: int, task_data: TaskUpdate, updated_by_id: int
    ) -> Optional[Task]:
        """Update an existing task."""
        task_result = await self.db.execute(select(Task).filter(Task.id == task_id))
        task = task_result.scalar_one_or_none()
        if not task:
            return None

        # Update basic fields
        update_dict = task_data.model_dump(
            exclude_unset=True, exclude={"assignee_ids", "dependency_ids"}
        )
        update_dict["updated_at"] = datetime.utcnow()

        for field, value in update_dict.items():
            setattr(task, field, value)

        # Update assignees if provided
        if task_data.assignee_ids is not None:
            await self._update_task_assignees(task.id, task_data.assignee_ids)
        # Update dependencies if provided
        if task_data.dependency_ids is not None:
            await self._update_task_dependencies(task.id, task_data.dependency_ids)

        await self.db.commit()
        return await self._load_task_with_relations(task.id)

    async def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        task_result = await self.db.execute(select(Task).filter(Task.id == task_id))
        task = task_result.scalar_one_or_none()
        if not task:
            return False
        # Remove associations first
        await self.db.execute(
            task_assignees.delete().where(task_assignees.c.task_id == task_id)
        )
        await self.db.execute(
            task_dependencies.delete().where(
                or_(
                    task_dependencies.c.task_id == task_id,
                    task_dependencies.c.depends_on_id == task_id,
                )
            )
        )
        await self.db.delete(task)
        await self.db.commit()
        return True

    async def get_tasks(self, params: TaskQueryParams) -> Tuple[List[Task], int]:
        """Get tasks with filtering, pagination, and sorting."""
        query = select(Task)

        # Apply filters
        if params.project_id:
            query = query.filter(Task.project_id == params.project_id)

        if params.status:
            query = query.filter(Task.status == params.status.value)

        if params.priority:
            query = query.filter(Task.priority == params.priority.value)

        if params.created_by_id:
            query = query.filter(Task.created_by_id == params.created_by_id)

        if params.assignee_id:
            query = query.join(task_assignees).filter(
                task_assignees.c.user_id == params.assignee_id
            )

        if params.search:
            search_term = f"%{params.search}%"
            query = query.filter(
                or_(Task.title.ilike(search_term), Task.description.ilike(search_term))
            )

        if params.tags:
            tag_terms = [tag.strip() for tag in params.tags.split(",")]
            for tag in tag_terms:
                query = query.filter(Task.tags.ilike(f"%{tag}%"))

        if params.due_date_from:
            query = query.filter(Task.due_date >= params.due_date_from)

        if params.due_date_to:
            query = query.filter(Task.due_date <= params.due_date_to)

        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(Task, params.sort_by, Task.created_at)
        if params.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)

        # Execute query
        result = await self.db.execute(query)
        tasks = result.scalars().all()

        # Load relations for each task
        task_ids = [task.id for task in tasks]
        if task_ids:
            # Load tasks with relations
            tasks_with_relations_query = (
                select(Task)
                .options(
                    selectinload(Task.project),
                    selectinload(Task.created_by),
                    selectinload(Task.assignees),
                    selectinload(Task.dependencies),
                    selectinload(Task.dependents),
                )
                .filter(Task.id.in_(task_ids))
            )

            tasks_result = await self.db.execute(tasks_with_relations_query)
            tasks_with_relations = tasks_result.scalars().all()

            # Maintain order
            task_dict = {task.id: task for task in tasks_with_relations}
            tasks = [task_dict[task.id] for task in tasks if task.id in task_dict]

        return tasks, total

    async def get_task_statistics(
        self, project_id: Optional[int] = None, user_id: Optional[int] = None
    ) -> TaskStatsResponse:
        """Get task statistics."""
        query = select(Task)

        if project_id:
            query = query.filter(Task.project_id == project_id)

        if user_id:
            query = query.join(task_assignees).filter(
                task_assignees.c.user_id == user_id
            )

        # Basic counts
        total_count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(total_count_query)
        total_tasks = total_result.scalar()

        # Status counts
        status_query = query.with_only_columns(
            Task.status, func.count(Task.id).label("count")
        ).group_by(Task.status)

        status_result = await self.db.execute(status_query)
        status_counts = status_result.all()
        status_dict = {status: count for status, count in status_counts}

        # Priority counts
        priority_query = query.with_only_columns(
            Task.priority, func.count(Task.id).label("count")
        ).group_by(Task.priority)

        priority_result = await self.db.execute(priority_query)
        priority_counts = priority_result.all()
        priority_dict = {priority: count for priority, count in priority_counts}

        # Overdue tasks
        overdue_query = query.filter(
            and_(
                Task.due_date < datetime.utcnow(),
                Task.status.notin_(["completed", "cancelled"]),
            )
        )
        overdue_count_query = select(func.count()).select_from(overdue_query.subquery())
        overdue_result = await self.db.execute(overdue_count_query)
        overdue_count = overdue_result.scalar()

        # Average completion time for completed tasks
        avg_query = (
            query.filter(Task.status == "completed")
            .filter(Task.actual_hours.isnot(None))
            .with_only_columns(func.avg(Task.actual_hours))
        )
        avg_result = await self.db.execute(avg_query)
        avg_completion = avg_result.scalar()

        return TaskStatsResponse(
            total_tasks=total_tasks,
            todo_tasks=status_dict.get("todo", 0),
            in_progress_tasks=status_dict.get("in_progress", 0),
            under_review_tasks=status_dict.get("under_review", 0),
            completed_tasks=status_dict.get("completed", 0),
            cancelled_tasks=status_dict.get("cancelled", 0),
            overdue_tasks=overdue_count,
            tasks_by_priority=priority_dict,
            avg_completion_time=float(avg_completion) if avg_completion else None,
        )

    async def get_user_tasks(
        self, user_id: int, params: TaskQueryParams
    ) -> Tuple[List[Task], int]:
        """Get tasks assigned to a specific user."""
        # Add assignee filter to existing params
        params.assignee_id = user_id
        return await self.get_tasks(params)

    async def get_project_tasks(
        self, project_id: int, params: TaskQueryParams
    ) -> Tuple[List[Task], int]:
        """Get tasks for a specific project."""
        # Add project filter to existing params
        params.project_id = project_id
        return await self.get_tasks(params)

    async def assign_task(self, task_id: int, user_ids: List[int]) -> Optional[Task]:
        """Assign users to a task."""
        task_result = await self.db.execute(select(Task).filter(Task.id == task_id))
        task = task_result.scalar_one_or_none()
        if not task:
            return None

        await self._assign_users_to_task(task_id, user_ids)
        await self.db.commit()
        return await self._load_task_with_relations(task_id)

    async def unassign_task(self, task_id: int, user_ids: List[int]) -> Optional[Task]:
        """Unassign users from a task."""
        task_result = await self.db.execute(select(Task).filter(Task.id == task_id))
        task = task_result.scalar_one_or_none()
        if not task:
            return None

        await self.db.execute(
            task_assignees.delete().where(
                and_(
                    task_assignees.c.task_id == task_id,
                    task_assignees.c.user_id.in_(user_ids),
                )
            )
        )
        await self.db.commit()
        return await self._load_task_with_relations(task_id)

    async def add_task_dependency(self, task_id: int, depends_on_id: int) -> bool:
        """Add a dependency between tasks."""
        # Check if tasks exist
        task_result = await self.db.execute(select(Task).filter(Task.id == task_id))
        task = task_result.scalar_one_or_none()

        depends_on_result = await self.db.execute(
            select(Task).filter(Task.id == depends_on_id)
        )
        depends_on_task = depends_on_result.scalar_one_or_none()

        if not task or not depends_on_task:
            return False

        # Check for circular dependencies
        if await self._would_create_circular_dependency(task_id, depends_on_id):
            raise ValueError(
                "Adding this dependency would create a circular dependency"
            )

        try:
            await self.db.execute(
                task_dependencies.insert().values(
                    task_id=task_id, depends_on_id=depends_on_id
                )
            )
            await self.db.commit()
            return True
        except IntegrityError:
            await self.db.rollback()
            return False  # Dependency already exists

    async def remove_task_dependency(self, task_id: int, depends_on_id: int) -> bool:
        """Remove a dependency between tasks."""
        result = await self.db.execute(
            task_dependencies.delete().where(
                and_(
                    task_dependencies.c.task_id == task_id,
                    task_dependencies.c.depends_on_id == depends_on_id,
                )
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    # Private helper methods
    async def _load_task_with_relations(self, task_id: int) -> Optional[Task]:
        """Load task with all related data."""
        query = (
            select(Task)
            .options(
                selectinload(Task.project),
                selectinload(Task.created_by),
                selectinload(Task.assignees),
                selectinload(Task.dependencies),
                selectinload(Task.dependents),
            )
            .filter(Task.id == task_id)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _assign_users_to_task(self, task_id: int, user_ids: List[int]):
        """Assign users to a task."""
        # Validate users exist
        existing_users_query = select(User.id).filter(User.id.in_(user_ids))
        existing_users_result = await self.db.execute(existing_users_query)
        existing_users = existing_users_result.all()
        existing_user_ids = [user.id for user in existing_users]

        for user_id in existing_user_ids:
            try:
                await self.db.execute(
                    task_assignees.insert().values(task_id=task_id, user_id=user_id)
                )
            except IntegrityError:
                await self.db.rollback()
                # Assignment already exists, continue
                pass

    async def _update_task_assignees(self, task_id: int, user_ids: List[int]):
        """Update task assignees by replacing existing ones."""
        # Remove existing assignees
        await self.db.execute(
            task_assignees.delete().where(task_assignees.c.task_id == task_id)
        )

        # Add new assignees
        if user_ids:
            await self._assign_users_to_task(task_id, user_ids)

    async def _add_task_dependencies(self, task_id: int, dependency_ids: List[int]):
        """Add dependencies to a task."""
        for depends_on_id in dependency_ids:
            try:
                if not await self._would_create_circular_dependency(
                    task_id, depends_on_id
                ):
                    await self.db.execute(
                        task_dependencies.insert().values(
                            task_id=task_id, depends_on_id=depends_on_id
                        )
                    )
            except IntegrityError:
                await self.db.rollback()
                # Dependency already exists, continue
                pass

    async def _update_task_dependencies(self, task_id: int, dependency_ids: List[int]):
        """Update task dependencies by replacing existing ones."""
        # Remove existing dependencies
        await self.db.execute(
            task_dependencies.delete().where(task_dependencies.c.task_id == task_id)
        )

        # Add new dependencies
        if dependency_ids:
            await self._add_task_dependencies(task_id, dependency_ids)

    async def _would_create_circular_dependency(
        self, task_id: int, depends_on_id: int
    ) -> bool:
        """Check if adding a dependency would create a circular dependency."""
        if task_id == depends_on_id:
            return True

        # Get all tasks that depend on task_id (directly or indirectly)
        visited = set()
        stack = [task_id]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            # If we find depends_on_id in the chain, it would create a circle
            if current == depends_on_id:
                return True

            # Get tasks that depend on current task
            dependents_query = select(task_dependencies.c.task_id).filter(
                task_dependencies.c.depends_on_id == current
            )
            dependents_result = await self.db.execute(dependents_query)
            dependents = dependents_result.all()

            for (dependent_id,) in dependents:
                if dependent_id not in visited:
                    stack.append(dependent_id)

        return False
