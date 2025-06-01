import enum
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    # A User could create many team
    team_creator = relationship("User", back_populates="created_teams")
    
    # Many Team has many project
    team_project_creator = relationship("Project", back_populates="team_project_created", foreign_keys="[Project.team_id]")
    
