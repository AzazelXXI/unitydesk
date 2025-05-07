"""
Error handlers for FastAPI application
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions and return appropriate JSON response
    """
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def not_found_exception_handler(
    request: Request, exc: HTTPException
) -> HTMLResponse:
    """
    Handle 404 Not Found exceptions and return custom error page
    """
    logger.warning(f"Not found: {request.url}")
    content = f"""
    <html>
        <head>
            <title>Page Not Found</title>
            <style>
                body {{ 
                    font-family: 'Arial', sans-serif;
                    text-align: center;
                    padding: 50px;
                    background-color: #f8f9fa;
                }}
                .error-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 30px;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }}
                h1 {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>404 - Page Not Found</h1>
                <p>The page you are looking for does not exist.</p>
                <p><a href="/">Return to Home</a></p>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=content, status_code=status.HTTP_404_NOT_FOUND)


async def server_error_handler(request: Request, exc: Exception) -> HTMLResponse:
    """
    Handle 500 Server Error exceptions and return custom error page
    """
    logger.error(f"Server error: {exc}", exc_info=True)
    content = f"""
    <html>
        <head>
            <title>Server Error</title>
            <style>
                body {{ 
                    font-family: 'Arial', sans-serif;
                    text-align: center;
                    padding: 50px;
                    background-color: #f8f9fa;
                }}
                .error-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 30px;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }}
                h1 {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>500 - Server Error</h1>
                <p>Something went wrong on our end. Please try again later.</p>
                <p><a href="/">Return to Home</a></p>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(
        content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
