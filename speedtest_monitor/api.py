"""
HTTP API module for Master mode.

Handles incoming reports from nodes.
"""

import asyncio
import json
from datetime import datetime

from aiohttp import web

from speedtest_monitor.aggregator import Aggregator
from speedtest_monitor.config import Config
from speedtest_monitor.logger import get_logger
from speedtest_monitor.models import NodeReportPayload, SpeedtestResult
from speedtest_monitor.telegram_notifier import TelegramNotifier

logger = get_logger()


class APIServer:
    """
    HTTP API Server for receiving node reports.
    """

    def __init__(self, config: Config, aggregator: Aggregator, notifier: TelegramNotifier):
        """
        Initialize the API server.

        Args:
            config: Application configuration.
            aggregator: Aggregator instance to store results.
            notifier: TelegramNotifier instance for sending reports.
        """
        self.config = config
        self.aggregator = aggregator
        self.notifier = notifier
        self.app = web.Application()
        self.setup_routes()
        
        # Background tasks
        self.app.on_startup.append(self.start_background_tasks)
        self.app.on_cleanup.append(self.cleanup_background_tasks)
        self.scheduler_task = None

    def setup_routes(self):
        """Define API routes."""
        self.app.router.add_post("/api/v1/report", self.handle_report)

    async def start_background_tasks(self, app):
        """Start background tasks on app startup."""
        self.scheduler_task = asyncio.create_task(self.scheduler_loop())
        logger.info("Scheduler task started")
        
        # Start Telegram polling
        self.polling_task = asyncio.create_task(self.notifier.start_polling())
        logger.info("Telegram polling started")

    async def cleanup_background_tasks(self, app):
        """Cleanup background tasks on app shutdown."""
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        if hasattr(self, 'polling_task') and self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Background tasks stopped")

    async def scheduler_loop(self):
        """
        Periodic task to build and send aggregated reports.
        """
        if not self.config.master:
            return

        interval = self.config.master.aggregation_interval_minutes * 60
        logger.info(f"Scheduler started. Interval: {self.config.master.aggregation_interval_minutes} minutes")

        while True:
            try:
                # Wait for the interval
                await asyncio.sleep(interval)
                
                logger.info("Building aggregated report...")
                report = self.aggregator.build_report()
                
                logger.info("Sending aggregated report...")
                await self.notifier.send_aggregated_report(report)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Wait a bit before retrying to avoid tight loops on error
                await asyncio.sleep(60)

    async def handle_report(self, request: web.Request) -> web.Response:
        """
        Handle POST /api/v1/report.
        Validates token, parses JSON, updates aggregator.
        """
        # 1. Authorization check
        auth_header = request.headers.get("Authorization")
        if not self.config.master:
            return web.Response(status=500, text="Master configuration missing")

        expected_token = f"Bearer {self.config.master.api_token}"
        if not auth_header or auth_header != expected_token:
            logger.warning(f"Unauthorized access attempt from {request.remote}")
            return web.Response(status=401, text="Unauthorized")

        # 2. Parse and Validate JSON
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.Response(status=400, text="Invalid JSON")

        try:
            # Handle timestamp conversion (ISO format expected)
            if "timestamp" in data and isinstance(data["timestamp"], str):
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])

            # Create payload object (validates fields via dataclass/init)
            # Note: dataclass doesn't strictly validate types at runtime on init, 
            # but missing keys will raise TypeError if not optional.
            # We assume the node sends correct fields.
            payload = NodeReportPayload(**data)

            # 3. Convert to SpeedtestResult
            result = SpeedtestResult(
                node_id=payload.node_id,
                timestamp=payload.timestamp,
                download_mbps=payload.download_mbps,
                upload_mbps=payload.upload_mbps,
                ping_ms=payload.ping_ms,
                status=payload.status,
                test_server=payload.test_server,
                isp=payload.isp,
                os_info=payload.os_info,
            )

            # 4. Update Aggregator
            self.aggregator.update_node_result(result)
            logger.info(f"Received report from node '{result.node_id}'")

            return web.Response(text="OK")

        except (TypeError, ValueError, KeyError) as e:
            logger.error(f"Invalid report payload: {e}")
            return web.Response(status=400, text=f"Bad Request: {str(e)}")
        except Exception as e:
            logger.error(f"Internal error processing report: {e}")
            return web.Response(status=500, text="Internal Server Error")

    def run(self):
        """Start the HTTP server (blocking)."""
        if not self.config.master:
            logger.error("Cannot start API server: Master config missing")
            return

        host = self.config.master.listen_host
        port = self.config.master.listen_port
        logger.info(f"Starting Master API server on {host}:{port}")
        
        # web.run_app is blocking, suitable for this stage
        web.run_app(self.app, host=host, port=port, print=None)
