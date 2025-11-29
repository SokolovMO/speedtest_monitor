"""
Main entry point for speedtest monitor.

Runs a single speedtest check and sends results to Telegram.
"""

import argparse
import asyncio
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

from speedtest_monitor import (
    SpeedtestRunner,
    TelegramNotifier,
    get_logger,
    load_config,
    setup_logger,
    validate_config,
)
from speedtest_monitor.aggregator import Aggregator
from speedtest_monitor.api import APIServer
from speedtest_monitor.constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_LOG_LEVEL,
)
from speedtest_monitor.models import SpeedtestResult as ModelSpeedtestResult
from speedtest_monitor.node_client import send_result_to_master
from speedtest_monitor.utils import get_system_info

# Version information
__version__ = "1.0.0"

# Global flag for graceful shutdown
_shutdown_requested = False


def signal_handler(signum, frame):
    """
    Handle shutdown signals gracefully.
    
    Args:
        signum: Signal number received
        frame: Current stack frame
    """
    global _shutdown_requested
    _shutdown_requested = True
    
    logger = get_logger()
    signal_name = signal.Signals(signum).name
    logger.info(f"Received signal {signal_name} ({signum}), shutting down gracefully...")
    sys.exit(0)


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Speedtest Monitor - Monitor internet speed with Telegram notifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  speedtest-monitor
  speedtest-monitor --config /etc/speedtest/config.yaml
  speedtest-monitor --log-level DEBUG
  speedtest-monitor --version
        """
    )
    
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help=f"Path to configuration file (default: {DEFAULT_CONFIG_PATH})"
    )
    
    parser.add_argument(
        "--log-level",
        "-l",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help=f"Override logging level (default: {DEFAULT_LOG_LEVEL})"
    )
    
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"Speedtest Monitor v{__version__}"
    )
    
    return parser.parse_args()


def determine_config_path(args_config=None):
    """
    Determine the configuration file path.
    
    Priority:
    1. Command line argument (--config)
    2. Environment variable (CONFIG_PATH)
    3. Current directory (config.yaml)
    4. Package directory (../config.yaml)
    
    Args:
        args_config: Config path from command line arguments
        
    Returns:
        Path: Path to configuration file
        
    Raises:
        FileNotFoundError: If configuration file not found
    """
    # Check command line argument
    if args_config:
        config_path = Path(args_config)
        if config_path.exists():
            return config_path
        raise FileNotFoundError(f"Configuration file not found: {args_config}")
    
    # Check environment variable
    env_config = os.getenv("CONFIG_PATH")
    if env_config:
        config_path = Path(env_config)
        if config_path.exists():
            return config_path
    
    # Check current directory
    config_path = Path(DEFAULT_CONFIG_PATH)
    if config_path.exists():
        return config_path
    
    # Check package directory
    config_path = Path(__file__).parent.parent / DEFAULT_CONFIG_PATH
    if config_path.exists():
        return config_path
    
    raise FileNotFoundError(
        f"Configuration file not found. Searched locations:\n"
        f"  - Command line argument\n"
        f"  - CONFIG_PATH environment variable\n"
        f"  - Current directory: {Path.cwd() / DEFAULT_CONFIG_PATH}\n"
        f"  - Package directory: {Path(__file__).parent.parent / DEFAULT_CONFIG_PATH}"
    )


def run_master(config, logger):
    """
    Run the application in master mode.
    
    Args:
        config: Application configuration
        logger: Logger instance
    """
    logger.info("Starting Master mode...")
    
    if not config.master:
        logger.error("Master configuration is missing in config.yaml")
        return

    # Initialize Aggregator
    aggregator = Aggregator(config)
    logger.info("Aggregator initialized")
    
    # Initialize Notifier
    notifier = TelegramNotifier(config, aggregator=aggregator)

    # Initialize and run API Server
    api_server = APIServer(config, aggregator, notifier)
    
    try:
        api_server.run()
    except Exception as e:
        logger.error(f"Master server failed: {e}")
        raise


def run_node(config, logger):
    """
    Run the application in node mode.
    
    Args:
        config: Application configuration
        logger: Logger instance
    """
    logger.info(f"Starting Node mode (ID: {config.node.node_id})...")
    
    if not config.node or not config.node.node_id:
        logger.error("Node ID is not configured")
        return

    # 1. Run Speedtest
    logger.info("Running speedtest...")
    runner = SpeedtestRunner(config.speedtest)
    runner_result = runner.run()
    
    # 2. Prepare data
    sys_info = get_system_info()
    os_info = f"{sys_info['os']} {sys_info['os_version']}"
    
    # Determine status
    status = "failed"
    if runner_result.success:
        dl = runner_result.download_mbps
        if dl >= config.thresholds.good:
            status = "excellent"
        elif dl >= config.thresholds.medium:
            status = "good"
        elif dl >= config.thresholds.low:
            status = "normal"
        elif dl >= config.thresholds.very_low:
            status = "low"
        else:
            status = "very_low"
    else:
        status = "failed"

    # 3. Create Model Object
    model_result = ModelSpeedtestResult(
        node_id=config.node.node_id,
        timestamp=datetime.now(),
        download_mbps=runner_result.download_mbps,
        upload_mbps=runner_result.upload_mbps,
        ping_ms=runner_result.ping_ms,
        status=status,
        test_server=f"{runner_result.server_name} ({runner_result.server_location})",
        isp=runner_result.isp,
        os_info=os_info
    )
    
    # 4. Send to Master
    logger.info("Sending result to master...")
    success = asyncio.run(send_result_to_master(model_result, config))
    
    if success:
        logger.info("Node cycle completed successfully")
    else:
        logger.warning("Node cycle completed with errors (failed to send report)")


def main():
    """
    Main execution function.

    Loads configuration, runs speedtest, and sends notification.
    
    Exit codes:
        0: Success
        1: Fatal error (configuration, network, etc.)
        2: Speedtest failed but notification sent
    """
    runner = None
    notifier = None
    logger = None
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Determine config path
        config_path = determine_config_path(args.config)
        
        # Load and validate configuration
        config = load_config(config_path)
        validate_config(config)
        
        # Register signal handlers for graceful shutdown (ONLY for Node/Single mode)
        # Master mode (aiohttp) handles signals internally to ensure proper cleanup.
        if config.mode != "master":
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        
        # Override log level if specified
        log_level = args.log_level or config.logging.level
        
        # Setup logging
        log_file = Path(config.logging.file)
        setup_logger(
            log_level=log_level,
            log_file=log_file,
            rotation=config.logging.rotation,
            retention=config.logging.retention,
        )
        
        logger = get_logger()
        logger.info("=" * 60)
        logger.info(f"Speedtest Monitor v{__version__} started")
        logger.info(f"Configuration: {config_path.absolute()}")
        logger.info(f"Log level: {log_level}")
        logger.info(f"Mode: {config.mode}")
        logger.info("=" * 60)
        
        # Check for shutdown signal
        if _shutdown_requested:
            logger.info("Shutdown requested before speedtest execution")
            return 0

        # Dispatch based on mode
        if config.mode == "master":
            run_master(config, logger)
            return 0
        elif config.mode == "node":
            run_node(config, logger)
            return 0
        
        # Initialize components (Single mode)
        runner = SpeedtestRunner(config.speedtest)
        notifier = TelegramNotifier(config)
        
        # Run speedtest
        logger.info("Starting speedtest...")
        result = runner.run()
        
        # Check for shutdown signal
        if _shutdown_requested:
            logger.info("Shutdown requested after speedtest execution")
            return 0
        
        # Send notification
        logger.info("Sending Telegram notification...")
        success = notifier.send_notification_sync(result)
        
        if success:
            logger.info("Speedtest monitor completed successfully")
            logger.info("=" * 60)
            return 0
        else:
            logger.warning("Notification was not sent")
            logger.info("=" * 60)
            return 0  # Not a critical error
    
    except FileNotFoundError as e:
        # Configuration file not found
        if logger:
            logger.error(f"Configuration error: {e}")
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    
    except KeyboardInterrupt:
        # User interrupted
        if logger:
            logger.info("Interrupted by user")
        else:
            print("\nInterrupted by user", file=sys.stderr)
        return 0
    
    except Exception as e:
        # Fatal error
        if logger:
            logger.error(f"Fatal error: {e}", exc_info=True)
        else:
            print(f"FATAL ERROR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
        return 1
    
    finally:
        # Cleanup resources
        try:
            if notifier:
                # Close any open connections
                pass
            if runner:
                # Cleanup runner resources
                pass
            if logger:
                logger.info("Cleanup completed")
        except Exception as e:
            if logger:
                logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    sys.exit(main())
