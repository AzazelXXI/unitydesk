# filepath: d:\projects\CSA\csa-hello\src\main.py
"""
CSA Platform - Main Application File

This file initializes the FastAPI application and includes all routers.
Application logic is moved to appropriate controller files.
Web routes for Jinja templates are in the src/web/ directory.
API routes are centralized through the api_router module with versioning.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
import asyncio
import logging

# Import all web routers through the centralized import
from src.apis import web_routers as api_web_routers
from src.views import web_routers as view_web_routers

# Import centralized API router (includes all API controllers)
from src.api_router import api_router, ws_router as notification_ws_router

# Import middleware and logging
from src.middleware import log_exceptions_middleware, request_logging_middleware
from src.logging_config import setup_logging
from src.apis.error_handlers import (
    http_exception_handler,
    not_found_exception_handler,
    server_error_handler,
    redirect_to_login_exception_handler,
)
from src.middleware.auth_middleware import RedirectToLoginException
from fastapi.exceptions import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import status

# Set up logging
app_logger = setup_logging()

# Initialize FastAPI application
app = FastAPI(
    title="CSA Platform",
    description="Customer Service Automation Platform",
    version="1.0.0",
    docs_url="/api/v1/docs",
)

# Mount static files for each web module
# Core static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="src/views/core/static"), name="static")

# Mount static files for task views
app.mount(
    "/tasks/static",
    StaticFiles(directory="src/views/task/static"),
    name="task_static",
)

# Mount static files for user views (authentication pages)
app.mount(
    "/user/static",
    StaticFiles(directory="src/views/user/static"),
    name="user_static",
)

# Mount static files for project views
app.mount(
    "/projects/static",
    StaticFiles(directory="src/views/project/static"),
    name="project_static",
)

# Mount static files for meeting views
app.mount(
    "/meeting/static",
    StaticFiles(directory="src/views/meeting/static"),
    name="meeting_static",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add custom middleware
app.middleware("http")(log_exceptions_middleware)
app.middleware("http")(request_logging_middleware)

# Include all web routers (Jinja templates)
for router in api_web_routers:
    app.include_router(router)

# Include all view web routers (Jinja templates)
for router in view_web_routers:
    app.include_router(router)

# Task routers are already included in view_web_routers, no need to include them again

# Import and include the project router
from src.views.project.project_routes import router as project_web_router

app.include_router(project_web_router)

# Note: Dashboard router temporarily disabled to resolve /projects route conflict
# from src.views.dashboard_routes import router as dashboard_router
# app.include_router(dashboard_router)

# Include the centralized API router (which includes all API routes with versioning)
app.include_router(api_router)

# Include WebSocket router separately
app.include_router(notification_ws_router)

# Add exception handlers
app.add_exception_handler(RedirectToLoginException, redirect_to_login_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(status.HTTP_404_NOT_FOUND, not_found_exception_handler)
app.add_exception_handler(Exception, server_error_handler)


# Add startup logging
@app.on_event("startup")
async def startup_event():
    logger = logging.getLogger("src.main")


# Gracefully handle asyncio.CancelledError on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    try:
        # Perform any cleanup tasks here
        app_logger.info("Application is shutting down...")
    except asyncio.CancelledError:
        app_logger.warning("Shutdown process was interrupted by CancelledError.")
        raise
