from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Request schemas
class DepartmentBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    head_user_id: Optional[int] = None
    is_active: bool = True
    order_index: int = 0


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    head_user_id: Optional[int] = None
    is_active: Optional[bool] = None
    order_index: Optional[int] = None


class PositionBase(BaseModel):
    title: str
    department_id: int
    description: Optional[str] = None
    responsibilities: Optional[str] = None
    required_skills: Optional[str] = None
    grade_level: int = 0
    is_managerial: bool = False
    reports_to_position_id: Optional[int] = None


class PositionCreate(PositionBase):
    pass


class PositionUpdate(BaseModel):
    title: Optional[str] = None
    department_id: Optional[int] = None
    description: Optional[str] = None
    responsibilities: Optional[str] = None
    required_skills: Optional[str] = None
    grade_level: Optional[int] = None
    is_managerial: Optional[bool] = None
    reports_to_position_id: Optional[int] = None


class DepartmentMembershipCreate(BaseModel):
    user_id: int
    department_id: int
    is_primary: bool = False
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None


class DepartmentMembershipUpdate(BaseModel):
    is_primary: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# Response schemas
class UserBasic(BaseModel):
    id: int
    username: str
    email: str
    
    model_config = {
        "from_attributes": True
    }


class PositionResponse(BaseModel):
    id: int
    title: str
    department_id: int
    description: Optional[str]
    responsibilities: Optional[str]
    required_skills: Optional[str]
    grade_level: int
    is_managerial: bool
    reports_to_position_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class DepartmentResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    parent_id: Optional[int]
    head_user_id: Optional[int]
    is_active: bool
    order_index: int
    path: Optional[str]
    level: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class DepartmentDetailResponse(DepartmentResponse):
    head: Optional[UserBasic]
    subdepartments: List['DepartmentResponse'] = []
    
    model_config = {
        "from_attributes": True
    }


# For organizational chart
class DepartmentTreeNode(BaseModel):
    id: int
    name: str
    code: str
    head_user_id: Optional[int] = None
    head_name: Optional[str] = None
    level: int
    order_index: int
    members_count: int
    children: List['DepartmentTreeNode'] = []


class OrganizationalChartResponse(BaseModel):
    departments: List[DepartmentTreeNode]
    
    model_config = {
        "from_attributes": True
    }


class DepartmentMembershipResponse(BaseModel):
    id: int
    user_id: int
    department_id: int
    is_primary: bool
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    user: UserBasic
    department: DepartmentResponse
    
    model_config = {
        "from_attributes": True
    }


# For batch operations
class DepartmentReorderItem(BaseModel):
    id: int
    parent_id: Optional[int]
    order_index: int


class DepartmentReorderRequest(BaseModel):
    departments: List[DepartmentReorderItem]


# Update recursive references
DepartmentDetailResponse.update_forward_refs()
DepartmentTreeNode.update_forward_refs()
