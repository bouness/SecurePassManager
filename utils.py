import logging
import os
import platform
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_app_data_dir(app_name="SecurePass"):
    """Get OS-specific application data directory"""
    system = platform.system()

    if system == "Windows":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / app_name
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / app_name
    else:  # Linux and other Unix-like systems
        # Follow XDG Base Directory Specification
        xdg_data = os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")
        return Path(xdg_data) / app_name.lower()


def setup_logging(app_name="SecurePass", log_level="INFO"):
    """Set up logging configuration with customizable level"""
    # Get OS-specific application data directory
    app_data_dir = get_app_data_dir(app_name)
    log_dir = app_data_dir / "logs"

    # Create log directory if needed
    log_dir.mkdir(parents=True, exist_ok=True)

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
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create file handler with rotation
    log_file = log_dir / f"{app_name}.log"
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3
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
    logger.info(f"Log directory: {log_dir}")
    return logger


def update_logging_level(log_level, app_name="SecurePass"):
    """Update logging level dynamically"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger = logging.getLogger(app_name)
    logger.setLevel(level)

    # Update all handlers except file handler
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(level)

    logger.info(f"Logging level changed to: {log_level}")


def resource_path(relative_path):
    """Get path relative to the executable or script."""
    if getattr(sys, "frozen", False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent

    return str(base_path / relative_path)


# Additional helper for config files
def get_config_path(app_name="SecurePass"):
    """Get OS-specific config file path"""
    app_data_dir = get_app_data_dir(app_name)
    config_dir = app_data_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "settings.ini"
