"""
Node client module.

Handles sending speedtest results to the master server.
"""

import asyncio
from dataclasses import asdict

import aiohttp

from speedtest_monitor.config import Config
from speedtest_monitor.logger import get_logger
from speedtest_monitor.models import NodeReportPayload, SpeedtestResult

logger = get_logger()


async def send_result_to_master(result: SpeedtestResult, config: Config) -> bool:
    """
    Send speedtest result to the master server.

    Args:
        result: The speedtest result to send.
        config: Application configuration.

    Returns:
        True if successful, False otherwise.
    """
    if not config.node:
        logger.error("Node configuration missing")
        return False
    
    if not config.node.master_url:
        logger.error("Master URL is not configured")
        return False

    # Create payload
    payload = NodeReportPayload(
        node_id=result.node_id,
        timestamp=result.timestamp,
        download_mbps=result.download_mbps,
        upload_mbps=result.upload_mbps,
        ping_ms=result.ping_ms,
        status=result.status,
        test_server=result.test_server,
        isp=result.isp,
        os_info=result.os_info,
        description=result.description
    )
    
    url = config.node.master_url
    headers = {
        "Authorization": f"Bearer {config.node.api_token}",
        "Content-Type": "application/json"
    }
    
    # Prepare JSON data
    data = asdict(payload)
    data["timestamp"] = payload.timestamp.isoformat()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers, timeout=30) as response:
                if response.status == 200:
                    logger.info(f"Successfully sent report to master: {url}")
                    return True
                else:
                    text = await response.text()
                    logger.error(f"Failed to send report. Status: {response.status}, Response: {text}")
                    return False
    except Exception as e:
        logger.error(f"Error sending report to master: {e}")
        return False
