"""
Configuration management module.

Handles loading and validation of application configuration.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml
from dotenv import load_dotenv


@dataclass
class ServerConfig:
    """Server identification configuration."""

    name: str = "auto"
    location: str = "auto"
    identifier: str = "auto"
    description: str = ""


@dataclass
class SpeedtestConfig:
    """Speedtest execution configuration."""

    timeout: int = 30
    servers: List[int] = field(default_factory=list)
    retry_count: int = 3
    retry_delay: int = 5


@dataclass
class ThresholdsConfig:
    """Speed thresholds configuration (in Mbps)."""

    very_low: float = 50.0
    low: float = 200.0
    medium: float = 500.0
    good: float = 1000.0


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""

    bot_token: str
    chat_ids: List[str] = field(default_factory=list)
    check_interval: int = 3600
    send_always: bool = False
    format: str = "html"
    



@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    file: str = "speedtest.log"
    rotation: str = "10 MB"
    retention: str = "1 week"


@dataclass
class Config:
    """Main application configuration."""

    server: ServerConfig
    speedtest: SpeedtestConfig
    thresholds: ThresholdsConfig
    telegram: TelegramConfig
    logging: LoggingConfig


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    pass


def load_config(config_path: Path) -> Config:
    """
    Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to config.yaml file

    Returns:
        Parsed configuration object

    Raises:
        ConfigurationError: If configuration is invalid or missing required fields

    Example:
        >>> config = load_config(Path("config.yaml"))
        >>> print(config.telegram.bot_token)
    """
    # Load environment variables
    load_dotenv()

    # Check required environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        raise ConfigurationError(
            "TELEGRAM_BOT_TOKEN environment variable is required. "
            "Set it in .env file or export TELEGRAM_BOT_TOKEN=your_token"
        )

    # Load YAML configuration
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f)

    if not yaml_config:
        raise ConfigurationError("Configuration file is empty")

    # Parse configuration sections
    try:
        server_config = ServerConfig(**yaml_config.get("server", {}))
        speedtest_config = SpeedtestConfig(**yaml_config.get("speedtest", {}))
        thresholds_config = ThresholdsConfig(**yaml_config.get("thresholds", {}))
        logging_config = LoggingConfig(**yaml_config.get("logging", {}))

        # Parse Telegram configuration
        telegram_yaml = yaml_config.get("telegram", {})
        
        # Get chat_ids from YAML (ONLY from config.yaml, not from .env)
        chat_ids = telegram_yaml.get("chat_ids", [])
        
        if not chat_ids:
            raise ConfigurationError(
                "At least one chat_id must be specified in config.yaml under telegram.chat_ids"
            )
        
        telegram_config = TelegramConfig(
            bot_token=bot_token,
            chat_ids=chat_ids,
            check_interval=telegram_yaml.get("check_interval", 3600),
            send_always=telegram_yaml.get("send_always", False),
            format=telegram_yaml.get("format", "html"),
        )

        return Config(
            server=server_config,
            speedtest=speedtest_config,
            thresholds=thresholds_config,
            telegram=telegram_config,
            logging=logging_config,
        )
    except TypeError as e:
        raise ConfigurationError(f"Invalid configuration format: {e}")


def validate_config(config: Config) -> None:
    """
    Validate configuration values.

    Args:
        config: Configuration to validate

    Raises:
        ConfigurationError: If configuration values are invalid

    Example:
        >>> validate_config(config)
    """
    # Validate speedtest timeout
    if config.speedtest.timeout <= 0:
        raise ConfigurationError("Speedtest timeout must be positive")

    # Validate thresholds
    thresholds = [
        config.thresholds.very_low,
        config.thresholds.low,
        config.thresholds.medium,
        config.thresholds.good,
    ]
    if not all(t > 0 for t in thresholds):
        raise ConfigurationError("All thresholds must be positive")

    # Validate Telegram format
    if config.telegram.format not in ["html", "markdown"]:
        raise ConfigurationError("Telegram format must be 'html' or 'markdown'")

    # Validate logging level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.logging.level.upper() not in valid_levels:
        raise ConfigurationError(
            f"Invalid log level. Must be one of: {', '.join(valid_levels)}"
        )
