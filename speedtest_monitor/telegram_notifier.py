"""
Telegram notification module.

Handles sending formatted messages to Telegram.
"""

import asyncio
from datetime import datetime
from typing import Optional

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from .config import Config, ServerConfig, ThresholdsConfig
from .logger import get_logger
from .speedtest_runner import SpeedtestResult
from .utils import format_ping, format_speed, get_location_by_ip, get_system_info

logger = get_logger()


class TelegramNotifier:
    """
    Sends formatted speedtest results to Telegram.

    Handles message formatting, status determination, and error handling.
    """

    def __init__(self, config: Config):
        """
        Initialize Telegram notifier.

        Args:
            config: Application configuration
        """
        self.config = config
        self.bot = Bot(token=config.telegram.bot_token)

    def _get_server_name(self) -> str:
        """Get server name (auto-detect if needed)."""
        if self.config.server.name == "auto":
            system_info = get_system_info()
            return system_info["hostname"]
        return self.config.server.name

    def _get_server_location(self) -> str:
        """Get server location (auto-detect if needed)."""
        if self.config.server.location == "auto":
            location = get_location_by_ip()
            return location or "Unknown"
        return self.config.server.location

    def _get_server_identifier(self) -> str:
        """Get server identifier (auto-detect if needed)."""
        if self.config.server.identifier == "auto":
            system_info = get_system_info()
            return system_info["hostname"]
        return self.config.server.identifier

    def _get_status_emoji(self, download_mbps: float) -> tuple[str, str]:
        """
        Determine status emoji and text based on download speed.

        Args:
            download_mbps: Download speed in Mbps

        Returns:
            Tuple of (emoji, status_text)
        """
        thresholds = self.config.thresholds

        if download_mbps < thresholds.very_low:
            return "🚨❌", "Очень низко / Very Low"
        elif download_mbps < thresholds.low:
            return "⚠️🐌", "Низко / Low"
        elif download_mbps < thresholds.medium:
            return "✅🚗", "Нормально / Normal"
        elif download_mbps < thresholds.good:
            return "👍🛜", "Хорошо / Good"
        else:
            return "🚀⚡", "Отлично / Excellent"

    def _format_message(self, result: SpeedtestResult) -> str:
        """
        Format speedtest result as Telegram message.

        Args:
            result: Speedtest result to format

        Returns:
            Formatted message text
        """
        server_name = self._get_server_name()
        server_location = self._get_server_location()
        server_id = self._get_server_identifier()
        description = self.config.server.description

        system_info = get_system_info()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not result.success:
            # Error message
            message = (
                "📊 <b>Отчет о скорости интернета / Internet Speed Report</b>\n\n"
                f"🖥 <b>Сервер / Server:</b> {server_name}"
            )
            if server_location != "Unknown":
                message += f" ({server_location})"
            message += "\n"

            if description:
                message += f"📝 <b>Описание / Description:</b> {description}\n"

            message += (
                f"🆔 <b>ID:</b> {server_id}\n"
                f"🕐 <b>Время / Time:</b> {timestamp}\n\n"
                f"❌ <b>Ошибка / Error:</b> {result.error_message}\n\n"
                f"💻 <b>ОС / OS:</b> {system_info['os']} {system_info['os_version']}"
            )
            return message

        # Success message
        emoji, status_text = self._get_status_emoji(result.download_mbps)

        message = (
            "📊 <b>Отчет о скорости интернета / Internet Speed Report</b>\n\n"
            f"🖥 <b>Сервер / Server:</b> {server_name}"
        )
        if server_location != "Unknown":
            message += f" ({server_location})"
        message += "\n"

        if description:
            message += f"📝 <b>Описание / Description:</b> {description}\n"

        message += (
            f"🆔 <b>ID:</b> {server_id}\n"
            f"🕐 <b>Время / Time:</b> {timestamp}\n\n"
            f"📶 <b>Результаты / Results:</b>\n"
            f"⬇️ <b>Загрузка / Download:</b> {format_speed(result.download_mbps)}\n"
            f"⬆️ <b>Отдача / Upload:</b> {format_speed(result.upload_mbps)}\n"
            f"📡 <b>Пинг / Ping:</b> {format_ping(result.ping_ms)}\n\n"
            f"📈 <b>Статус / Status:</b> {emoji} {status_text}\n\n"
        )

        if result.server_location:
            message += f"🌐 <b>Тестовый сервер / Test Server:</b> {result.server_location}\n"

        if result.isp:
            message += f"🏢 <b>Провайдер / ISP:</b> {result.isp}\n"

        message += f"💻 <b>ОС / OS:</b> {system_info['os']} {system_info['os_version']}"

        return message

    def _should_send_notification(self, result: SpeedtestResult) -> bool:
        """
        Determine if notification should be sent.

        Args:
            result: Speedtest result

        Returns:
            True if notification should be sent
        """
        # Always send errors
        if not result.success:
            return True

        # If send_always is enabled
        if self.config.telegram.send_always:
            return True

        # Send only if speed is below threshold
        return result.download_mbps < self.config.thresholds.low

    async def send_notification(self, result: SpeedtestResult) -> bool:
        """
        Send speedtest result to Telegram (async).

        Args:
            result: Speedtest result to send

        Returns:
            True if notification was sent successfully

        Example:
            >>> notifier = TelegramNotifier(config)
            >>> await notifier.send_notification(result)
        """
        if not self._should_send_notification(result):
            logger.info("Skipping notification (speed is good and send_always=False)")
            return False

        try:
            message = self._format_message(result)
            await self.bot.send_message(
                chat_id=self.config.telegram.chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
            )
            logger.info("Telegram notification sent successfully")
            return True
        except TelegramAPIError as e:
            logger.error(f"Telegram API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return False
        finally:
            await self.bot.session.close()

    def send_notification_sync(self, result: SpeedtestResult) -> bool:
        """
        Send speedtest result to Telegram (sync wrapper).

        Args:
            result: Speedtest result to send

        Returns:
            True if notification was sent successfully

        Example:
            >>> notifier = TelegramNotifier(config)
            >>> notifier.send_notification_sync(result)
        """
        return asyncio.run(self.send_notification(result))
