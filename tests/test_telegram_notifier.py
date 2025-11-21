"""
Tests for Telegram notifier.
"""

import pytest
from speedtest_monitor.telegram_notifier import TelegramNotifier
from speedtest_monitor.speedtest_runner import SpeedtestResult
from speedtest_monitor.config import Config


def test_format_message_success():
    """Test formatting successful speedtest message."""
    # Create mock config
    # Create mock result
    # Test message formatting
    pass


def test_format_message_error():
    """Test formatting error message."""
    result = SpeedtestResult(
        download_mbps=0.0,
        upload_mbps=0.0,
        ping_ms=0.0,
        server_name="",
        server_location="",
        isp="",
        success=False,
        error_message="Test error",
    )
    # Test error message formatting
    pass


def test_should_send_notification():
    """Test notification send logic."""
    # Test send_always = True
    # Test speed below threshold
    # Test speed above threshold
    pass


@pytest.mark.asyncio
async def test_send_notification_async():
    """Test async notification sending."""
    # Mock telegram bot
    # Test successful send
    # Test retry logic
    pass
