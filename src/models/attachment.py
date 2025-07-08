import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from .base import Base


class Attachment(Base):
    """
    Attachment model for files uploaded to tasks or projects
    """

    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Foreign Keys
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=True
    )  # Project documents

    # Relationships
    uploader = relationship("User", back_populates="uploaded_attachments")
    project = relationship("Project", back_populates="documents")
    tasks = relationship(
        "Task", secondary="task_attachments", back_populates="attachments"
    )
    comments = relationship(
        "Comment", secondary="comment_attachments", back_populates="attachments"
    )
