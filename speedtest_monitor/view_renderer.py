"""
View renderer module.

Converts aggregated reports into formatted text messages.
"""

from speedtest_monitor.localization import get_label
from speedtest_monitor.models import AggregatedReport, NodeAggregatedStatus


def _get_status_emoji(status: str) -> str:
    """Get emoji for status."""
    if status == "ok":
        return "✅"
    elif status == "degraded":
        return "⚠️"
    elif status == "offline":
        return "🔴"
    return "❓"


def _get_detailed_status_emoji(speedtest_status: str) -> str:
    """Get emoji for detailed status description."""
    if speedtest_status == "excellent":
        return "🚀"
    elif speedtest_status == "good":
        return "👍"
    elif speedtest_status == "degraded":
        return "⚠️"
    elif speedtest_status == "failed":
        return "❌"
    return "❓"


def render_compact(report: AggregatedReport, language: str) -> str:
    """
    Render report in compact view.
    
    Format:
    📊 Title (time)
    
    🇫🇮 Name — DL / UL Mbps, ping X ms — Status
    ...
    """
    title = get_label("report_title", language)
    last_hour = get_label("last_hour", language)
    time_str = report.generated_at.strftime("%H:%M")
    
    lines = [f"<b>{title}</b> ({last_hour})", ""]
    
    for node in report.nodes:
        flag = node.meta.flag or ""
        name = node.meta.display_name or node.meta.node_id
        
        if node.is_online and node.last_result:
            dl = f"{node.last_result.download_mbps:.0f}"
            ul = f"{node.last_result.upload_mbps:.0f}"
            ping = f"{node.last_result.ping_ms:.1f}"
            
            # Determine status label
            status_label_key = "ok"
            if node.derived_status == "degraded":
                status_label_key = "degraded"
            
            status_text = get_label(status_label_key, language)
            status_emoji = _get_detailed_status_emoji(node.last_result.status)
            
            lines.append(
                f"{flag} {name} — {dl} / {ul} Mbps, ping {ping} ms — {status_emoji} {status_text}"
            )
        else:
            offline_text = get_label("offline", language)
            lines.append(f"{flag} {name} — {offline_text} (offline)")
            
    return "\n".join(lines)


def render_detailed(report: AggregatedReport, language: str) -> str:
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
        flag = node.meta.flag or ""
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
            status_key = "ok"
            if node.derived_status == "degraded":
                status_key = "degraded"
            status_text = get_label(status_key, language)
            status_emoji = _get_detailed_status_emoji(node.last_result.status)
            
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
