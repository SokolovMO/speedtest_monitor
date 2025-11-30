"""
Message formatter module.

Handles formatting of Telegram messages for all modes (single, master, node)
and styles (compact, detailed) with localization support.
"""

from datetime import datetime
from typing import Dict, Optional, Any, Tuple, Union

from speedtest_monitor.models import SpeedtestResult as ModelSpeedtestResult, AggregatedReport
from speedtest_monitor.speedtest_runner import SpeedtestResult as RunnerSpeedtestResult
from speedtest_monitor.utils import format_speed, format_ping, get_system_info

# Localization strings
STRINGS = {
    "en": {
        "header": "📊 Internet Speed Report",
        "server": "Server",
        "desc": "Description",
        "id": "ID",
        "time": "Time",
        "results": "Results",
        "download": "Download",
        "upload": "Upload",
        "ping": "Ping",
        "status": "Status",
        "test_server": "Test Server",
        "isp": "ISP",
        "os": "OS",
        "error": "Error",
        "error_detail": "Error Details",
        "last_hour": "last hour",
        "offline": "No data",
        # Statuses
        "status_very_low": "Very Low",
        "status_low": "Low",
        "status_normal": "Normal",
        "status_good": "Good",
        "status_excellent": "Excellent",
        "status_ok": "Good",
        "status_degraded": "Degraded",
        "status_offline": "Offline",
    },
    "ru": {
        "header": "📊 Отчет о скорости интернета",
        "server": "Сервер",
        "desc": "Описание",
        "id": "ID",
        "time": "Время",
        "results": "Результаты",
        "download": "Загрузка",
        "upload": "Отдача",
        "ping": "Пинг",
        "status": "Статус",
        "test_server": "Тестовый сервер",
        "isp": "Провайдер",
        "os": "ОС",
        "error": "Ошибка",
        "error_detail": "Подробности ошибки",
        "last_hour": "последний час",
        "offline": "Нет данных",
        # Statuses
        "status_very_low": "Очень низко",
        "status_low": "Низко",
        "status_normal": "Нормально",
        "status_good": "Хорошо",
        "status_excellent": "Отлично",
        "status_ok": "Хорошо",
        "status_degraded": "Просадка",
        "status_offline": "Офлайн",
    },
}

# Default emojis for statuses
STATUS_EMOJIS = {
    "very_low": "🚨❌",
    "low": "⚠️🐌",
    "normal": "✅🚗",
    "good": "👍🛜",
    "excellent": "🚀⚡",
    "ok": "✅",
    "degraded": "⚠️",
    "offline": "🔴",
    "unknown": "❓",
}


class MessageFormatter:
    """
    Formatter for Telegram messages.
    """

    @staticmethod
    def _get_string(key: str, lang: str) -> str:
        """Get localized string."""
        return STRINGS.get(lang, STRINGS["en"]).get(key, key)

    @staticmethod
    def _get_status_info(status_key: str, lang: str, custom_config: Optional[Any] = None) -> Tuple[str, str]:
        """
        Get emoji and localized text for a status.
        
        Args:
            status_key: Status key (e.g., "good", "low", "ok")
            lang: Language code
            custom_config: Optional StatusConfig object from config
            
        Returns:
            Tuple of (emoji, text)
        """
        emoji = STATUS_EMOJIS.get(status_key, STATUS_EMOJIS["unknown"])
        text = MessageFormatter._get_string(f"status_{status_key}", lang)

        # Override from config if available
        if custom_config:
            # Check single node statuses
            if custom_config.single_node_statuses and status_key in custom_config.single_node_statuses:
                cfg = custom_config.single_node_statuses[status_key]
                emoji = cfg.emoji
                if cfg.label.get(lang):
                    text = cfg.label.get(lang)
            # Check aggregated statuses
            elif custom_config.aggregated_statuses and status_key in custom_config.aggregated_statuses:
                cfg = custom_config.aggregated_statuses[status_key]
                emoji = cfg.emoji
                if cfg.label.get(lang):
                    text = cfg.label.get(lang)

        return emoji, text

    @staticmethod
    def format_single_result(
        result: RunnerSpeedtestResult,
        style: str = "detailed",
        lang: str = "ru",
        server_info: Optional[Dict[str, str]] = None,
        status_config: Optional[Any] = None,
        status_key: str = "unknown"
    ) -> str:
        """
        Format a single speedtest result (Single Mode).
        """
        s = lambda k: MessageFormatter._get_string(k, lang)
        
        # Header
        header = s("header")
        
        # Server Info
        server_name = server_info.get("name", "Unknown") if server_info else "Unknown"
        server_loc = server_info.get("location", "Unknown") if server_info else "Unknown"
        server_id = server_info.get("id", "Unknown") if server_info else "Unknown"
        desc = server_info.get("description", "") if server_info else ""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_info = get_system_info()

        # Error Handling
        if not result.success:
            msg = [
                f"<b>{header}</b>",
                "",
                f"🖥 <b>{s('server')}:</b> {server_name} ({server_loc})",
            ]
            if desc:
                msg.append(f"📝 <b>{s('desc')}:</b> {desc}")
            
            msg.extend([
                f"🆔 <b>{s('id')}:</b> {server_id}",
                f"🕐 <b>{s('time')}:</b> {timestamp}",
                "",
                f"❌ <b>{s('error')}:</b> {result.error_message or 'Unknown error'}",
            ])
            
            # Add OS info at the bottom
            msg.extend([
                "",
                f"💻 <b>{s('os')}:</b> {system_info['os']} {system_info['os_version']}"
            ])
            
            return "\n".join(msg)

        # Success Handling
        emoji, status_text = MessageFormatter._get_status_info(status_key, lang, status_config)

        if style == "compact":
            # Truly compact mode: Header + Results + Status
            msg = [
                f"<b>{header}</b>",
                f"⬇️ {format_speed(result.download_mbps)} | ⬆️ {format_speed(result.upload_mbps)} | 📡 {format_ping(result.ping_ms)}",
                f"{emoji} {status_text}"
            ]
            return "\n".join(msg)

        # Detailed mode
        msg = [
            f"<b>{header}</b>",
            "",
            f"🖥 <b>{s('server')}:</b> {server_name} ({server_loc})",
        ]
        if desc:
            msg.append(f"📝 <b>{s('desc')}:</b> {desc}")
            
        msg.extend([
            f"🆔 <b>{s('id')}:</b> {server_id}",
            f"🕐 <b>{s('time')}:</b> {timestamp}",
            "",
        ])

        msg.extend([
            f"📶 <b>{s('results')}:</b>",
            f"⬇️ <b>{s('download')}:</b> {format_speed(result.download_mbps)}",
            f"⬆️ <b>{s('upload')}:</b> {format_speed(result.upload_mbps)}",
            f"📡 <b>{s('ping')}:</b> {format_ping(result.ping_ms)}",
            "",
            f"📈 <b>{s('status')}:</b> {emoji} {status_text}",
            ""
        ])
        
        if result.server_location:
            msg.append(f"🌐 <b>{s('test_server')}:</b> {result.server_location}")
        if result.isp:
            msg.append(f"🏢 <b>{s('isp')}:</b> {result.isp}")
            
        msg.append(f"💻 <b>{s('os')}:</b> {system_info['os']} {system_info['os_version']}")

        return "\n".join(msg)

    @staticmethod
    def format_master_report(
        report: AggregatedReport,
        style: str = "compact",
        lang: str = "ru",
        status_config: Optional[Any] = None
    ) -> str:
        """
        Format aggregated report (Master Mode).
        """
        s = lambda k: MessageFormatter._get_string(k, lang)
        header = s("header")
        last_hour = s("last_hour")
        
        msg = [f"<b>{header}</b> ({last_hour})", ""]
        
        if style == "compact":
            for node in report.nodes:
                flag = node.meta.flag or "🛰️"
                name = node.meta.display_name or node.meta.node_id
                
                if node.is_online and node.last_result:
                    dl = f"{node.last_result.download_mbps:.0f}"
                    ul = f"{node.last_result.upload_mbps:.0f}"
                    ping = f"{node.last_result.ping_ms:.1f}"
                    
                    # Determine status
                    # Use detailed status if available, else derived
                    status_key = node.last_result.status if node.last_result.status else "ok"
                    if node.derived_status == "degraded":
                        status_key = "degraded" # Override if aggregator thinks it's degraded
                    
                    emoji, text = MessageFormatter._get_status_info(status_key, lang, status_config)
                    
                    msg.append(
                        f"{flag} {name} — {dl} / {ul} Mbps, ping {ping} ms — {emoji} {text}"
                    )
                else:
                    offline_text = s("offline")
                    msg.append(f"{flag} {name} — {offline_text} 🔴")
        
        else: # Detailed master report
            # Implement if needed, for now similar to compact but maybe with more lines per node
            for node in report.nodes:
                flag = node.meta.flag or "🛰️"
                name = node.meta.display_name or node.meta.node_id
                msg.append(f"🔹 <b>{flag} {name}</b>")
                
                if node.is_online and node.last_result:
                    if node.last_result.description:
                        msg.append(f"   📝 {node.last_result.description}")

                    dl = format_speed(node.last_result.download_mbps)
                    ul = format_speed(node.last_result.upload_mbps)
                    ping = format_ping(node.last_result.ping_ms)
                    
                    status_key = node.last_result.status if node.last_result.status else "ok"
                    emoji, text = MessageFormatter._get_status_info(status_key, lang, status_config)
                    
                    msg.append(f"   ⬇️ {dl} | ⬆️ {ul} | 📡 {ping}")
                    msg.append(f"   📈 {emoji} {text}")
                else:
                    msg.append(f"   🔴 {s('offline')}")
                msg.append("")

        return "\n".join(msg)
