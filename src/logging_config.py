"""
Logging configuration for the application
"""
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """Configure application logging to capture ALL logs including Uvicorn"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure logging format
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    log_file = "logs/app.log"
    
    # Set up rotating file handler
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Configure ROOT logger to catch everything
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add our handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers for better control
    loggers_config = {
        "uvicorn": logging.DEBUG,
        "uvicorn.access": logging.INFO,
        "uvicorn.error": logging.INFO,
        "fastapi": logging.DEBUG,
        "src": logging.DEBUG,
        "sqlalchemy.engine": logging.WARNING,  # Reduce DB noise
        "sqlalchemy.pool": logging.WARNING,
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        # Don't add handlers - let them propagate to root
        logger.propagate = True
    
    # Log a test message to verify setup
    root_logger.info("✅ Logging system configured successfully")
    root_logger.info(f"📝 Log file: {log_file}")
    
    return root_logger
