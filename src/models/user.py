import enum
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, Text
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
    __table__ = "users"

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
    update_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user_type = Column(
        SAEnum(UserTypeEnum, name="user_type_name", create_type=False), nullable=False
    )

    # ProjectManager Specific
    department = Column(String(255), nullable=True)

    __mapper_args = {
        # Value for superclass, can skip if User is always one of three
        "polymorphic_identity": "user",
        "polymorphic_on": user_type,
    }

    # Relationships: will define later when other models created

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, email={self.email}, type={self.user_type.value})>"


class ProjectManagerUser(User):
    __mapper_args__ = {"polymorphic_identity": UserTypeEnum.PROJECT_MANAGER}

class TeamMemberUser(User):
    __mapper_args__ = {"polymorphic_identity": UserTypeEnum.TEAM_MEMBER}

class ClientUser(User):
    __mapper_args__ = {"polymorphic_identity": UserTypeEnum.CLIENT}
