from fastapi import APIRouter, Depends, HTTPException
import src.controllers.department_controller as controller

router = APIRouter()
# controller = Department()

@router.get("/")
async def get_departments():
    """Get all departments"""
    return controller.get_departments()

@router.post("/")
async def create_department(department_data: dict):
    """Create a new department"""
    return controller.create_department(department_data)

@router.get("/{department_id}")
async def get_department(department_id: int):
    """Get department by ID"""
    return controller.get_department(department_id)

@router.put("/{department_id}")
async def update_department(department_id: int, department_data: dict):
    """Update department"""
    return controller.update_department(department_id, department_data)

@router.delete("/{department_id}")
async def delete_department(department_id: int):
    """Delete department"""
    return controller.delete_department(department_id)
