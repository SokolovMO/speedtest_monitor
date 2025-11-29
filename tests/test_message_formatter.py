import unittest
from datetime import datetime
from speedtest_monitor.message_formatter import MessageFormatter
from speedtest_monitor.speedtest_runner import SpeedtestResult as RunnerResult
from speedtest_monitor.models import SpeedtestResult as ModelResult, AggregatedReport, NodeDisplayMeta, NodeAggregatedStatus

class TestMessageFormatter(unittest.TestCase):
    def test_single_mode_detailed(self):
        res = RunnerResult(
            download_mbps=850.5,
            upload_mbps=920.1,
            ping_ms=4.2,
            server_name="Test Server",
            server_location="Moscow",
            isp="TestProvider",
            success=True,
            timestamp=datetime.now().isoformat()
        )
        server_info = {
            "name": "MyServer",
            "location": "Home",
            "id": "srv-01",
            "description": "Main Server"
        }
        msg = MessageFormatter.format_single_result(
            res, style="detailed", lang="ru", server_info=server_info, status_key="good"
        )
        self.assertIn("📊 Отчет о скорости интернета", msg)
        self.assertIn("MyServer", msg)
        self.assertIn("850.50 Mbps", msg)
        self.assertIn("Хорошо", msg)

    def test_single_mode_error(self):
        err_res = RunnerResult(
            download_mbps=0,
            upload_mbps=0,
            ping_ms=0,
            server_name="",
            server_location="",
            isp="",
            success=False,
            error_message="Cannot retrieve configuration: 403 Forbidden"
        )
        server_info = {"name": "MyServer"}
        msg = MessageFormatter.format_single_result(
            err_res, style="detailed", lang="ru", server_info=server_info
        )
        self.assertIn("Ошибка", msg)
        self.assertIn("403 Forbidden", msg)
        self.assertIn("MyServer", msg)

    def test_master_mode_compact(self):
        node1 = NodeAggregatedStatus(
            meta=NodeDisplayMeta(node_id="node1", display_name="Node 1", flag="🇷🇺"),
            is_online=True,
            last_result=ModelResult(
                node_id="node1",
                timestamp=datetime.now(),
                download_mbps=500,
                upload_mbps=500,
                ping_ms=10,
                status="good",
                test_server="Srv1",
                isp="ISP1",
                os_info="Linux"
            ),
            derived_status="ok"
        )
        
        report = AggregatedReport(
            generated_at=datetime.now(),
            nodes=[node1],
            summary={}
        )
        
        msg = MessageFormatter.format_master_report(report, style="compact", lang="ru")
        self.assertIn("Node 1", msg)
        self.assertIn("500", msg)
        self.assertIn("Хорошо", msg)

if __name__ == "__main__":
    unittest.main()
