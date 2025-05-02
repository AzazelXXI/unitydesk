from fastapi import APIRouter, Depends, HTTPException
import src.controllers.position_controller as controller

router = APIRouter()
# controller = PositionController()

@router.get("/")
async def get_positions():
    """Get all positions"""
    return controller.get_positions()

@router.post("/")
async def create_position(position_data: dict):
    """Create a new position"""
    return controller.create_position(position_data)

@router.get("/{position_id}")
async def get_position(position_id: int):
    """Get position by ID"""
    return controller.get_position(position_id)

@router.put("/{position_id}")
async def update_position(position_id: int, position_data: dict):
    """Update position"""
    return controller.update_position(position_id, position_data)

@router.delete("/{position_id}")
async def delete_position(position_id: int):
    """Delete position"""
    return controller.delete_position(position_id)
