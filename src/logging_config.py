"""
Logging configuration for the application
"""
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """Configure application logging"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure logging
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_file = "logs/app.log"
    
    # Set up rotating file handler
    log_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
    log_handler.setFormatter(log_formatter)
    log_handler.setLevel(logging.INFO)
    
    # Set up app logger
    app_logger = logging.getLogger("fastapi")
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(log_handler)
    
    # Add console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    app_logger.addHandler(console_handler)
    
    return app_logger
