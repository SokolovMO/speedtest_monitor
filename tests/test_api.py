"""
Tests for the API module.
"""

import pytest
import json
from datetime import datetime
from aiohttp import web
from aiohttp.test_utils import TestClient
from unittest.mock import MagicMock

from speedtest_monitor.api import APIServer
from speedtest_monitor.config import Config, MasterConfig
from speedtest_monitor.aggregator import Aggregator
from speedtest_monitor.telegram_notifier import TelegramNotifier

@pytest.fixture
def mock_config():
    master_config = MasterConfig(api_token="secret-token")
    return Config(
        server=MagicMock(), speedtest=MagicMock(), thresholds=MagicMock(), telegram=MagicMock(), logging=MagicMock(),
        mode="master", master=master_config
    )

@pytest.fixture
def mock_aggregator():
    return MagicMock(spec=Aggregator)

@pytest.fixture
def mock_notifier():
    return MagicMock(spec=TelegramNotifier)

@pytest.fixture
def client(event_loop, aiohttp_client, mock_config, mock_aggregator, mock_notifier):
    api_server = APIServer(mock_config, mock_aggregator, mock_notifier)
    return event_loop.run_until_complete(aiohttp_client(api_server.app))

@pytest.mark.asyncio
async def test_report_endpoint_success(client, mock_aggregator):
    """Test successful report submission."""
    payload = {
        "node_id": "test-node",
        "timestamp": datetime.now().isoformat(),
        "download_mbps": 100.0,
        "upload_mbps": 50.0,
        "ping_ms": 10.0,
        "status": "good",
        "test_server": "Server",
        "isp": "ISP",
        "os_info": "Linux"
    }
    
    headers = {"Authorization": "Bearer secret-token"}
    resp = await client.post("/api/v1/report", json=payload, headers=headers)
    
    assert resp.status == 200
    assert await resp.text() == "OK"
    mock_aggregator.update_node_result.assert_called_once()

@pytest.mark.asyncio
async def test_report_endpoint_unauthorized(client):
    """Test unauthorized access."""
    payload = {}
    resp = await client.post("/api/v1/report", json=payload, headers={"Authorization": "Bearer wrong"})
    assert resp.status == 401

@pytest.mark.asyncio
async def test_report_endpoint_invalid_json(client):
    """Test invalid JSON payload."""
    headers = {"Authorization": "Bearer secret-token"}
    resp = await client.post("/api/v1/report", data="invalid-json", headers=headers)
    assert resp.status == 400

@pytest.mark.asyncio
async def test_report_endpoint_missing_fields(client):
    """Test payload with missing fields."""
    payload = {"node_id": "test"} # Missing other fields
    headers = {"Authorization": "Bearer secret-token"}
    resp = await client.post("/api/v1/report", json=payload, headers=headers)
    assert resp.status == 400
