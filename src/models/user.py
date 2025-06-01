import enum
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from .base import Base


class UserStatusEnum(str, enum.Enum):
    ONLINE = "Online"
    OFFLINE = "Offline"
    IDLE = "Idle"


class UserTypeEnum(str, enum.Enum):
    PROJECT_MANAGER = "ProjectManager"
    TEAM_MEMBER = "TeamMember"
    CLIENT = "Client"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    status = Column(
        SAEnum(UserStatusEnum, name="user_status_enum", create_type=False),
        nullable=False,
        default=UserStatusEnum.OFFLINE,
    )
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    update_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    user_type = Column(
        SAEnum(UserTypeEnum, name="user_type_enum", create_type=False), nullable=False
    )

    __mapper_args = {
        # Value for superclass (if it does contain)
        "polymorphic_identity": "user",
        # Column use to determine subclass
        "polymorphic_on": user_type,
    }

    # Foreign Key
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Relationships
    # A user could create many Project
    created_project = relationship("Project", back_populates="creator", foreign_keys="Project.creator_id")
    # A user could be assigned many Task
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="[Task.assignee_id]")
    # A user could write many Comment
    comments = relationship("Comment", back_populates="author", foreign_keys="[Comment.user_id]")
    # A user could upload many attachment
    uploaded_attachments = relationship("Attachment", back_populates="uploader", foreign_keys="Attachment.user_id")
    


class ProjectManagerUser(User):
    __mapper_args__ = {"polymorphic_identity": UserTypeEnum.PROJECT_MANAGER}


class TeamMemberUser(User):
    __mapper_args__ = {"polymorphic_identity": UserTypeEnum.TEAM_MEMBER}


class ClientUser(User):
    __mapper_args__ = {"polymorphic_identity": UserTypeEnum.CLIENT}
