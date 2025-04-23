# Import all API routers from view modules
from src.views.asset_views import router as asset_router
from src.views.analytics_views import router as analytics_router
from src.views.client_views import router as client_router
from src.views.project_views import router as project_router
from src.views.task_views import router as task_router
from src.views.task_views import task_router

# List of all routers to include in the application
routers = [
    asset_router,
    analytics_router,
    client_router,
    project_router,
    task_router,   # Task router for project-related endpoints
    task_router    # Task router for direct task operations
]
