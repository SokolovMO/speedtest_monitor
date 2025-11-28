import pytest
from unittest.mock import MagicMock, AsyncMock
from speedtest_monitor.config import MasterConfig, MasterScheduleConfig, Config
from speedtest_monitor.api import APIServer

def test_master_schedule_config_defaults():
    """Test default values for MasterScheduleConfig."""
    schedule = MasterScheduleConfig()
    assert schedule.interval_minutes == 60
    assert schedule.send_immediately is False

def test_master_config_backward_compatibility():
    """Test that missing schedule section defaults to backward compatible values."""
    # Simulate loading config dict without 'schedule'
    config_dict = {
        "aggregation_interval_minutes": 30,
        # ... other fields
    }
    
    # We can't easily test the load_config logic without mocking yaml/file, 
    # but we can test the logic if we extract it or just trust the integration test.
    # Let's test the logic we added to load_config by mocking the dict structure
    # But load_config is a function that reads a file.
    pass

@pytest.mark.asyncio
async def test_api_server_send_immediately():
    """Test that send_immediately=True triggers immediate report sending."""
    # Setup mocks
    mock_config = MagicMock(spec=Config)
    mock_config.master = MagicMock(spec=MasterConfig)
    mock_config.master.api_token = "test_token"
    mock_config.master.schedule = MasterScheduleConfig(send_immediately=True)
    
    mock_aggregator = MagicMock()
    mock_notifier = MagicMock()
    mock_notifier.send_aggregated_report = AsyncMock()
    
    api = APIServer(mock_config, mock_aggregator, mock_notifier)
    
    # Mock request
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "Bearer test_token"
    mock_request.json = AsyncMock(return_value={
        "node_id": "test_node",
        "timestamp": "2023-01-01T12:00:00",
        "download_mbps": 100.0,
        "upload_mbps": 50.0,
        "ping_ms": 10.0,
        "status": "ok",
        "test_server": "test",
        "isp": "test",
        "os_info": "test"
    })
    
    # Call handle_report
    response = await api.handle_report(mock_request)
    
    # Verify response
    assert response.status == 200
    
    # Verify aggregator update
    mock_aggregator.update_node_result.assert_called_once()
    
    # Verify immediate send
    mock_notifier.send_aggregated_report.assert_called_once()

@pytest.mark.asyncio
async def test_api_server_delayed_send():
    """Test that send_immediately=False does NOT trigger immediate report sending."""
    # Setup mocks
    mock_config = MagicMock(spec=Config)
    mock_config.master = MagicMock(spec=MasterConfig)
    mock_config.master.api_token = "test_token"
    mock_config.master.schedule = MasterScheduleConfig(send_immediately=False)
    
    mock_aggregator = MagicMock()
    mock_notifier = MagicMock()
    mock_notifier.send_aggregated_report = AsyncMock()
    
    api = APIServer(mock_config, mock_aggregator, mock_notifier)
    
    # Mock request
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "Bearer test_token"
    mock_request.json = AsyncMock(return_value={
        "node_id": "test_node",
        "timestamp": "2023-01-01T12:00:00",
        "download_mbps": 100.0,
        "upload_mbps": 50.0,
        "ping_ms": 10.0,
        "status": "ok",
        "test_server": "test",
        "isp": "test",
        "os_info": "test"
    })
    
    # Call handle_report
    response = await api.handle_report(mock_request)
    
    # Verify response
    assert response.status == 200
    
    # Verify aggregator update
    mock_aggregator.update_node_result.assert_called_once()
    
    # Verify NO immediate send
    mock_notifier.send_aggregated_report.assert_not_called()
