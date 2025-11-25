"""
Tests for the View Renderer module.
"""

import pytest
from datetime import datetime
from speedtest_monitor.models import AggregatedReport, NodeAggregatedStatus, NodeDisplayMeta, SpeedtestResult
from speedtest_monitor.view_renderer import render_compact, render_detailed

@pytest.fixture
def sample_report():
    now = datetime.now()
    nodes = [
        NodeAggregatedStatus(
            meta=NodeDisplayMeta(node_id="node1", flag="🇺🇸", display_name="USA Node"),
            last_result=SpeedtestResult(
                node_id="node1", timestamp=now, download_mbps=100.5, upload_mbps=50.2, ping_ms=10.5,
                status="good", test_server="Server NY", isp="ISP Inc", os_info="Linux"
            ),
            is_online=True,
            derived_status="ok"
        ),
        NodeAggregatedStatus(
            meta=NodeDisplayMeta(node_id="node2", flag="🇩🇪", display_name="DE Node"),
            last_result=None,
            is_online=False,
            derived_status="offline"
        )
    ]
    return AggregatedReport(
        generated_at=now,
        nodes=nodes,
        summary={"ok": 1, "offline": 1}
    )

def test_render_compact_en(sample_report):
    """Test compact rendering in English."""
    text = render_compact(sample_report, "en")
    
    assert "Internet Speed Report" in text
    assert "USA Node" in text
    assert "100 / 50 Mbps" in text
    assert "Good" in text
    assert "DE Node" in text
    assert "offline" in text

def test_render_compact_ru(sample_report):
    """Test compact rendering in Russian."""
    text = render_compact(sample_report, "ru")
    
    assert "Отчет о скорости интернета" in text
    assert "Хорошо" in text
    assert "Нет данных" in text # offline text

def test_render_detailed_en(sample_report):
    """Test detailed rendering in English."""
    text = render_detailed(sample_report, "en")
    
    assert "Internet Speed Report" in text
    assert "Download: 100 Mbps" in text
    assert "Upload: 50 Mbps" in text
    assert "Ping: 10.5 ms" in text
    assert "Server: Server NY" in text
    assert "ISP: ISP Inc" in text
    assert "OS: Linux" in text
    assert "No data" in text

def test_render_detailed_ru(sample_report):
    """Test detailed rendering in Russian."""
    text = render_detailed(sample_report, "ru")
    
    assert "Отчет о скорости интернета" in text
    assert "Загрузка: 100 Mbps" in text
    assert "Отдача: 50 Mbps" in text
    assert "Пинг: 10.5 ms" in text
    assert "Тестовый сервер: Server NY" in text
    assert "Провайдер: ISP Inc" in text
    assert "ОС: Linux" in text
    assert "Нет данных" in text
