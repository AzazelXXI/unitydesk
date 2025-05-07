"""
Application middleware functions
"""
from fastapi import Request
import logging
import time

# Get logger
logger = logging.getLogger("fastapi")

async def log_exceptions_middleware(request: Request, call_next):
    """Log uncaught exceptions"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.exception("Unhandled exception occurred")
        raise e

async def request_logging_middleware(request: Request, call_next):
    """Log request information and timing"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    log_msg = f"{request.method} {request.url.path}"
    logger.info(f"{log_msg} completed in {process_time:.4f}s")
    
    return response
