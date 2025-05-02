"""
API Router Index

This file centralizes all API router imports to make main.py cleaner.
It imports and exports all API routers so they can be included in the main application with a single import.
API routes are versioned for better compatibility management.
"""

from fastapi import APIRouter

# Import all API routers
from src.views.core_views import router as core_router
from src.views.meeting_views import router as meeting_router
from src.views.notification_views import router as notification_router
from src.views.notification_views import ws_router as notification_ws_router
from src.views.task_views import router as task_router
from src.views.project_views import router as project_router
from src.views.asset_views import router as asset_router
from src.views.client_views import router as client_router
from src.views.customer_service_views import router as customer_service_router
from src.views.department_views import router as department_router
from src.views.position_views import router as position_router
from src.views.user_views import router as user_router

# Create API v1 router that includes all v1 API endpoints
api_router_v1 = APIRouter(prefix="/api/v1")

# Create API router that includes all versions
api_router = APIRouter()

# Include all API routers in v1
api_router_v1.include_router(core_router, prefix="/core")
api_router_v1.include_router(meeting_router, prefix="/meetings")
api_router_v1.include_router(notification_router)
api_router_v1.include_router(task_router, prefix="/tasks")
api_router_v1.include_router(project_router, prefix="/projects")
api_router_v1.include_router(asset_router, prefix="/assets")
api_router_v1.include_router(client_router, prefix="/clients")
api_router_v1.include_router(customer_service_router, prefix="/customer-service")
api_router_v1.include_router(department_router, prefix="/departments")
api_router_v1.include_router(position_router, prefix="/positions")
api_router_v1.include_router(user_router)

# Include the v1 router in the main API router
api_router.include_router(api_router_v1)

# Export the WebSocket router separately since it shouldn't have the /api prefix
ws_router = notification_ws_router
