from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


# Project status
class ProjectStatus(str, Enum):
    PLANNING = "PLANNING"
    NOT_STARTED = "NOT STARTED"
    IN_PROGRESS = "IN PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ProjectPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    objectives: Optional[List[str]] = []
    scope: Optional[str] = Field(None, max_length=2000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: ProjectPriority = ProjectPriority.MEDIUM
    budget: Optional[float] = Field(None, ge=0)
    team_leader_id: Optional[str] = None
    team_members: Optional[List[str]] = []

    @validator("end_date")
    def validate_end_date(cls, v, values):
        if v and "start_date" in values and values["start_date"]:
            if v <= values["start_date"]:
                raise ValueError("End date must be after start date")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    objectives: Optional[List[str]] = None
    scope: Optional[str] = Field(None, max_length=2000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[ProjectPriority] = None
    budget: Optional[float] = Field(None, ge=0)
    progress: Optional[float] = Field(None, ge=0, le=100)
    team_leader_id: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    objectives: Optional[List[str]]
    scope: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    status: ProjectStatus
    priority: ProjectPriority
    progress: float
    budget: Optional[float]
    owner_id: str
    team_leader_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
