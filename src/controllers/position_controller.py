from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database import get_db
from src.models.user import Position, Department, User
from src.schemas.department import (
    PositionCreate, PositionUpdate, PositionResponse
)
from src.schemas.user import UserResponse

router = APIRouter(
    prefix="/api/positions",
    tags=["positions"]
)


@router.post("/", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
def create_position(
    position: PositionCreate,
    db: Session = Depends(get_db)
):
    """Create a new position"""
    # Verify department exists
    department = db.query(Department).filter(Department.id == position.department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {position.department_id} not found"
        )
    
    # Verify reports_to position exists if specified
    if position.reports_to_position_id:
        reports_to = db.query(Position).filter(Position.id == position.reports_to_position_id).first()
        if not reports_to:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reports-to position with ID {position.reports_to_position_id} not found"
            )
    
    # Create new position
    db_position = Position(
        title=position.title,
        department_id=position.department_id,
        description=position.description,
        responsibilities=position.responsibilities,
        required_skills=position.required_skills,
        grade_level=position.grade_level,
        is_managerial=position.is_managerial,
        reports_to_position_id=position.reports_to_position_id
    )
    
    db.add(db_position)
    db.commit()
    db.refresh(db_position)
    return db_position


@router.get("/", response_model=List[PositionResponse])
def get_positions(
    department_id: Optional[int] = None,
    is_managerial: Optional[bool] = None,
    title: Optional[str] = None,
    grade_level_min: Optional[int] = None,
    grade_level_max: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all positions with optional filtering"""
    query = db.query(Position)
    
    if department_id is not None:
        query = query.filter(Position.department_id == department_id)
    
    if is_managerial is not None:
        query = query.filter(Position.is_managerial == is_managerial)
    
    if title:
        query = query.filter(Position.title.ilike(f"%{title}%"))
    
    if grade_level_min is not None:
        query = query.filter(Position.grade_level >= grade_level_min)
    
    if grade_level_max is not None:
        query = query.filter(Position.grade_level <= grade_level_max)
    
    return query.order_by(Position.department_id, Position.grade_level.desc()).offset(skip).limit(limit).all()


@router.get("/{position_id}", response_model=PositionResponse)
def get_position(
    position_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific position by ID"""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position with ID {position_id} not found"
        )
    return position


@router.put("/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: int,
    position_update: PositionUpdate,
    db: Session = Depends(get_db)
):
    """Update a position"""
    db_position = db.query(Position).filter(Position.id == position_id).first()
    if not db_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position with ID {position_id} not found"
        )
    
    # Update fields if provided
    update_data = position_update.dict(exclude_unset=True)
    
    # Verify department exists if updating department_id
    if "department_id" in update_data:
        department = db.query(Department).filter(Department.id == update_data["department_id"]).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {update_data['department_id']} not found"
            )
    
    # Verify reports_to position exists if updating
    if "reports_to_position_id" in update_data and update_data["reports_to_position_id"]:
        if update_data["reports_to_position_id"] == position_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Position cannot report to itself"
            )
            
        reports_to = db.query(Position).filter(Position.id == update_data["reports_to_position_id"]).first()
        if not reports_to:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reports-to position with ID {update_data['reports_to_position_id']} not found"
            )
    
    for key, value in update_data.items():
        setattr(db_position, key, value)
    
    db.commit()
    db.refresh(db_position)
    return db_position


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    position_id: int,
    db: Session = Depends(get_db)
):
    """Delete a position"""
    db_position = db.query(Position).filter(Position.id == position_id).first()
    if not db_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position with ID {position_id} not found"
        )
    
    # Check if any users hold this position
    users_with_position = db.query(User).filter(User.position_id == position_id).first()
    if users_with_position:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete position that is assigned to users. Reassign users first."
        )
    
    # Check if any positions report to this position
    positions_reporting_to = db.query(Position).filter(Position.reports_to_position_id == position_id).first()
    if positions_reporting_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete position that has other positions reporting to it. Update reporting structure first."
        )
    
    db.delete(db_position)
    db.commit()
    return None


@router.get("/{position_id}/users", response_model=List[UserResponse])
def get_position_users(
    position_id: int,
    db: Session = Depends(get_db)
):
    """Get all users assigned to a position"""
    # Verify position exists
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position with ID {position_id} not found"
        )
    
    users = db.query(User).filter(User.position_id == position_id).all()
    return users


@router.get("/organizational-chart", response_model=dict)
def get_position_organizational_chart(
    department_id: Optional[int] = None,
    include_users: bool = True,
    db: Session = Depends(get_db)
):
    """Get position-based organizational chart"""
    # Start with top-level positions (no reports_to_position_id)
    query = db.query(Position).filter(Position.reports_to_position_id.is_(None))
    
    # Filter by department if specified
    if department_id:
        query = query.filter(Position.department_id == department_id)
    
    top_positions = query.all()
    
    # Function to recursively build position tree
    def build_position_tree(position):
        position_dict = {
            "id": position.id,
            "title": position.title,
            "department_id": position.department_id,
            "grade_level": position.grade_level,
            "is_managerial": position.is_managerial
        }
        
        # Add users if requested
        if include_users:
            users = db.query(User).filter(User.position_id == position.id).all()
            position_dict["users"] = [
                {"id": user.id, "username": user.username, "email": user.email} 
                for user in users
            ]
        
        # Find subordinate positions
        subordinates = db.query(Position).filter(Position.reports_to_position_id == position.id).all()
        if subordinates:
            position_dict["subordinates"] = [build_position_tree(sub) for sub in subordinates]
        else:
            position_dict["subordinates"] = []
            
        return position_dict
    
    # Build the tree for each top position
    chart = {
        "positions": [build_position_tree(pos) for pos in top_positions]
    }
    
    return chart


@router.get("/vacant", response_model=List[PositionResponse])
def get_vacant_positions(
    department_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get positions that have no users assigned"""
    # Subquery to find positions with users
    positions_with_users = db.query(User.position_id).filter(User.position_id.isnot(None)).distinct().subquery()
    
    # Query for positions without users
    query = db.query(Position).filter(~Position.id.in_(positions_with_users))
    
    # Filter by department if specified
    if department_id:
        query = query.filter(Position.department_id == department_id)
    
    return query.all()
