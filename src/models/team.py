import enum
import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Text, UUID
from sqlalchemy.orm import relationship
from .association_tables import project_teams_table

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
    team_creator = relationship("User", back_populates="created_teams")

    # Many Team has many project
    projects = relationship(
        "Project", secondary=project_teams_table, back_populates="teams"
    )
