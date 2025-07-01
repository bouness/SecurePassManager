# utils.py
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def setup_logging(app_name="SecurePass", log_level="INFO"):
    """Set up logging configuration with customizable level"""
    # Determine log directory
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(app_name)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    # Convert string level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create file handler
    log_file = os.path.join(log_dir, f"{app_name}.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)  # File always logs everything
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)  # Console uses specified level
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized at level: {log_level}")
    return logger

def update_logging_level(log_level):
    """Update logging level dynamically"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger = logging.getLogger("SecurePass")
    logger.setLevel(level)
    
    # Update all handlers except file handler
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(level)
    
    logger.info(f"Logging level changed to: {log_level}")
    
def resource_path(relative_path):
    """Get path relative to the executable or script."""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
