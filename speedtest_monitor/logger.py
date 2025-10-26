"""
Logging configuration module.

Provides centralized logging setup with rotation and formatting.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
    compression: str = "zip",
) -> None:
    """
    Configure application logger with rotation and formatting.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, only console output
        rotation: When to rotate log file (size or time)
        retention: How long to keep old logs
        compression: Compression format for old logs

    Example:
        >>> setup_logger("INFO", Path("/var/log/speedtest/app.log"))
    """
    # Remove default handler
    logger.remove()

    # Console handler with colored output
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        colorize=True,
    )

    # File handler with rotation
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} | {message}",
            rotation=rotation,
            retention=retention,
            compression=compression,
            enqueue=True,  # Thread-safe logging
        )

    logger.info(f"Logger initialized with level: {log_level}")


def get_logger():
    """
    Get configured logger instance.

    Returns:
        Logger instance

    Example:
        >>> log = get_logger()
        >>> log.info("Application started")
    """
    return logger
