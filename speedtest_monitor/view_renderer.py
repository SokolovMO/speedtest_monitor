"""
View renderer module.

Converts aggregated reports into formatted text messages.
"""

from typing import Optional, Tuple
from speedtest_monitor.config import StatusConfig
from speedtest_monitor.localization import get_label
from speedtest_monitor.models import AggregatedReport, NodeAggregatedStatus


def _get_aggregated_status(status_key: str, language: str, config: Optional[StatusConfig] = None) -> Tuple[str, str]:
    """
    Get emoji and label for aggregated status.
    
    Args:
        status_key: Status key ("ok", "degraded")
        language: Language code
        config: Status configuration
        
    Returns:
        Tuple of (emoji, label)
    """
    # Default emojis matching current behavior
    default_emojis = {
        "ok": "✅",
        "degraded": "⚠️",
        "offline": "🔴"
    }
    
    emoji = default_emojis.get(status_key, "❓")
    label = get_label(status_key, language)
    
    if config and config.aggregated_statuses and status_key in config.aggregated_statuses:
        cfg = config.aggregated_statuses[status_key]
        emoji = cfg.emoji
        if cfg.label.get(language):
            label = cfg.label.get(language)
            
    return emoji, label


def _get_detailed_status_display(node_status: str, derived_status: str, language: str, config: Optional[StatusConfig] = None) -> Tuple[str, str]:
    """
    Get emoji and label for a status, preferring detailed single_node_statuses.
    """
    # Try to find exact match in single_node_statuses
    if config and config.single_node_statuses and node_status in config.single_node_statuses:
        cfg = config.single_node_statuses[node_status]
        label = cfg.label.get(language, node_status)
        return cfg.emoji, label
    
    # Fallback to derived status (ok/degraded)
    status_key = "ok"
    if derived_status == "degraded":
        status_key = "degraded"
    elif derived_status == "offline":
        status_key = "offline"
        
    return _get_aggregated_status(status_key, language, config)


def render_compact(report: AggregatedReport, language: str, status_config: Optional[StatusConfig] = None) -> str:
    """
    Render report in compact view.
    
    Format:
    📊 Title (time)
    
    🇫🇮 Name — DL / UL Mbps, ping X ms — Status
    ...
    """
    title = get_label("report_title", language)
    last_hour = get_label("last_hour", language)
    
    lines = [f"<b>{title}</b> ({last_hour})", ""]
    
    for node in report.nodes:
        flag = node.meta.flag or "🛰️"
        name = node.meta.display_name or node.meta.node_id
        
        if node.is_online and node.last_result:
            dl = f"{node.last_result.download_mbps:.0f}"
            ul = f"{node.last_result.upload_mbps:.0f}"
            ping = f"{node.last_result.ping_ms:.1f}"
            
            # Determine status
            status_emoji, status_text = _get_detailed_status_display(
                node.last_result.status,
                node.derived_status,
                language,
                status_config
            )
            
            lines.append(
                f"{flag} {name} — {dl} / {ul} Mbps, ping {ping} ms — {status_emoji} {status_text}"
            )
        else:
            offline_text = get_label("offline", language)
            lines.append(f"{flag} {name} — {offline_text} (offline)")
            
    return "\n".join(lines)


def render_detailed(report: AggregatedReport, language: str, status_config: Optional[StatusConfig] = None) -> str:
    """
    Render report in detailed view.
    
    Format:
    📊 Title (time)
    
    🇫🇮 Name
    ⬇️ Download: X Mbps
    ⬆️ Upload: X Mbps
    📡 Ping: X ms
    📈 Status: Emoji Text
    
    🌐 Server: ...
    🏢 ISP: ...
    💻 OS: ...
    
    ———
    ...
    """
    title = get_label("report_title", language)
    last_hour = get_label("last_hour", language)
    
    lines = [f"<b>{title}</b> ({last_hour})", ""]
    
    for i, node in enumerate(report.nodes):
        flag = node.meta.flag or "🛰️"
        name = node.meta.display_name or node.meta.node_id
        
        lines.append(f"<b>{flag} {name}</b>")
        
        if node.is_online and node.last_result:
            dl_label = get_label("download", language)
            ul_label = get_label("upload", language)
            ping_label = get_label("ping", language)
            status_label = get_label("status", language)
            server_label = get_label("test_server", language)
            isp_label = get_label("isp", language)
            os_label = get_label("os", language)
            
            dl = f"{node.last_result.download_mbps:.0f}"
            ul = f"{node.last_result.upload_mbps:.0f}"
            ping = f"{node.last_result.ping_ms:.1f}"
            
            # Status
            status_emoji, status_text = _get_detailed_status_display(
                node.last_result.status,
                node.derived_status,
                language,
                status_config
            )
            
            lines.append(f"⬇️ {dl_label}: {dl} Mbps")
            lines.append(f"⬆️ {ul_label}: {ul} Mbps")
            lines.append(f"📡 {ping_label}: {ping} ms")
            lines.append(f"📈 {status_label}: {status_emoji} {status_text}")
            lines.append("")
            lines.append(f"🌐 {server_label}: {node.last_result.test_server}")
            lines.append(f"🏢 {isp_label}: {node.last_result.isp}")
            lines.append(f"💻 {os_label}: {node.last_result.os_info}")
        else:
            offline_text = get_label("offline", language)
            lines.append(f"🔴 {offline_text}")
        
        if i < len(report.nodes) - 1:
            lines.append("")
            lines.append("———")
            lines.append("")
            
    return "\n".join(lines)
