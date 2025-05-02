"""
Calendar Web Router - Handles calendar web routes and Jinja template rendering

This module contains all calendar-related web routes for the CSA Platform, including:
- Calendar overview page
- Monthly calendar view
- Weekly calendar view
- Event detail views
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

# Create router for calendar web routes
router = APIRouter(
    prefix="/calendar",
    tags=["web-calendar"],
    responses={404: {"description": "Page not found"}},
)

# Templates
templates = Jinja2Templates(directory="src/web/calendar/templates")

@router.get("/")
async def calendar_home(request: Request):
    """Calendar home page"""
    return templates.TemplateResponse(
        request=request, 
        name="calendar.html", 
        context={"request": request, "title": "Calendar"}
    )

@router.get("/month")
async def calendar_month_view(request: Request):
    """Monthly calendar view"""
    return templates.TemplateResponse(
        request=request, 
        name="month_view.html", 
        context={"request": request, "title": "Monthly Calendar"}
    )

@router.get("/week")
async def calendar_week_view(request: Request):
    """Weekly calendar view"""
    return templates.TemplateResponse(
        request=request, 
        name="week_view.html", 
        context={"request": request, "title": "Weekly Calendar"}
    )

@router.get("/event/{event_id}")
async def event_details(request: Request, event_id: int):
    """Event details view"""
    # In a real application, you would fetch the event from a database
    event = {"id": event_id, "title": "Example Event", "date": "2025-04-24"}
    return templates.TemplateResponse(
        request=request, 
        name="event_details.html",
        context={"request": request, "title": "Event Details", "event": event}
    )
