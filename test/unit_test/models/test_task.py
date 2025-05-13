import pytest
import enum
from datetime import datetime

# Import các model và các thành phần cần thiết từ code của bạn
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect, String, Text, Integer, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from src.database import Base # Giả định Base được định nghĩa ở đây
from src.models.base import RootModel

class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Project(Base, RootModel):
    """Project model for organizing related tasks"""
    __tablename__ = "projects"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id")) # Giả định bảng users có cột id kiểu Integer
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(100), default="active")
    color = Column(String(20), nullable=True) # Color code
    is_archived = Column(Boolean, default=False)
    
    # Relationships
    # owner = relationship("User", back_populates="projects_owned") # Cần import User model
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Task(Base, RootModel):
    """Task model for managing work items"""
    __tablename__ = "tasks"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    due_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    completion_percentage = Column(Integer, default=0)
    creator_id = Column(Integer, ForeignKey("users.id")) # Giả định bảng users có cột id kiểu Integer
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Relationships
    # creator = relationship("User", foreign_keys=[creator_id], back_populates="tasks_created") # Cần import User
    project = relationship("Project", back_populates="tasks")
    assignees = relationship("TaskAssignee", back_populates="task", cascade="all, delete-orphan")
    parent_task = relationship("Task", remote_side=[id], backref="subtasks") # Recursive relationship


class TaskAssignee(Base, RootModel):
    """Association between tasks and users (assignees)"""
    __tablename__ = "task_assignees"
    
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True) # Giả định là Primary Key composite
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True) # Giả định là Primary Key composite
    assigned_at = Column(DateTime, default=datetime.utcnow)
    is_responsible = Column(Boolean, default=False) # Main assignee responsible for the task
    
    # Relationships
    task = relationship("Task", back_populates="assignees")
    # user = relationship("User", back_populates="task_assignments") # Cần import User


class TaskComment(Base, RootModel):
    """Comments on tasks"""
    __tablename__ = "task_comments"
    
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True) # Giả định users.id là Integer
    content = Column(Text, nullable=False)
    
    # Relationships
    task = relationship("Task", backref="comments") # backref được định nghĩa ở đây
    # user = relationship("User") # Cần import User

# --- Hết phần Tái tạo Model (Chỉ để đảm bảo code test chạy được độc lập nếu cần) ---
# --- Trong file test thực tế, bạn chỉ cần dòng import các model ở trên cùng ---


# Giả định bạn có fixture này trong conftest.py hoặc tương tự
# @pytest.fixture
# async def test_session() -> AsyncSession:
#     """Provides an async database session for tests."""
#     # Logic to create and yield a session (e.g., connect to test DB, create tables)
#     pass # Thay thế bằng logic setup DB thực tế

# Giả định bạn có fixture này cung cấp dữ liệu mẫu đã được thêm vào session
# @pytest.fixture
# async def sample_data(test_session: AsyncSession):
#     """Provides sample data (users, projects, tasks, etc.) in the test session."""
#     # Logic to create and add sample model instances to test_session
#     # e.g., user1 = User(...); project1 = Project(owner=user1, ...); await test_session.commit()
#     # return {"users": {...}, "projects": {...}, "tasks": {...}, ...}
#     pass # Thay thế bằng logic tạo dữ liệu mẫu thực tế


# --- Các Test Cases ---

class TestTaskEnums:
    """Test TaskStatus and TaskPriority Enums"""

    def test_task_status_enum(self):
        assert TaskStatus.TODO.value == "todo"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.REVIEW.value == "review"
        assert TaskStatus.DONE.value == "done"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_task_priority_enum(self):
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.URGENT.value == "urgent"


class TestProjectModel:
    """Test Project model definition and basic properties"""

    @pytest.mark.model_definition
    def test_project_tablename(self):
        assert Project.__tablename__ == "projects"

    @pytest.mark.model_definition
    def test_project_columns(self):
        inspector = inspect(Project)
        columns = {col.name: col for col in inspector.columns}

        assert "id" in columns
        assert "name" in columns
        assert "description" in columns
        assert "owner_id" in columns
        assert "start_date" in columns
        assert "end_date" in columns
        assert "status" in columns
        assert "color" in columns
        assert "is_archived" in columns

        assert columns["name"].type.length == 255
        assert columns["name"].nullable is False
        assert isinstance(columns["description"].type, Text)
        assert columns["description"].nullable is True
        assert isinstance(columns["owner_id"].type, Integer)
        assert isinstance(columns["start_date"].type, DateTime)
        assert isinstance(columns["end_date"].type, DateTime)
        assert isinstance(columns["status"].type, String) # Status column is String(100)
        assert columns["status"].type.length == 100
        assert isinstance(columns["color"].type, String)
        assert columns["color"].type.length == 20
        assert isinstance(columns["is_archived"].type, Boolean)

    @pytest.mark.model_definition
    def test_project_constraints(self):
        table = Project.__table__
        assert table.primary_key is not None
        assert "id" in [col.name for col in table.primary_key]

        foreign_keys = [fk for col in table.columns for fk in col.foreign_keys]
        owner_fk = next((fk for fk in foreign_keys if fk.parent.name == "owner_id"), None)
        assert owner_fk is not None
        assert owner_fk.column.table.name == "users"
        assert owner_fk.column.name == "id"

    @pytest.mark.model_definition
    def test_project_defaults(self):
        project = Project(name="Test Project")
        assert project.status == "active"
        assert project.is_archived is False

    @pytest.mark.model_definition
    def test_project_relationship_attributes(self):
        assert hasattr(Project, "owner") # Assuming User model is imported and relationship defined
        assert hasattr(Project, "tasks")


class TestTaskModel:
    """Test Task model definition and basic properties"""

    @pytest.mark.model_definition
    def test_task_tablename(self):
        assert Task.__tablename__ == "tasks"

    @pytest.mark.model_definition
    def test_task_columns(self):
        inspector = inspect(Task)
        columns = {col.name: col for col in inspector.columns}

        assert "id" in columns
        assert "title" in columns
        assert "description" in columns
        assert "status" in columns
        assert "priority" in columns
        assert "due_date" in columns
        assert "start_date" in columns
        assert "estimated_hours" in columns
        assert "actual_hours" in columns
        assert "completion_percentage" in columns
        assert "creator_id" in columns
        assert "project_id" in columns
        assert "parent_task_id" in columns

        assert columns["title"].type.length == 255
        assert columns["title"].nullable is False
        assert isinstance(columns["description"].type, Text)
        assert columns["description"].nullable is True
        assert isinstance(columns["status"].type, Enum)
        assert columns["status"].type.enum == TaskStatus
        assert isinstance(columns["priority"].type, Enum)
        assert columns["priority"].type.enum == TaskPriority
        assert isinstance(columns["due_date"].type, DateTime)
        assert isinstance(columns["start_date"].type, DateTime)
        assert isinstance(columns["estimated_hours"].type, Integer)
        assert isinstance(columns["actual_hours"].type, Integer)
        assert isinstance(columns["completion_percentage"].type, Integer)
        assert isinstance(columns["creator_id"].type, Integer)
        assert columns["project_id"].nullable is True
        assert columns["parent_task_id"].nullable is True


    @pytest.mark.model_definition
    def test_task_constraints(self):
        table = Task.__table__
        assert table.primary_key is not None
        assert "id" in [col.name for col in table.primary_key]

        foreign_keys = [fk for col in table.columns for fk in col.foreign_keys]

        creator_fk = next((fk for fk in foreign_keys if fk.parent.name == "creator_id"), None)
        assert creator_fk is not None
        assert creator_fk.column.table.name == "users"
        assert creator_fk.column.name == "id"

        project_fk = next((fk for fk in foreign_keys if fk.parent.name == "project_id"), None)
        assert project_fk is not None
        assert project_fk.column.table.name == "projects"
        assert project_fk.column.name == "id"

        parent_task_fk = next((fk for fk in foreign_keys if fk.parent.name == "parent_task_id"), None)
        assert parent_task_fk is not None
        assert parent_task_fk.column.table.name == "tasks"
        assert parent_task_fk.column.name == "id"


    @pytest.mark.model_definition
    def test_task_defaults(self):
        task = Task(title="New Task")
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM
        assert task.completion_percentage == 0

    @pytest.mark.model_definition
    def test_task_relationship_attributes(self):
        assert hasattr(Task, "creator") # Assuming User imported & relationship defined
        assert hasattr(Task, "project")
        assert hasattr(Task, "assignees")
        assert hasattr(Task, "parent_task")
        assert hasattr(Task, "subtasks") # Check backref


class TestTaskAssigneeModel:
    """Test TaskAssignee model definition and basic properties"""

    @pytest.mark.model_definition
    def test_task_assignee_tablename(self):
        assert TaskAssignee.__tablename__ == "task_assignees"

    @pytest.mark.model_definition
    def test_task_assignee_columns(self):
        inspector = inspect(TaskAssignee)
        columns = {col.name: col for col in inspector.columns}

        assert "task_id" in columns
        assert "user_id" in columns
        assert "assigned_at" in columns
        assert "is_responsible" in columns

        assert isinstance(columns["task_id"].type, Integer)
        assert isinstance(columns["user_id"].type, Integer)
        assert isinstance(columns["assigned_at"].type, DateTime)
        assert isinstance(columns["is_responsible"].type, Boolean)

    @pytest.mark.model_definition
    def test_task_assignee_constraints(self):
        table = TaskAssignee.__table__

        # Check composite primary key
        assert table.primary_key is not None
        pk_column_names = {col.name for col in table.primary_key.columns}
        assert "task_id" in pk_column_names
        assert "user_id" in pk_column_names

        foreign_keys = [fk for col in table.columns for fk in col.foreign_keys]

        task_fk = next((fk for fk in foreign_keys if fk.parent.name == "task_id"), None)
        assert task_fk is not None
        assert task_fk.column.table.name == "tasks"
        assert task_fk.column.name == "id"
        assert "cascade" in str(task_fk.ondelete).lower() # Check ON DELETE CASCADE

        user_fk = next((fk for fk in foreign_keys if fk.parent.name == "user_id"), None)
        assert user_fk is not None
        assert user_fk.column.table.name == "users"
        assert user_fk.column.name == "id"
        assert "cascade" in str(user_fk.ondelete).lower() # Check ON DELETE CASCADE

    @pytest.mark.model_definition
    def test_task_assignee_defaults(self):
        # Need task_id and user_id to create an instance due to composite PK
        # In a real test, you might use dummy IDs or create parent objects first
        assignee = TaskAssignee(task_id=1, user_id=1)
        assert isinstance(assignee.assigned_at, datetime)
        # Check if assigned_at is close to now (handle small time differences)
        now = datetime.utcnow()
        assert abs((now - assignee.assigned_at).total_seconds()) < 5

        assert assignee.is_responsible is False

    @pytest.mark.model_definition
    def test_task_assignee_relationship_attributes(self):
        assert hasattr(TaskAssignee, "task")
        assert hasattr(TaskAssignee, "user") # Assuming User imported & relationship defined


class TestTaskCommentModel:
    """Test TaskComment model definition and basic properties"""

    @pytest.mark.model_definition
    def test_task_comment_tablename(self):
        assert TaskComment.__tablename__ == "task_comments"

    @pytest.mark.model_definition
    def test_task_comment_columns(self):
        inspector = inspect(TaskComment)
        columns = {col.name: col for col in inspector.columns}

        assert "id" in columns
        assert "task_id" in columns
        assert "user_id" in columns
        assert "content" in columns

        assert isinstance(columns["task_id"].type, Integer)
        assert isinstance(columns["user_id"].type, Integer)
        assert columns["user_id"].nullable is True # user_id is nullable
        assert isinstance(columns["content"].type, Text)
        assert columns["content"].nullable is False


    @pytest.mark.model_definition
    def test_task_comment_constraints(self):
        table = TaskComment.__table__
        assert table.primary_key is not None
        assert "id" in [col.name for col in table.primary_key]

        foreign_keys = [fk for col in table.columns for fk in col.foreign_keys]

        task_fk = next((fk for fk in foreign_keys if fk.parent.name == "task_id"), None)
        assert task_fk is not None
        assert task_fk.column.table.name == "tasks"
        assert task_fk.column.name == "id"
        assert "cascade" in str(task_fk.ondelete).lower() # Check ON DELETE CASCADE

        user_fk = next((fk for fk in foreign_keys if fk.parent.name == "user_id"), None)
        assert user_fk is not None
        assert user_fk.column.table.name == "users"
        assert user_fk.column.name == "id"
        assert "set null" in str(user_fk.ondelete).lower() # Check ON DELETE SET NULL

    @pytest.mark.model_definition
    def test_task_comment_relationship_attributes(self):
        assert hasattr(TaskComment, "task") # Checked via backref
        assert hasattr(TaskComment, "user") # Assuming User imported & relationship defined


# --- Tests kiểm tra Mối quan hệ với dữ liệu mẫu (Cần fixture test_session và sample_data) ---

# Giả định sample_data fixture cung cấp:
# sample_data = {
#     "users": {"user1": User_instance, "user2": User_instance, ...},
#     "projects": {"project1": Project_instance, ...},
#     "tasks": {"task1": Task_instance, "subtask1": Task_instance, ...},
#     "assignees": {"assignee1": TaskAssignee_instance, ...},
#     "comments": {"comment1": TaskComment_instance, ...},
# }
# và các mối quan hệ đã được thiết lập khi tạo dữ liệu mẫu.

@pytest.mark.asyncio
@pytest.mark.relationship
@pytest.mark.parametrize("project_key, expected_task_keys", [
    ("project1", ["task1", "task2"]), # Giả định project1 có task1 và task2
    ("project2", []), # Giả định project2 không có task nào
])
async def test_project_tasks_relationship(test_session: AsyncSession, sample_data, project_key, expected_task_keys):
    """Test Project -> Tasks relationship"""
    project = sample_data["projects"][project_key]
    
    # Load project with tasks relationship
    project_with_tasks = await test_session.get(Project, project.id)
    
    # Check if the tasks relationship attribute exists and contains expected tasks
    assert hasattr(project_with_tasks, 'tasks')
    loaded_task_ids = {task.id for task in project_with_tasks.tasks}
    expected_task_ids = {sample_data["tasks"][key].id for key in expected_task_keys}
    
    assert loaded_task_ids == expected_task_ids

@pytest.mark.asyncio
@pytest.mark.relationship
@pytest.mark.parametrize("task_key, expected_assignee_user_keys", [
    ("task1", ["user1", "user2"]), # Giả định task1 được gán cho user1 và user2
    ("task2", ["user3"]), # Giả định task2 được gán cho user3
    ("task3", []), # Giả định task3 chưa được gán
])
async def test_task_assignees_relationship(test_session: AsyncSession, sample_data, task_key, expected_assignee_user_keys):
    """Test Task -> TaskAssignee -> User relationship"""
    task = sample_data["tasks"][task_key]

    # Load task with assignees relationship
    task_with_assignees = await test_session.get(Task, task.id)
    
    # Check if the assignees relationship attribute exists and contains expected assignees
    assert hasattr(task_with_assignees, 'assignees')
    loaded_assignee_user_ids = {assignee.user_id for assignee in task_with_assignees.assignees}
    expected_assignee_user_ids = {sample_data["users"][key].id for key in expected_assignee_user_keys}
    
    assert loaded_assignee_user_ids == expected_assignee_user_ids

    # You could also check properties on TaskAssignee instances themselves here


@pytest.mark.asyncio
@pytest.mark.relationship
@pytest.mark.parametrize("task_key, expected_comment_user_keys", [
    ("task1", ["user1", "user3"]), # Giả định task1 có comment từ user1 và user3
    ("task2", []), # Giả định task2 không có comment nào
])
async def test_task_comments_relationship(test_session: AsyncSession, sample_data, task_key, expected_comment_user_keys):
    """Test Task -> TaskComment -> User relationship (via backref)"""
    task = sample_data["tasks"][task_key]
    
    # Load task with comments relationship
    task_with_comments = await test_session.get(Task, task.id)
    
    # Check if the comments backref relationship attribute exists and contains expected comments
    assert hasattr(task_with_comments, 'comments')
    loaded_comment_user_ids = {comment.user_id for comment in task_with_comments.comments}
    expected_comment_user_ids = {sample_data["users"][key].id for key in expected_comment_user_keys}
    
    assert loaded_comment_user_ids == expected_comment_user_ids


@pytest.mark.asyncio
@pytest.mark.relationship
@pytest.mark.hierarchy
@pytest.mark.parametrize("child_task_key, parent_task_key, expected_subtask_keys_for_parent", [
    ("subtask1_of_task1", "task1", ["subtask1_of_task1", "subtask2_of_task1"]), # subtask1 & subtask2 là con của task1
    ("task2", None, []), # task2 không có parent
])
async def test_task_recursive_relationship(test_session: AsyncSession, sample_data, child_task_key, parent_task_key, expected_subtask_keys_for_parent):
    """Test Task recursive relationship (parent_task and subtasks)"""
    child_task = sample_data["tasks"][child_task_key]
    
    # Test child -> parent link
    if parent_task_key:
        parent_task_expected = sample_data["tasks"][parent_task_key]
        # Load child task to access parent relationship
        child_task_loaded = await test_session.get(Task, child_task.id)
        assert hasattr(child_task_loaded, 'parent_task')
        assert child_task_loaded.parent_task_id == parent_task_expected.id
        # Check the parent object itself (if loaded)
        # assert child_task_loaded.parent_task.id == parent_task_expected.id # Requires parent_task to be loaded

    else:
        # Load child task to access parent relationship
        child_task_loaded = await test_session.get(Task, child_task.id)
        assert child_task_loaded.parent_task_id is None
        assert child_task_loaded.parent_task is None

    # Test parent -> subtasks link (only if parent_task_key is provided, or test top-level task's subtasks)
    if parent_task_key:
        parent_task_actual = sample_data["tasks"][parent_task_key]
        # Load parent task to access subtasks backref
        parent_task_loaded = await test_session.get(Task, parent_task_actual.id)
        assert hasattr(parent_task_loaded, 'subtasks')
        loaded_subtask_ids = {subtask.id for subtask in parent_task_loaded.subtasks}
        expected_subtask_ids = {sample_data["tasks"][key].id for key in expected_subtask_keys_for_parent}
        assert loaded_subtask_ids == expected_subtask_ids
    # Note: This test structure assumes that expected_subtask_keys_for_parent lists ALL subtasks
    # for the given parent_task_key in that test scenario.