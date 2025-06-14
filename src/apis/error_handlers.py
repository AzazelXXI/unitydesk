from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


async def http_exception_handler(
    request: Request, exc: FastAPIHTTPException | StarletteHTTPException
):
    """Handler for HTTP exceptions"""
    logger.warning(
        f"HTTP exception: {exc.status_code} - {getattr(exc, 'detail', str(exc))}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": getattr(exc, "detail", str(exc))},
    )


async def not_found_exception_handler(request: Request, exc: Exception):
    """Handler for 404 not found errors"""
    logger.warning(f"Resource not found: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Resource not found"}
    )


async def server_error_handler(request: Request, exc: Exception):
    """Handler for unexpected server errors - DEBUGGING MODE"""
    import traceback

    error_details = traceback.format_exc()
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

    # Return detailed error for debugging (REMOVE THIS IN PRODUCTION!)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc),
            "traceback": error_details,
            "path": str(request.url.path),
        },
    )
