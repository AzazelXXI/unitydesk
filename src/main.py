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
import ssl
import asyncio

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
)
from fastapi.exceptions import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import status

# Set up logging
app_logger = setup_logging()

# Configure SSL for secure connections
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(".cert/cert.pem", keyfile=".cert/key.pem")

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

# Include task web router directly to avoid API prefix
try:
    from src.views.task.web_routes import task_web_router

    app.include_router(task_web_router)
except Exception as e:
    app_logger.error(f"Failed to include task_web_router: {e}")

# Include the centralized API router (which includes all API routes with versioning)
app.include_router(api_router)

# Include WebSocket router separately
app.include_router(notification_ws_router)

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(status.HTTP_404_NOT_FOUND, not_found_exception_handler)
app.add_exception_handler(Exception, server_error_handler)


# Gracefully handle asyncio.CancelledError on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    try:
        # Perform any cleanup tasks here
        app_logger.info("Application is shutting down...")
    except asyncio.CancelledError:
        app_logger.warning("Shutdown process was interrupted by CancelledError.")
        raise
