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
from speedtest_monitor.speedtest_runner import SpeedtestRunner
from speedtest_monitor.utils import get_system_info
from speedtest_monitor.models import SpeedtestResult as ModelSpeedtestResult

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
        self.master_speedtest_task = None

    def setup_routes(self):
        """Define API routes."""
        self.app.router.add_post("/api/v1/report", self.handle_report)
        self.app.router.add_get("/health", self.health_check)

    async def health_check(self, request: web.Request) -> web.Response:
        """
        Health check endpoint.
        Returns status and current mode.
        """
        return web.json_response({
            "status": "ok",
            "mode": "master",
            "version": "1.0.0"  # Ideally import __version__ from main or init
        })

    async def start_background_tasks(self, app):
        """Start background tasks on app startup."""
        # Only start scheduler if NOT sending immediately
        if self.config.master and not self.config.master.schedule.send_immediately:
            self.scheduler_task = asyncio.create_task(self.scheduler_loop())
            logger.info("Scheduler task started")
        else:
            logger.info("Scheduler task skipped (send_immediately=True)")
        
        # Start Telegram polling
        self.polling_task = asyncio.create_task(self.notifier.start_polling())
        logger.info("Telegram polling started")
        
        # Start Master Speedtest Loop (if configured)
        # We check if master should run speedtests. 
        # We can assume if it's master, it might want to report itself.
        # Let's check if there is a node_id in config.master.nodes_meta that corresponds to "master" or similar?
        # Or we can just check if we have a node_id configured in 'node' section even if mode is master?
        # Or we can add a specific flag.
        # For now, let's assume if 'node' section is present and valid, we run it.
        if self.config.node and self.config.node.node_id:
             self.master_speedtest_task = asyncio.create_task(self.master_speedtest_loop())
             logger.info(f"Master speedtest loop started for node_id: {self.config.node.node_id}")

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

        if self.master_speedtest_task:
            self.master_speedtest_task.cancel()
            try:
                await self.master_speedtest_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Background tasks stopped")

    async def master_speedtest_loop(self):
        """
        Periodic task to run speedtest on the master server itself.
        """
        # Use the same interval as the scheduler or a default one?
        # Ideally it should match the reporting interval or be configurable.
        # Let's use master.schedule.interval_minutes for now.
        interval = self.config.master.schedule.interval_minutes * 60
        if interval < 300: # Minimum 5 minutes to avoid overload if interval is short
             interval = 300
             
        logger.info(f"Master speedtest loop started. Interval: {interval} seconds")

        while True:
            try:
                logger.info("Running master speedtest...")
                
                # Run speedtest in a thread executor to avoid blocking the event loop
                loop = asyncio.get_running_loop()
                runner = SpeedtestRunner(self.config.speedtest)
                runner_result = await loop.run_in_executor(None, runner.run)
                
                # Prepare data
                sys_info = get_system_info()
                os_info = f"{sys_info['os']} {sys_info['os_version']}"
                
                # Determine status
                status = "failed"
                if runner_result.success:
                    dl = runner_result.download_mbps
                    if dl >= self.config.thresholds.good:
                        status = "excellent"
                    elif dl >= self.config.thresholds.medium:
                        status = "good"
                    elif dl >= self.config.thresholds.low:
                        status = "degraded"
                    else:
                        status = "degraded"
                
                # Create Model Object
                model_result = ModelSpeedtestResult(
                    node_id=self.config.node.node_id,
                    timestamp=datetime.now(),
                    download_mbps=runner_result.download_mbps,
                    upload_mbps=runner_result.upload_mbps,
                    ping_ms=runner_result.ping_ms,
                    status=status,
                    test_server=f"{runner_result.server_name} ({runner_result.server_location})",
                    isp=runner_result.isp,
                    os_info=os_info,
                    description=self.config.server.description if hasattr(self.config, "server") else None
                )
                
                # Update Aggregator directly
                self.aggregator.update_node_result(model_result)
                logger.info(f"Master speedtest completed and aggregated for node '{self.config.node.node_id}'")
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in master speedtest loop: {e}")
                await asyncio.sleep(60)

    async def scheduler_loop(self):
        """
        Periodic task to build and send aggregated reports.
        """
        if not self.config.master:
            return

        # Use schedule.interval_minutes
        interval_minutes = self.config.master.schedule.interval_minutes
        interval = interval_minutes * 60
        
        logger.info(f"Scheduler started. Interval: {interval_minutes} minutes")
        
        # Log configuration
        logger.info(f"Mode: master")
        logger.info(f"Send immediately: {self.config.master.schedule.send_immediately}")
        logger.info(f"Interval: {interval_minutes} minutes")

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
                description=payload.description
            )

            # 4. Update Aggregator
            self.aggregator.update_node_result(result)
            logger.info(f"Received report from node '{result.node_id}'")
            
            # 5. Send immediately if configured
            if self.config.master.schedule.send_immediately:
                logger.info("Sending immediate aggregated report...")
                report = self.aggregator.build_report()
                # Fire and forget (or await? handle_report is async)
                # We should await it to ensure it's sent, but it might slow down the response to the node.
                # Since this is "immediate", awaiting is fine.
                asyncio.create_task(self.notifier.send_aggregated_report(report))
            else:
                logger.debug("Report queued for next aggregation cycle")

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
