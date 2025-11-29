"""
Aggregator module for Master mode.

Responsible for:
- Storing latest results from nodes.
- Building aggregated reports based on configuration and timeouts.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from speedtest_monitor import get_logger
from speedtest_monitor.config import Config
from speedtest_monitor.models import (
    AggregatedReport,
    NodeAggregatedStatus,
    NodeDisplayMeta,
    SpeedtestResult,
)


class Aggregator:
    """
    Aggregates speedtest results from multiple nodes.
    """

    def __init__(self, config: Config):
        """
        Initialize the aggregator.

        Args:
            config: Application configuration (must have master section).
        """
        self.config = config
        self.last_results: Dict[str, SpeedtestResult] = {}
        self.last_updated_at: Dict[str, datetime] = {}
        self._logged_unknown_nodes = set()

    def update_node_result(self, result: SpeedtestResult) -> None:
        """
        Update the latest result for a specific node.

        Args:
            result: The speedtest result received from a node.
        """
        # Check if node is known in metadata
        if self.config.master and result.node_id not in self.config.master.nodes_meta:
            if result.node_id not in self._logged_unknown_nodes:
                logger = get_logger()
                logger.warning(
                    f'unknown node_id "{result.node_id}". please add to nodes_meta. suggested config:\n'
                    f'    {result.node_id}:\n'
                    f'      flag: "🏳️"\n'
                    f'      display_name: "Node {result.node_id}"'
                )
                self._logged_unknown_nodes.add(result.node_id)

        self.last_results[result.node_id] = result
        self.last_updated_at[result.node_id] = datetime.now()

    def build_report(self) -> AggregatedReport:
        """
        Build an aggregated report from current state.

        Returns:
            AggregatedReport containing status of all nodes.
        """
        if not self.config.master:
            # Should not happen if running in master mode
            return AggregatedReport(
                generated_at=datetime.now(), nodes=[], summary={}
            )

        nodes_status: List[NodeAggregatedStatus] = []
        summary = {"ok": 0, "degraded": 0, "offline": 0}
        
        # Determine the set of all known nodes (from config + received results)
        config_nodes = set(self.config.master.nodes_meta.keys())
        received_nodes = set(self.last_results.keys())
        all_node_ids = config_nodes.union(received_nodes)

        # Sort nodes: first by config order, then alphabetical for others
        ordered_nodes = []
        
        # 1. Add nodes from explicit order list
        for node_id in self.config.master.nodes_order:
            if node_id in all_node_ids:
                ordered_nodes.append(node_id)
        
        # 2. Add remaining nodes alphabetically
        remaining_nodes = sorted(list(all_node_ids - set(ordered_nodes)))
        ordered_nodes.extend(remaining_nodes)

        now = datetime.now()
        timeout_delta = timedelta(minutes=self.config.master.node_timeout_minutes)

        for node_id in ordered_nodes:
            # Get metadata
            meta_config = self.config.master.nodes_meta.get(node_id)
            display_meta = NodeDisplayMeta(
                node_id=node_id,
                flag=meta_config.flag if meta_config else None,
                display_name=meta_config.display_name if meta_config else None,
            )

            last_result = self.last_results.get(node_id)
            last_update = self.last_updated_at.get(node_id)
            
            is_online = False
            derived_status = "offline"

            if last_result and last_update:
                # Check timeout
                if now - last_update <= timeout_delta:
                    is_online = True
                    # Map speedtest status to aggregated status
                    if last_result.status in ["excellent", "good"]:
                        derived_status = "ok"
                    elif last_result.status == "degraded":
                        derived_status = "degraded"
                    else:
                        # failed, no_data, or unknown
                        derived_status = "offline" # Or maybe degraded? TDS says "offline if no data or timeout". 
                        # TDS also says: "else derive from SpeedtestResult.status (excellent/good/degraded) to ok/degraded"
                        # If status is "failed", it's probably offline or degraded. Let's map "failed" to "offline" for now as per TDS hint.
                else:
                    # Timed out
                    is_online = False
                    derived_status = "offline"
            else:
                # No data ever received
                is_online = False
                derived_status = "offline"

            # Update summary
            summary[derived_status] = summary.get(derived_status, 0) + 1

            nodes_status.append(
                NodeAggregatedStatus(
                    meta=display_meta,
                    last_result=last_result if is_online else None, # TDS: "None if no data / timed out"
                    is_online=is_online,
                    derived_status=derived_status,
                )
            )

        return AggregatedReport(
            generated_at=now,
            nodes=nodes_status,
            summary=summary,
        )
