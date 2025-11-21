"""
Tests for speedtest runner.
"""

import pytest
from speedtest_monitor.speedtest_runner import SpeedtestRunner, SpeedtestResult
from speedtest_monitor.config import SpeedtestConfig


def test_speedtest_result_creation():
    """Test creating SpeedtestResult."""
    result = SpeedtestResult(
        download_mbps=100.0,
        upload_mbps=50.0,
        ping_ms=20.0,
        server_name="Test Server",
        server_location="Test Location",
        isp="Test ISP",
        success=True,
    )
    assert result.download_mbps == 100.0
    assert result.success is True


def test_parse_json_output():
    """Test parsing JSON speedtest output."""
    # Mock JSON output from official speedtest
    json_output = '''
    {
        "download": {"bandwidth": 125000000},
        "upload": {"bandwidth": 62500000},
        "ping": {"latency": 15.5},
        "server": {"name": "Test", "location": "NYC"},
        "isp": "Test ISP"
    }
    '''
    # Test parsing logic
    pass


def test_parse_text_output():
    """Test parsing text speedtest output."""
    text_output = '''
    Download: 100.5 Mbit/s
    Upload: 50.2 Mbit/s
    Ping: 20.3 ms
    '''
    # Test parsing logic
    pass


def test_speedtest_runner_init():
    """Test SpeedtestRunner initialization."""
    config = SpeedtestConfig()
    runner = SpeedtestRunner(config)
    assert runner.config == config
    assert isinstance(runner.speedtest_commands, list)
