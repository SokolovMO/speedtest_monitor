"""
Speedtest Monitor - Internet speed monitoring with Telegram notifications.

A production-ready tool for monitoring internet connection speed across
multiple servers with centralized Telegram reporting.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

from .config import Config, load_config, validate_config
from .logger import get_logger, setup_logger
from .speedtest_runner import SpeedtestResult, SpeedtestRunner
from .telegram_notifier import TelegramNotifier
from .utils import (
    format_ping,
    format_speed,
    get_location_by_ip,
    get_public_ip,
    get_system_info,
)

__all__ = [
    "__version__",
    "Config",
    "load_config",
    "validate_config",
    "setup_logger",
    "get_logger",
    "SpeedtestRunner",
    "SpeedtestResult",
    "TelegramNotifier",
    "get_system_info",
    "get_public_ip",
    "get_location_by_ip",
    "format_speed",
    "format_ping",
]
