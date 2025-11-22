"""
Speedtest execution module.

Handles running speedtest and collecting results.
"""

import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .config import SpeedtestConfig
from .constants import (
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_DELAY,
    DEFAULT_TIMEOUT,
    SPEEDTEST_COMMANDS,
)
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
        
        Supports multiple output formats:
        - Official Ookla speedtest JSON (--format=json)
        - Official Ookla speedtest human-readable
        - speedtest-cli plain text
        - speedtest-cli --simple format

        Args:
            output: Command output text
            command: Command that was executed

        Returns:
            Parsed result or None if parsing failed
        """
        try:
            # Try JSON format first (official speedtest with --format=json)
            if output.strip().startswith("{"):
                try:
                    data = json.loads(output)
                    # Official Ookla speedtest JSON format
                    if "download" in data and "bandwidth" in data.get("download", {}):
                        return SpeedtestResult(
                            download_mbps=data["download"]["bandwidth"] / 125000,  # bits to Mbps
                            upload_mbps=data["upload"]["bandwidth"] / 125000,
                            ping_ms=data.get("ping", {}).get("latency", 0),
                            server_name=data.get("server", {}).get("name", "Unknown"),
                            server_location=data.get("server", {}).get("location", "Unknown"),
                            isp=data.get("isp", "Unknown"),
                            success=True,
                        )
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.debug(f"Failed to parse as JSON: {e}")

            # Parse text output with regex patterns
            # Try speedtest-cli --simple format first (most structured)
            simple_match = re.search(
                r"Ping:\s+([\d.]+)\s+ms.*?Download:\s+([\d.]+)\s+Mbit/s.*?Upload:\s+([\d.]+)\s+Mbit/s",
                output,
                re.DOTALL | re.IGNORECASE,
            )
            if simple_match:
                return SpeedtestResult(
                    download_mbps=float(simple_match.group(2)),
                    upload_mbps=float(simple_match.group(3)),
                    ping_ms=float(simple_match.group(1)),
                    server_name="Unknown",
                    server_location="Unknown",
                    isp="Unknown",
                    success=True,
                )

            # Parse human-readable format line by line
            lines = output.strip().split("\n")
            result_data = {}

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Match download speed (various formats)
                download_match = re.search(
                    r"(?:Download|download):\s+([\d.]+)\s+(?:Mbit/s|Mbps)",
                    line,
                    re.IGNORECASE,
                )
                if download_match:
                    result_data["download"] = float(download_match.group(1))

                # Match upload speed
                upload_match = re.search(
                    r"(?:Upload|upload):\s+([\d.]+)\s+(?:Mbit/s|Mbps)",
                    line,
                    re.IGNORECASE,
                )
                if upload_match:
                    result_data["upload"] = float(upload_match.group(1))

                # Match ping/latency
                ping_match = re.search(
                    r"(?:Latency|latency|Ping|ping):\s+([\d.]+)\s+ms",
                    line,
                    re.IGNORECASE,
                )
                if ping_match:
                    result_data["ping"] = float(ping_match.group(1))

                # Match server info
                if "Server:" in line:
                    parts = line.split(":", 1)
                    if len(parts) >= 2:
                        result_data["server"] = parts[1].strip()

                # Match ISP
                if "ISP:" in line:
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

            logger.warning("Could not extract download/upload speeds from output")
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

                    # Configure output format based on speedtest version
                    if "speedtest-cli" not in command:
                        # Official Ookla speedtest: check if --format=json is supported
                        # Some versions support JSON output, others only text format
                        try:
                            version_check = subprocess.run(
                                [command, "--version"],
                                capture_output=True,
                                text=True,
                                timeout=5,
                            )
                            version_output = version_check.stdout + version_check.stderr
                            # Versions with JSON support (typically 1.1.0+)
                            if "1.1" in version_output or "1.2" in version_output or "2." in version_output:
                                cmd.append("--format=json")
                            # Other versions use default text output (parsed by regex)
                        except Exception:
                            # If version check fails, use default text output
                            pass
                    else:
                        # speedtest-cli: use --simple for structured output
                        cmd.append("--simple")

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
