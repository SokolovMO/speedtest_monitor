"""
Tests for the Aggregator module.
"""

import pytest
from datetime import datetime, timedelta
from speedtest_monitor.aggregator import Aggregator
from speedtest_monitor.config import Config, MasterConfig, NodeMetaConfig
from speedtest_monitor.models import SpeedtestResult

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    master_config = MasterConfig(
        node_timeout_minutes=60,
        nodes_order=["node1", "node2"],
        nodes_meta={
            "node1": NodeMetaConfig(flag="🇺🇸", display_name="Node 1"),
            "node2": NodeMetaConfig(flag="🇩🇪", display_name="Node 2"),
        }
    )
    # We need to mock the rest of Config as well since Aggregator expects it
    # But Aggregator only uses config.master
    from unittest.mock import MagicMock
    config = Config(
        server=MagicMock(),
        speedtest=MagicMock(),
        thresholds=MagicMock(),
        telegram=MagicMock(),
        logging=MagicMock(),
        mode="master",
        master=master_config
    )
    return config

@pytest.fixture
def aggregator(mock_config):
    return Aggregator(mock_config)

def test_update_node_result(aggregator):
    """Test updating node results."""
    result = SpeedtestResult(
        node_id="node1",
        timestamp=datetime.now(),
        download_mbps=100.0,
        upload_mbps=50.0,
        ping_ms=10.0,
        status="good",
        test_server="Server",
        isp="ISP",
        os_info="Linux"
    )
    aggregator.update_node_result(result)
    assert "node1" in aggregator.last_results
    assert aggregator.last_results["node1"] == result
    assert "node1" in aggregator.last_updated_at

def test_build_report_ordering(aggregator):
    """Test that nodes are ordered correctly in the report."""
    # Add results for node2 and node1 (reverse order)
    now = datetime.now()
    aggregator.update_node_result(SpeedtestResult(
        node_id="node2", timestamp=now, download_mbps=10, upload_mbps=10, ping_ms=10, status="good", test_server="S", isp="I", os_info="O"
    ))
    aggregator.update_node_result(SpeedtestResult(
        node_id="node1", timestamp=now, download_mbps=10, upload_mbps=10, ping_ms=10, status="good", test_server="S", isp="I", os_info="O"
    ))
    
    # Add unknown node
    aggregator.update_node_result(SpeedtestResult(
        node_id="node3", timestamp=now, download_mbps=10, upload_mbps=10, ping_ms=10, status="good", test_server="S", isp="I", os_info="O"
    ))

    report = aggregator.build_report()
    
    # Expected order: node1 (config), node2 (config), node3 (alphabetical)
    assert len(report.nodes) == 3
    assert report.nodes[0].meta.node_id == "node1"
    assert report.nodes[1].meta.node_id == "node2"
    assert report.nodes[2].meta.node_id == "node3"

def test_build_report_timeout(aggregator):
    """Test that timed out nodes are marked as offline."""
    now = datetime.now()
    old_time = now - timedelta(minutes=61) # Timeout is 60
    
    aggregator.update_node_result(SpeedtestResult(
        node_id="node1", timestamp=old_time, download_mbps=10, upload_mbps=10, ping_ms=10, status="good", test_server="S", isp="I", os_info="O"
    ))
    
    # Manually set update time to old
    aggregator.last_updated_at["node1"] = old_time
    
    report = aggregator.build_report()
    node_status = report.nodes[0]
    
    assert node_status.meta.node_id == "node1"
    assert node_status.is_online is False
    assert node_status.derived_status == "offline"
    assert report.summary["offline"] == 2 # node1 + node2 (which has no data)

def test_build_report_statuses(aggregator):
    """Test status derivation."""
    now = datetime.now()
    
    # Good -> ok
    aggregator.update_node_result(SpeedtestResult(
        node_id="node1", timestamp=now, download_mbps=100, upload_mbps=100, ping_ms=10, status="good", test_server="S", isp="I", os_info="O"
    ))
    
    # Degraded -> degraded
    aggregator.update_node_result(SpeedtestResult(
        node_id="node2", timestamp=now, download_mbps=10, upload_mbps=10, ping_ms=100, status="degraded", test_server="S", isp="I", os_info="O"
    ))
    
    report = aggregator.build_report()
    
    n1 = next(n for n in report.nodes if n.meta.node_id == "node1")
    n2 = next(n for n in report.nodes if n.meta.node_id == "node2")
    
    assert n1.derived_status == "ok"
    assert n2.derived_status == "degraded"
    assert report.summary["ok"] == 1
    assert report.summary["degraded"] == 1
