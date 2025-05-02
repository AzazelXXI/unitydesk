"""
Middleware Initialization Module

This module exports middleware functions to be used in the main application.
"""

import logging
import time
import traceback
from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from src.middleware.auth_middleware import (
    get_current_user,
    get_current_active_user,
    role_required,
    admin_only,
    admin_or_manager,
    non_guest,
)

logger = logging.getLogger(__name__)


async def log_exceptions_middleware(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    """
    Middleware that logs exceptions with traceback for debugging.
    """
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Request to {request.url.path} failed with error: {str(e)}")
        logger.error(traceback.format_exc())
        raise


async def request_logging_middleware(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    """
    Middleware that logs API requests with timing.
    """
    start_time = time.time()

    # Get client info
    client_host = request.client.host if request.client else "unknown"

    # Log request start
    logger.info(
        f"Request started: {request.method} {request.url.path} from {client_host}"
    )

    # Process request
    response = await call_next(request)

    # Calculate and log request duration
    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"Request completed: {request.method} {request.url.path} "
        f"- Status: {response.status_code} - Duration: {process_time:.2f}ms"
    )

    return response


__all__ = [
    "log_exceptions_middleware",
    "request_logging_middleware",
    "get_current_user",
    "get_current_active_user",
    "role_required",
    "admin_only",
    "admin_or_manager",
    "non_guest",
]
