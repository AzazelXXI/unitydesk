from sqlalchemy import Column, Integer, Table
from .base import Base
# FIXME: Problem with the many-to-many
project_teams_table = Table(
    "project_team",
    Base.metadata,
    Column("project_id", Integer)
)