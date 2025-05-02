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
import logging

# Import all web routers through the centralized import
from src.web import web_routers

# Import centralized API router (includes all API controllers)
from src.api_router import api_router, ws_router as notification_ws_router

# Import middleware and logging
from src.middleware import log_exceptions_middleware, request_logging_middleware
from src.logging_config import setup_logging

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
app.mount("/static", StaticFiles(directory="src/web/core/static"), name="static")
app.mount(
    "/meeting/static",
    StaticFiles(directory="src/web/meeting/static"),
    name="meeting_static",
)
app.mount(
    "/user/static",
    StaticFiles(directory="src/web/user/static"),
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
for router in web_routers:
    app.include_router(router)

# Include the centralized API router (which includes all API routes with versioning)
app.include_router(api_router)

# Include WebSocket router separately
app.include_router(notification_ws_router)


# Gracefully handle asyncio.CancelledError on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    try:
        # Perform any cleanup tasks here
        app_logger.info("Application is shutting down...")
    except asyncio.CancelledError:
        app_logger.warning("Shutdown process was interrupted by CancelledError.")
        raise
