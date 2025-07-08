import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base


class Comment(Base):
    """
    Comment model for tasks - allows users to add comments to tasks
    """

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Comment author
    task_id = Column(
        Integer, ForeignKey("tasks.id"), nullable=False
    )  # Task being commented on

    # Relationships
    author = relationship("User", back_populates="comments")
    task = relationship("Task", back_populates="comments")
    attachments = relationship(
        "Attachment",
        secondary="comment_attachments",
        backref="comment_attachments",
        cascade="all, delete",
    )
