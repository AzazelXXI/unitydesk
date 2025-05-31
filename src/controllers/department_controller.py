from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta

from src.database import get_db
from src.models_backup.user import Department, Position, DepartmentMembership, User, UserProfile
from src.schemas.department import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentDetailResponse,
    PositionCreate, PositionUpdate, PositionResponse,
    DepartmentMembershipCreate, DepartmentMembershipUpdate, DepartmentMembershipResponse,
    DepartmentReorderRequest, OrganizationalChartResponse, DepartmentTreeNode
)
from src.schemas.user import UserBase

router = APIRouter(
    prefix="/api/departments",
    tags=["departments"]
)


# Department CRUD operations
@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db)
):
    """Create a new department"""
    level = 0
    path = ""
    
    # If parent exists, calculate path and level
    if department.parent_id:
        parent = db.query(Department).filter(Department.id == department.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent department with ID {department.parent_id} not found"
            )
        level = parent.level + 1
        path = f"{parent.path}/{parent.id}" if parent.path else str(parent.id)
    
    # Create new department
    db_department = Department(
        name=department.name,
        code=department.code,
        description=department.description,
        parent_id=department.parent_id,
        head_user_id=department.head_user_id,
        is_active=department.is_active,
        order_index=department.order_index,
        level=level,
        path=path
    )
    
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department


@router.get("/", response_model=List[DepartmentResponse])
def get_departments(
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all departments with optional filtering"""
    query = db.query(Department)
    
    if parent_id is not None:
        query = query.filter(Department.parent_id == parent_id)
    elif parent_id == -1:  # Special case for root departments
        query = query.filter(Department.parent_id is None)
        
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    
    # Order by level first, then by parent_id and order_index
    return query.order_by(Department.level, Department.parent_id, Department.order_index).offset(skip).limit(limit).all()


@router.get("/{department_id}", response_model=DepartmentDetailResponse)
def get_department(
    department_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific department by ID with subdepartments"""
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found"
        )
    return department


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    department_update: DepartmentUpdate,
    db: Session = Depends(get_db)
):
    """Update a department"""
    db_department = db.query(Department).filter(Department.id == department_id).first()
    if not db_department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found"
        )
    
    # Update fields if provided
    update_data = department_update.dict(exclude_unset=True)
    
    # Special handling for parent_id as it affects path and level
    if "parent_id" in update_data and update_data["parent_id"] != db_department.parent_id:
        # Check for circular references
        if update_data["parent_id"] == department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department cannot be its own parent"
            )
            
        # Check if the new parent exists
        if update_data["parent_id"] is not None:
            parent = db.query(Department).filter(Department.id == update_data["parent_id"]).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent department with ID {update_data['parent_id']} not found"
                )
                
            # Check that the new parent is not a descendant of this department
            if parent.path and (str(department_id) in parent.path.split("/")):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move department under its own descendant"
                )
                
            # Update level and path based on new parent
            update_data["level"] = parent.level + 1
            update_data["path"] = f"{parent.path}/{parent.id}" if parent.path else str(parent.id)
            
            # This will trigger an update for all subdepartments
            old_path = db_department.path or str(db_department.id)
            new_path = update_data["path"]
            
            # Update the department first
            for key, value in update_data.items():
                setattr(db_department, key, value)
            db.commit()
            db.refresh(db_department)
            
            # Update all subdepartments
            subdepartments = db.query(Department).filter(
                Department.path.like(f"{old_path}/%") if old_path else Department.parent_id == department_id
            ).all()
            
            for subdept in subdepartments:
                # Calculate new path by replacing the old path prefix with the new one
                if subdept.path:
                    new_subdept_path = subdept.path.replace(old_path, new_path, 1)
                    subdept.path = new_subdept_path
                    # Recalculate level based on path segments
                    subdept.level = new_subdept_path.count("/") + 1
                db.add(subdept)
            
            db.commit()
            return db_department
    
    # Regular update for other fields
    for key, value in update_data.items():
        setattr(db_department, key, value)
    
    db.commit()
    db.refresh(db_department)
    return db_department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db)
):
    """Archive a department (soft delete)"""
    db_department = db.query(Department).filter(Department.id == department_id).first()
    if not db_department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found"
        )
    
    # Check if department has subdepartments
    has_subdepartments = db.query(Department).filter(Department.parent_id == department_id).first() is not None
    if has_subdepartments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete department with subdepartments. Archive or move them first."
        )
    
    # Perform soft delete (archive) - set is_active to False
    db_department.is_active = False
    db.commit()
    return None


# Department members management
@router.get("/{department_id}/members", response_model=List[DepartmentMembershipResponse])
def get_department_members(
    department_id: int,
    is_primary: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all members of a department"""
    query = db.query(DepartmentMembership).filter(DepartmentMembership.department_id == department_id)
    
    if is_primary is not None:
        query = query.filter(DepartmentMembership.is_primary == is_primary)
    
    return query.all()


@router.post("/{department_id}/members", response_model=DepartmentMembershipResponse, status_code=status.HTTP_201_CREATED)
def add_department_member(
    department_id: int,
    membership: DepartmentMembershipCreate,
    db: Session = Depends(get_db)
):
    """Add a user to a department"""
    # Verify department exists
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found"
        )
    
    # Verify user exists
    user = db.query(User).filter(User.id == membership.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {membership.user_id} not found"
        )
    
    # Check if membership already exists
    existing_membership = db.query(DepartmentMembership).filter(
        DepartmentMembership.department_id == department_id,
        DepartmentMembership.user_id == membership.user_id,
        DepartmentMembership.end_date.is_(None)  # Active membership
    ).first()
    
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {membership.user_id} is already a member of department {department_id}"
        )
    
    # If setting as primary, update any existing primary memberships
    if membership.is_primary:
        existing_primary = db.query(DepartmentMembership).filter(
            DepartmentMembership.user_id == membership.user_id,
            DepartmentMembership.is_primary == True,
            DepartmentMembership.end_date.is_(None)
        ).first()
        
        if existing_primary:
            existing_primary.is_primary = False
            db.add(existing_primary)
            
        # Also update the user's department_id
        user.department_id = department_id
        db.add(user)
    
    # Create new membership
    new_membership = DepartmentMembership(
        user_id=membership.user_id,
        department_id=department_id,
        is_primary=membership.is_primary,
        start_date=membership.start_date,
        end_date=membership.end_date
    )
    
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    return new_membership


@router.delete("/{department_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_department_member(
    department_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Remove a user from a department (end their membership)"""
    membership = db.query(DepartmentMembership).filter(
        DepartmentMembership.department_id == department_id,
        DepartmentMembership.user_id == user_id,
        DepartmentMembership.end_date.is_(None)  # Active membership
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} is not a member of department {department_id}"
        )
    
    # End membership by setting end_date to current time
    membership.end_date = datetime.utcnow()
    
    # If this was the primary department, update user.department_id to None
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.department_id == department_id:
        user.department_id = None
        db.add(user)
    
    db.add(membership)
    db.commit()
    return None


# Get subdepartments
@router.get("/{department_id}/subdepartments", response_model=List[DepartmentResponse])
def get_subdepartments(
    department_id: int,
    recursive: bool = False,
    db: Session = Depends(get_db)
):
    """Get all subdepartments of a department"""
    if recursive:
        # Get department's path to find all descendants
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {department_id} not found"
            )
        
        path_query = f"{department.path}/{department_id}%" if department.path else f"{department_id}/%"
        subdepartments = db.query(Department).filter(Department.path.like(path_query)).all()
        return subdepartments
    else:
        # Only direct children
        return db.query(Department).filter(Department.parent_id == department_id).all()


# Organizational chart
@router.get("/organizational-chart", response_model=OrganizationalChartResponse)
def get_organizational_chart(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """Get the full organizational chart structure"""
    # Get all departments
    query = db.query(Department)
    if not include_inactive:
        query = query.filter(Department.is_active == True)
    
    departments = query.order_by(Department.level, Department.order_index).all()
    
    # Get member counts
    member_counts = {}
    counts = db.query(
        DepartmentMembership.department_id,
        func.count(DepartmentMembership.user_id).label("count")
    ).filter(DepartmentMembership.end_date.is_(None)).group_by(DepartmentMembership.department_id).all()
    
    for dept_id, count in counts:
        member_counts[dept_id] = count
    
    # Get department head names
    head_names = {}
    department_heads = db.query(
        Department.head_user_id,
        UserProfile.first_name,
        UserProfile.last_name
    ).join(
        User, Department.head_user_id == User.id
    ).join(
        UserProfile, User.id == UserProfile.user_id
    ).filter(Department.head_user_id.isnot(None)).all()
    
    for head_id, first_name, last_name in department_heads:
        head_names[head_id] = f"{first_name} {last_name}" if first_name and last_name else "Unknown"
    
    # Build tree
    def build_tree(parent_id=None, level=0):
        nodes = []
        for dept in departments:
            if dept.parent_id == parent_id:
                children = build_tree(dept.id, level + 1)
                head_name = head_names.get(dept.head_user_id) if dept.head_user_id else None
                
                node = DepartmentTreeNode(
                    id=dept.id,
                    name=dept.name,
                    code=dept.code,
                    head_user_id=dept.head_user_id,
                    head_name=head_name,
                    level=dept.level,
                    order_index=dept.order_index,
                    members_count=member_counts.get(dept.id, 0),
                    children=children
                )
                nodes.append(node)
        return nodes
    
    # Start with root departments (parent_id is None)
    tree = build_tree()
    return OrganizationalChartResponse(departments=tree)


# Department reordering
@router.put("/reorder", response_model=List[DepartmentResponse])
def reorder_departments(
    reorder_request: DepartmentReorderRequest,
    db: Session = Depends(get_db)
):
    """Update department order and parent relationships in batch"""
    updated_departments = []
    
    for item in reorder_request.departments:
        department = db.query(Department).filter(Department.id == item.id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {item.id} not found"
            )
        
        # Update parent if changed
        if item.parent_id != department.parent_id:
            if item.parent_id is not None:
                parent = db.query(Department).filter(Department.id == item.parent_id).first()
                if not parent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Parent department with ID {item.parent_id} not found"
                    )
                
                # Prevent circular references
                if parent.path and str(department.id) in parent.path.split("/"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot move department {department.id} under its descendant {parent.id}"
                    )
                
                # Update level and path
                department.parent_id = item.parent_id
                department.level = parent.level + 1
                department.path = f"{parent.path}/{parent.id}" if parent.path else str(parent.id)
            else:
                # Moving to root level
                department.parent_id = None
                department.level = 0
                department.path = ""
        
        # Update order index
        department.order_index = item.order_index
        db.add(department)
        updated_departments.append(department)
    
    db.commit()
    for dept in updated_departments:
        db.refresh(dept)
    
    return updated_departments
