# Import all API routers from view modules
from src.apis.asset_views import router as asset_router
from src.apis.analytics_views import router as analytics_router
from src.apis.client_views import router as client_router
from src.apis.project_views import router as project_router
from src.apis.task_views import router as task_router
from src.apis.task_api import (
    router as task_api_router,
)  # New task API with notifications
from src.apis.notification_api import router as notification_router  # Notification API
from src.apis.websocket_api import ws_router  # WebSocket API

# List of all routers to include in the application
web_routers = [
    asset_router,
    analytics_router,
    client_router,
    project_router,
    task_router,  # Task router for task operations
    task_api_router,  # New task API with notifications
    notification_router,  # Notification API
    ws_router,  # WebSocket API for real-time notifications
]
