import enum
import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Text, UUID
from sqlalchemy.orm import relationship
from .association_tables import (
    project_teams_table,
)  # Không cần import team_members_table nữa

# Import TeamMemberAssociation nếu bạn muốn dùng secondary=TeamMemberAssociation.__table__
# nhưng dùng tên bảng dạng string "team_members" thì không cần.
# from .user import TeamMemberAssociation

from .base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    # A User could create many team
    team_creator = relationship(
        "User", back_populates="created_teams"
    )  # Người tạo team

    # Many Team has many project
    projects = relationship(
        "Project", secondary=project_teams_table, back_populates="teams"
    )

    # Mối quan hệ thành viên trong team
    member_details = relationship(
        "TeamMemberAssociation", back_populates="team", cascade="all, delete-orphan"
    )
    members = relationship(
        "User",
        secondary="team_members",  # Thay đổi ở đây
        back_populates="member_of_teams",
        viewonly=True,  # Để tránh xung đột khi quản lý qua TeamMemberAssociation
    )

    # Helper property để lấy leader (nếu có)
    @property
    def leader(self):
        for detail in self.member_details:
            if detail.role == "Leader":
                return detail.user
        return None
