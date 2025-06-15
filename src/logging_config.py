"""
Logging configuration for the application
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import datetime


def setup_logging():
    """Configure application logging to capture ALL logs including Uvicorn"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Generate time-stamped log filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_file = f"logs/app-log-{timestamp}.log"

    # Configure logging format
    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Set up file handler (creates new file each time)
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
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

    # Log startup information with the new log file name
    startup_logger = logging.getLogger("src.logging")
    startup_logger.info(f"📝 New log session started")
    startup_logger.info(f"📁 Log file: {log_file}")

    return root_logger


def get_latest_log_file():
    """Get the path to the most recent log file"""
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        return None

    # Find all app-log-*.log files
    log_files = [
        f
        for f in os.listdir(logs_dir)
        if f.startswith("app-log-") and f.endswith(".log")
    ]

    if not log_files:
        return None

    # Sort by modification time (newest first)
    log_files.sort(
        key=lambda f: os.path.getmtime(os.path.join(logs_dir, f)), reverse=True
    )

    return os.path.join(logs_dir, log_files[0])
