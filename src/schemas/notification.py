from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from src.models.notification import NotificationType, NotificationChannel, NotificationPriority


# Request schemas
class NotificationCreate(BaseModel):
    user_id: int
    title: str
    content: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    action_url: Optional[str] = None
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP]


class NotificationBulkCreate(BaseModel):
    user_ids: List[int]
    title: str
    content: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    action_url: Optional[str] = None
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP]


class NotificationUpdate(BaseModel):
    read: Optional[bool] = None
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[NotificationPriority] = None
    data: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    action_url: Optional[str] = None


class NotificationSettingUpdate(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    min_priority: Optional[NotificationPriority] = None


class NotificationTemplateCreate(BaseModel):
    name: str
    notification_type: NotificationType
    title_template: str
    content_template: str
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    sms_template: Optional[str] = None
    default_icon: Optional[str] = None


class NotificationTemplateUpdate(BaseModel):
    title_template: Optional[str] = None
    content_template: Optional[str] = None
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    sms_template: Optional[str] = None
    default_icon: Optional[str] = None
    is_active: Optional[bool] = None


# Response schemas
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    notification_type: NotificationType
    priority: NotificationPriority
    resource_type: Optional[str]
    resource_id: Optional[int]
    data: Optional[Dict[str, Any]]
    icon: Optional[str]
    action_url: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]
    in_app_delivered: bool
    email_delivered: bool
    push_delivered: bool
    sms_delivered: bool
    
    class Config:
        orm_mode = True


class NotificationCountResponse(BaseModel):
    total: int
    unread: int
    read: int
    by_type: Dict[NotificationType, int]


class NotificationSettingResponse(BaseModel):
    user_id: int
    notification_type: NotificationType
    in_app_enabled: bool
    email_enabled: bool
    push_enabled: bool
    sms_enabled: bool
    min_priority: NotificationPriority
    
    class Config:
        orm_mode = True


class NotificationTemplateResponse(BaseModel):
    id: int
    name: str
    notification_type: NotificationType
    title_template: str
    content_template: str
    email_subject_template: Optional[str]
    email_body_template: Optional[str]
    sms_template: Optional[str]
    default_icon: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
