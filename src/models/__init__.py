from sqlalchemy.orm import relationship
from src.models.user import User, UserProfile
from src.models.messenger import Chat, Message, ChatMember
from src.models.calendar import Calendar, Event, EventParticipant
from src.models.document import Document
from src.models.task import Task, TaskAssignee, Project
from src.models.storage import Folder, File, FilePermission
from src.models.notification import Notification

User.owned_chats = relationship("Chat", back_populates="owner")
User.messages = relationship("Message", back_populates="sender")
User.chat_memberships = relationship("ChatMember", back_populates="user")
User.calendars = relationship("Calendar", back_populates="owner")
User.events = relationship("Event", back_populates="organizer")
User.event_participations = relationship("EventParticipant", back_populates="user")
User.documents = relationship("Document", back_populates="owner")
User.folders = relationship("Folder", back_populates="owner")
User.files = relationship("File", back_populates="owner") 
User.tasks_created = relationship(
    "Task", foreign_keys="Task.creator_id", back_populates="creator"
)
User.task_assignments = relationship("TaskAssignee", back_populates="user")
User.projects_owned = relationship("Project", back_populates="owner")
User.notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
