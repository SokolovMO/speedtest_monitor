"""
Data models for speedtest monitor (v2 architecture).

This module defines the data structures used for:
- Node-side speedtest results
- API payloads between node and master
- Master-side aggregation and reporting
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class SpeedtestResult:
    """
    Internal representation of a speedtest result.
    Used by the node to store local results and by the master to store received results.
    """
    node_id: str
    timestamp: datetime
    download_mbps: float
    upload_mbps: float
    ping_ms: float
    status: str  # "excellent" | "good" | "degraded" | "failed" | "no_data"
    test_server: str
    isp: str
    os_info: str


@dataclass
class NodeReportPayload:
    """
    Data payload sent from node to master via API.
    Matches the JSON structure expected by the master's /api/v1/report endpoint.
    """
    node_id: str
    timestamp: datetime
    download_mbps: float
    upload_mbps: float
    ping_ms: float
    status: str
    test_server: str
    isp: str
    os_info: str


@dataclass
class NodeDisplayMeta:
    """
    Metadata for displaying a node in reports.
    Loaded from master configuration.
    """
    node_id: str
    flag: Optional[str] = None
    display_name: Optional[str] = None


@dataclass
class NodeAggregatedStatus:
    """
    Combined status of a node including metadata, last result, and derived state.
    Used during the aggregation process.
    """
    meta: NodeDisplayMeta
    last_result: Optional[SpeedtestResult]
    is_online: bool
    derived_status: str  # "ok" | "degraded" | "offline"


@dataclass
class AggregatedReport:
    """
    Final report containing all node statuses and summary statistics.
    Passed to the view renderer to generate Telegram messages.
    """
    generated_at: datetime
    nodes: List[NodeAggregatedStatus]
    summary: Dict[str, int]  # e.g. {"ok": 4, "degraded": 1, "offline": 1}
