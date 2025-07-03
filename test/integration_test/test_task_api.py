import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.models.project import Project
from src.models.task import Task, TaskStatusEnum
from src.models.association_tables import project_members, task_assignees
from src.main import app


@pytest.mark.asyncio
async def test_update_task_status_success_owner(test_session: AsyncSession):
    """Owner can update task status"""
    # Create owner user
    owner = User(name="Owner", email="owner@example.com", password_hash="x")
    test_session.add(owner)
    await test_session.flush()

    # Create project
    project = Project(name="Test Project", description="desc", owner_id=owner.id)
    test_session.add(project)
    await test_session.flush()

    # Add owner as project member
    await test_session.execute(
        project_members.insert().values(project_id=project.id, user_id=owner.id)
    )

    # Create task
    task = Task(
        name="Task 1",
        description="desc",
        status=TaskStatusEnum.NOT_STARTED,
        project_id=project.id,
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)

    # Simulate login (mock dependency override)
    # Patch dependency override for authentication
    app.dependency_overrides.clear()

    async def override_get_current_user_web(*args, **kwargs):
        return owner

    # Use the actual import path for the dependency
    from src.middleware.auth_middleware import get_current_user_web

    app.dependency_overrides[get_current_user_web] = override_get_current_user_web

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(f"/api/tasks/{task.id}", json={"status": "IN_PROGRESS"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_update_task_status_permission_denied(test_session: AsyncSession):
    """Non-owner, non-assignee, non-admin cannot update status"""
    owner = User(name="Owner", email="owner2@example.com", password_hash="x")
    other = User(name="Other", email="other@example.com", password_hash="x")
    test_session.add_all([owner, other])
    await test_session.flush()
    project = Project(name="P2", description="desc", owner_id=owner.id)
    test_session.add(project)
    await test_session.flush()
    await test_session.execute(
        project_members.insert().values(project_id=project.id, user_id=owner.id)
    )
    task = Task(
        name="Task 2",
        description="desc",
        status=TaskStatusEnum.NOT_STARTED,
        project_id=project.id,
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)
    app.dependency_overrides.clear()

    async def override_get_current_user_web(*args, **kwargs):
        return other

    from src.middleware.auth_middleware import get_current_user_web

    app.dependency_overrides[get_current_user_web] = override_get_current_user_web
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(f"/api/tasks/{task.id}", json={"status": "COMPLETED"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_task_status_invalid_status(test_session: AsyncSession):
    """Invalid status value returns 422"""
    owner = User(name="Owner", email="owner3@example.com", password_hash="x")
    test_session.add(owner)
    await test_session.flush()
    project = Project(name="P3", description="desc", owner_id=owner.id)
    test_session.add(project)
    await test_session.flush()
    await test_session.execute(
        project_members.insert().values(project_id=project.id, user_id=owner.id)
    )
    task = Task(
        name="Task 3",
        description="desc",
        status=TaskStatusEnum.NOT_STARTED,
        project_id=project.id,
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)
    app.dependency_overrides.clear()

    async def override_get_current_user_web(*args, **kwargs):
        return owner

    from src.middleware.auth_middleware import get_current_user_web

    app.dependency_overrides[get_current_user_web] = override_get_current_user_web
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(f"/api/tasks/{task.id}", json={"status": "NotAStatus"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_task_status_not_found(test_session: AsyncSession):
    """Task not found returns 404"""
    owner = User(name="Owner", email="owner4@example.com", password_hash="x")
    test_session.add(owner)
    await test_session.flush()
    app.dependency_overrides.clear()

    async def override_get_current_user_web(*args, **kwargs):
        return owner

    from src.middleware.auth_middleware import get_current_user_web

    app.dependency_overrides[get_current_user_web] = override_get_current_user_web
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(f"/api/tasks/999999", json={"status": "COMPLETED"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_task_status_success_assignee(test_session: AsyncSession):
    """Assignee can update task status"""
    owner = User(name="Owner", email="owner5@example.com", password_hash="x")
    assignee = User(name="Assignee", email="assignee@example.com", password_hash="x")
    test_session.add_all([owner, assignee])
    await test_session.flush()
    project = Project(name="P4", description="desc", owner_id=owner.id)
    test_session.add(project)
    await test_session.flush()
    await test_session.execute(
        project_members.insert().values(project_id=project.id, user_id=owner.id)
    )
    task = Task(
        name="Task 4",
        description="desc",
        status=TaskStatusEnum.NOT_STARTED,
        project_id=project.id,
    )
    test_session.add(task)
    await test_session.flush()
    await test_session.execute(
        task_assignees.insert().values(task_id=task.id, user_id=assignee.id)
    )
    await test_session.commit()
    await test_session.refresh(task)
    app.dependency_overrides.clear()

    async def override_get_current_user_web(*args, **kwargs):
        return assignee

    from src.middleware.auth_middleware import get_current_user_web

    app.dependency_overrides[get_current_user_web] = override_get_current_user_web
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(f"/api/tasks/{task.id}", json={"status": "COMPLETED"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
