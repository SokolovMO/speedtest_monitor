"""
Main entry point for speedtest monitor.

Runs a single speedtest check and sends results to Telegram.
"""

import signal
import sys
from pathlib import Path

from speedtest_monitor import (
    Config,
    SpeedtestRunner,
    TelegramNotifier,
    get_logger,
    load_config,
    setup_logger,
    validate_config,
)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = get_logger()
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


def main():
    """
    Main execution function.

    Loads configuration, runs speedtest, and sends notification.
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Determine config path
        config_path = Path(__file__).parent.parent / "config.yaml"
        if not config_path.exists():
            config_path = Path("config.yaml")

        # Load configuration
        config = load_config(config_path)
        validate_config(config)

        # Setup logging
        log_file = Path(config.logging.file)
        setup_logger(
            log_level=config.logging.level,
            log_file=log_file,
            rotation=config.logging.rotation,
            retention=config.logging.retention,
        )

        logger = get_logger()
        logger.info("=" * 60)
        logger.info("Speedtest Monitor started")
        logger.info("=" * 60)

        # Run speedtest
        logger.info("Starting speedtest...")
        runner = SpeedtestRunner(config.speedtest)
        result = runner.run()

        # Send notification
        logger.info("Sending Telegram notification...")
        notifier = TelegramNotifier(config)
        success = notifier.send_notification_sync(result)

        if success:
            logger.info("Speedtest monitor completed successfully")
            sys.exit(0)
        else:
            logger.warning("Notification was not sent")
            sys.exit(0)  # Not a critical error

    except Exception as e:
        logger = get_logger()
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
