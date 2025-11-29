"""Application constants.

This module contains all application-wide constants to avoid hardcoded values
throughout the codebase.
"""

# Telegram API Configuration
MAX_MESSAGE_LENGTH = 4096
TELEGRAM_API_TIMEOUT = 30
TELEGRAM_RETRY_COUNT = 3
TELEGRAM_RETRY_DELAY = 2  # seconds

# Speedtest Configuration
DEFAULT_TIMEOUT = 60
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 5  # seconds
SPEEDTEST_COMMANDS = ["speedtest", "speedtest-cli"]

# External APIs
IPAPI_URL = "https://ipapi.co/{ip}/json/"
IPIFY_URL = "https://api.ipify.org"
API_TIMEOUT = 5
API_RETRY_COUNT = 2

# Logging
DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
LOG_ROTATION = "10 MB"
LOG_RETENTION = "1 week"

# File Paths
DEFAULT_CONFIG_PATH = "config.yaml"
DEFAULT_ENV_PATH = ".env"
