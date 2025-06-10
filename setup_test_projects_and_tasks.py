#!/usr/bin/env python3
"""
Setup script for creating test projects and tasks in the database.
This script will populate the database with sample data for development.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from asyncio import current_task

from src.database import engine
from src.models.user import User
from src.models.project import Project, ProjectStatusEnum
from src.models.task import Task, TaskStatusEnum, TaskPriorityEnum

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_test_projects_and_tasks():
    """Create test projects and tasks with the existing test users"""

    # Create session using the same pattern as conftest.py
    session_maker = sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )
    Session = async_scoped_session(session_maker, scopefunc=current_task)

    async with Session() as session:
        try:
            # Get existing test users
            users_result = await session.execute(select(User))
            users = users_result.scalars().all()

            if not users:
                logger.error(
                    "No users found in database. Please run setup_test_users.py first."
                )
                return

            logger.info(f"Found {len(users)} users in database")

            # Create test projects
            projects_data = [
                {
                    "name": "Website Redesign",
                    "description": "Complete redesign of company website with modern UI/UX",
                    "status": ProjectStatusEnum.IN_PROGRESS,
                    "progress": 35,
                    "budget": 50000.00,
                    "start_date": datetime.now() - timedelta(days=30),
                    "end_date": datetime.now() + timedelta(days=60),
                    "owner_id": users[0].id,
                },
                {
                    "name": "Mobile App Development",
                    "description": "Native mobile app for iOS and Android platforms",
                    "status": ProjectStatusEnum.IN_PROGRESS,
                    "progress": 60,
                    "budget": 80000.00,
                    "start_date": datetime.now() - timedelta(days=45),
                    "end_date": datetime.now() + timedelta(days=90),
                    "owner_id": users[1].id if len(users) > 1 else users[0].id,
                },
                {
                    "name": "Marketing Campaign",
                    "description": "Q2 digital marketing campaign across all channels",
                    "status": ProjectStatusEnum.PLANNING,
                    "progress": 15,
                    "budget": 25000.00,
                    "start_date": datetime.now() + timedelta(days=15),
                    "end_date": datetime.now() + timedelta(days=105),
                    "owner_id": users[2].id if len(users) > 2 else users[0].id,
                },
                {
                    "name": "Data Analytics Platform",
                    "description": "Business intelligence dashboard for data-driven insights",
                    "status": ProjectStatusEnum.IN_PROGRESS,
                    "progress": 75,
                    "budget": 120000.00,
                    "start_date": datetime.now() - timedelta(days=90),
                    "end_date": datetime.now() + timedelta(days=30),
                    "owner_id": users[0].id,
                },
            ]

            projects = []
            for project_data in projects_data:
                # Check if project already exists
                existing_project = await session.execute(
                    select(Project).where(Project.name == project_data["name"])
                )
                if existing_project.scalars().first():
                    logger.info(
                        f"Project '{project_data['name']}' already exists, skipping..."
                    )
                    continue

                project = Project(**project_data)
                session.add(project)
                projects.append(project)
                logger.info(f"Created project: {project.name}")

            # Flush to get project IDs
            await session.flush()

            # Create test tasks for each project (without creator_id)
            task_templates = [
                # Website Redesign tasks
                [
                    {
                        "name": "Design homepage mockup",
                        "description": "Create wireframes and mockups for the new homepage design",
                        "status": TaskStatusEnum.COMPLETED,
                        "priority": TaskPriorityEnum.HIGH,
                        "estimated_hours": 16,
                        "actual_hours": 18,
                        "due_date": datetime.now() - timedelta(days=5),
                        "completed_date": datetime.now() - timedelta(days=3),
                    },
                    {
                        "name": "Implement responsive navigation",
                        "description": "Code the responsive navigation menu with mobile support",
                        "status": TaskStatusEnum.IN_PROGRESS,
                        "priority": TaskPriorityEnum.HIGH,
                        "estimated_hours": 12,
                        "actual_hours": 8,
                        "due_date": datetime.now() + timedelta(days=3),
                        "start_date": datetime.now() - timedelta(days=2),
                    },
                    {
                        "name": "Content migration",
                        "description": "Migrate existing content to new CMS structure",
                        "status": TaskStatusEnum.NOT_STARTED,
                        "priority": TaskPriorityEnum.MEDIUM,
                        "estimated_hours": 24,
                        "due_date": datetime.now() + timedelta(days=10),
                    },
                    {
                        "name": "Performance optimization",
                        "description": "Optimize page load times and implement caching",
                        "status": TaskStatusEnum.NOT_STARTED,
                        "priority": TaskPriorityEnum.MEDIUM,
                        "estimated_hours": 20,
                        "due_date": datetime.now() + timedelta(days=15),
                    },
                ],
                # Mobile App Development tasks
                [
                    {
                        "name": "User authentication flow",
                        "description": "Implement login, signup, and password reset functionality",
                        "status": TaskStatusEnum.COMPLETED,
                        "priority": TaskPriorityEnum.HIGH,
                        "estimated_hours": 20,
                        "actual_hours": 22,
                        "due_date": datetime.now() - timedelta(days=10),
                        "completed_date": datetime.now() - timedelta(days=8),
                    },
                    {
                        "name": "Core app navigation",
                        "description": "Build main navigation structure and tab system",
                        "status": TaskStatusEnum.IN_PROGRESS,
                        "priority": TaskPriorityEnum.HIGH,
                        "estimated_hours": 16,
                        "actual_hours": 12,
                        "due_date": datetime.now() + timedelta(days=5),
                        "start_date": datetime.now() - timedelta(days=3),
                    },
                    {
                        "name": "Push notifications setup",
                        "description": "Configure push notification service and handling",
                        "status": TaskStatusEnum.IN_PROGRESS,
                        "priority": TaskPriorityEnum.MEDIUM,
                        "estimated_hours": 14,
                        "actual_hours": 6,
                        "due_date": datetime.now() + timedelta(days=8),
                        "start_date": datetime.now() - timedelta(days=1),
                    },
                    {
                        "name": "App store submission",
                        "description": "Prepare and submit app to iOS and Android stores",
                        "status": TaskStatusEnum.NOT_STARTED,
                        "priority": TaskPriorityEnum.LOW,
                        "estimated_hours": 8,
                        "due_date": datetime.now() + timedelta(days=25),
                    },
                ],
                # Marketing Campaign tasks
                [
                    {
                        "name": "Market research analysis",
                        "description": "Analyze target audience and competitor strategies",
                        "status": TaskStatusEnum.IN_PROGRESS,
                        "priority": TaskPriorityEnum.HIGH,
                        "estimated_hours": 12,
                        "actual_hours": 4,
                        "due_date": datetime.now() + timedelta(days=7),
                        "start_date": datetime.now() - timedelta(days=2),
                    },
                    {
                        "name": "Creative asset development",
                        "description": "Design banners, ads, and promotional materials",
                        "status": TaskStatusEnum.NOT_STARTED,
                        "priority": TaskPriorityEnum.HIGH,
                        "estimated_hours": 32,
                        "due_date": datetime.now() + timedelta(days=14),
                    },
                    {
                        "name": "Social media strategy",
                        "description": "Plan social media content calendar and posting strategy",
                        "status": TaskStatusEnum.NOT_STARTED,
                        "priority": TaskPriorityEnum.MEDIUM,
                        "estimated_hours": 16,
                        "due_date": datetime.now() + timedelta(days=12),
                    },
                ],
                # Data Analytics Platform tasks
                [
                    {
                        "name": "Database optimization",
                        "description": "Optimize queries and improve database performance",
                        "status": TaskStatusEnum.COMPLETED,
                        "priority": TaskPriorityEnum.HIGH,
                        "estimated_hours": 24,
                        "actual_hours": 28,
                        "due_date": datetime.now() - timedelta(days=15),
                        "completed_date": datetime.now() - timedelta(days=12),
                    },
                    {
                        "name": "Real-time dashboard",
                        "description": "Build real-time data visualization dashboard",
                        "status": TaskStatusEnum.IN_PROGRESS,
                        "priority": TaskPriorityEnum.HIGH,
                        "estimated_hours": 40,
                        "actual_hours": 32,
                        "due_date": datetime.now() + timedelta(days=10),
                        "start_date": datetime.now() - timedelta(days=8),
                    },
                    {
                        "name": "User access controls",
                        "description": "Implement role-based access control for dashboard",
                        "status": TaskStatusEnum.NOT_STARTED,
                        "priority": TaskPriorityEnum.MEDIUM,
                        "estimated_hours": 18,
                        "due_date": datetime.now() + timedelta(days=20),
                    },
                ],
            ]

            # Create tasks for each project (only using valid Task model fields)
            for i, project in enumerate(projects):
                if i < len(task_templates):
                    for task_template in task_templates[i]:
                        # Create task data with only valid fields
                        task_data = {
                            "name": task_template["name"],
                            "description": task_template.get("description"),
                            "status": task_template.get(
                                "status", TaskStatusEnum.NOT_STARTED
                            ),
                            "priority": task_template.get(
                                "priority", TaskPriorityEnum.MEDIUM
                            ),
                            "project_id": project.id,
                        }

                        # Add optional fields if they exist in the template
                        optional_fields = [
                            "estimated_hours",
                            "actual_hours",
                            "start_date",
                            "due_date",
                            "completed_date",
                            "tags",
                        ]
                        for field in optional_fields:
                            if field in task_template:
                                task_data[field] = task_template[field]

                        task = Task(**task_data)
                        session.add(task)
                        logger.info(
                            f"Created task: {task.name} for project {project.name}"
                        )

            # Commit all changes
            await session.commit()
            logger.info("Successfully created test projects and tasks!")

            # Print summary
            projects_result = await session.execute(select(Project))
            all_projects = projects_result.scalars().all()

            tasks_result = await session.execute(select(Task))
            all_tasks = tasks_result.scalars().all()

            logger.info(f"Database now contains:")
            logger.info(f"  - {len(all_projects)} projects")
            logger.info(f"  - {len(all_tasks)} tasks")
            logger.info(f"  - {len(users)} users")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating test data: {e}")
            raise
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(create_test_projects_and_tasks())
