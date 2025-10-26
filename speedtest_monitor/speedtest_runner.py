"""
Speedtest execution module.

Handles running speedtest and collecting results.
"""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .config import SpeedtestConfig
from .logger import get_logger

logger = get_logger()


@dataclass
class SpeedtestResult:
    """Result of a speedtest execution."""

    download_mbps: float
    upload_mbps: float
    ping_ms: float
    server_name: str
    server_location: str
    isp: str
    success: bool
    error_message: Optional[str] = None
    timestamp: Optional[str] = None


class SpeedtestRunner:
    """
    Runs speedtest and collects results.

    Automatically detects available speedtest commands and uses retry logic.
    """

    def __init__(self, config: SpeedtestConfig):
        """
        Initialize speedtest runner.

        Args:
            config: Speedtest configuration
        """
        self.config = config
        self.speedtest_commands = self._find_speedtest_commands()
        logger.info(f"Found speedtest commands: {self.speedtest_commands}")

    def _find_speedtest_commands(self) -> List[str]:
        """
        Find available speedtest commands on the system.

        Returns:
            List of available speedtest command paths

        Example:
            >>> runner = SpeedtestRunner(config)
            >>> commands = runner._find_speedtest_commands()
            >>> print(commands)
            ['/usr/bin/speedtest', '/usr/bin/speedtest-cli']
        """
        commands = []
        possible_locations = [
            "/usr/bin/speedtest",
            "/usr/local/bin/speedtest",
            "/opt/homebrew/bin/speedtest",
            "/snap/bin/speedtest",
            "/usr/bin/speedtest-cli",
            "/usr/local/bin/speedtest-cli",
        ]

        # Check known locations
        for location in possible_locations:
            if Path(location).exists():
                commands.append(location)

        # Try 'which' command
        for cmd in ["speedtest", "speedtest-cli"]:
            try:
                result = subprocess.run(
                    ["which", cmd],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path and path not in commands:
                        commands.append(path)
            except Exception:
                pass

        return commands

    def _parse_speedtest_output(
        self, output: str, command: str
    ) -> Optional[SpeedtestResult]:
        """
        Parse speedtest command output.

        Args:
            output: Command output text
            command: Command that was executed

        Returns:
            Parsed result or None if parsing failed
        """
        try:
            lines = output.strip().split("\n")
            result_data = {}

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Parse different output formats
                if "Download:" in line or "download:" in line.lower():
                    parts = line.split(":")
                    if len(parts) >= 2:
                        speed_str = parts[1].strip().split()[0]
                        result_data["download"] = float(speed_str)

                elif "Upload:" in line or "upload:" in line.lower():
                    parts = line.split(":")
                    if len(parts) >= 2:
                        speed_str = parts[1].strip().split()[0]
                        result_data["upload"] = float(speed_str)

                elif "Latency:" in line or "ping:" in line.lower():
                    parts = line.split(":")
                    if len(parts) >= 2:
                        ping_str = parts[1].strip().split()[0]
                        result_data["ping"] = float(ping_str)

                elif "Server:" in line:
                    parts = line.split(":", 1)
                    if len(parts) >= 2:
                        result_data["server"] = parts[1].strip()

                elif "ISP:" in line:
                    parts = line.split(":", 1)
                    if len(parts) >= 2:
                        result_data["isp"] = parts[1].strip()

            # Validate we have essential data
            if "download" in result_data and "upload" in result_data:
                return SpeedtestResult(
                    download_mbps=result_data.get("download", 0.0),
                    upload_mbps=result_data.get("upload", 0.0),
                    ping_ms=result_data.get("ping", 0.0),
                    server_name=result_data.get("server", "Unknown"),
                    server_location=result_data.get("server", "Unknown"),
                    isp=result_data.get("isp", "Unknown"),
                    success=True,
                )

            return None
        except Exception as e:
            logger.error(f"Error parsing speedtest output: {e}")
            return None

    def run(self) -> SpeedtestResult:
        """
        Execute speedtest with retry logic.

        Returns:
            Speedtest result

        Raises:
            RuntimeError: If all retry attempts fail

        Example:
            >>> runner = SpeedtestRunner(config)
            >>> result = runner.run()
            >>> print(f"Download: {result.download_mbps} Mbps")
        """
        if not self.speedtest_commands:
            error_msg = "No speedtest command found. Please install speedtest-cli or official speedtest"
            logger.error(error_msg)
            return SpeedtestResult(
                download_mbps=0.0,
                upload_mbps=0.0,
                ping_ms=0.0,
                server_name="",
                server_location="",
                isp="",
                success=False,
                error_message=error_msg,
            )

        last_error = None

        for attempt in range(self.config.retry_count):
            for command in self.speedtest_commands:
                try:
                    logger.info(
                        f"Running speedtest (attempt {attempt + 1}/{self.config.retry_count}) with {command}"
                    )

                    # Build command
                    cmd = [command]

                    # Add server IDs if specified
                    if self.config.servers:
                        if "speedtest-cli" in command:
                            cmd.extend(["--server", str(self.config.servers[0])])
                        else:
                            cmd.extend(["--server-id", str(self.config.servers[0])])

                    # Add JSON output if supported
                    if "speedtest-cli" not in command:
                        cmd.append("--format=human-readable")

                    # Execute command
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=self.config.timeout,
                    )

                    if result.returncode == 0:
                        parsed = self._parse_speedtest_output(result.stdout, command)
                        if parsed:
                            logger.info(
                                f"Speedtest successful: Download={parsed.download_mbps:.2f} Mbps, "
                                f"Upload={parsed.upload_mbps:.2f} Mbps, Ping={parsed.ping_ms:.2f} ms"
                            )
                            return parsed
                        else:
                            logger.warning(f"Failed to parse speedtest output")
                    else:
                        logger.warning(
                            f"Speedtest command failed with code {result.returncode}: {result.stderr}"
                        )
                        last_error = result.stderr

                except subprocess.TimeoutExpired:
                    logger.warning(f"Speedtest command timed out after {self.config.timeout}s")
                    last_error = "Timeout"
                except Exception as e:
                    logger.error(f"Error running speedtest: {e}")
                    last_error = str(e)

            # Wait before retry
            if attempt < self.config.retry_count - 1:
                logger.info(f"Waiting {self.config.retry_delay}s before retry...")
                time.sleep(self.config.retry_delay)

        # All attempts failed
        error_msg = f"All speedtest attempts failed. Last error: {last_error}"
        logger.error(error_msg)
        return SpeedtestResult(
            download_mbps=0.0,
            upload_mbps=0.0,
            ping_ms=0.0,
            server_name="",
            server_location="",
            isp="",
            success=False,
            error_message=error_msg,
        )
