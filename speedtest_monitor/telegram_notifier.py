"""
Telegram notification module.

Handles sending formatted messages to Telegram.
"""

import asyncio
import time
from datetime import datetime
from typing import Optional

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from .config import Config, ServerConfig, ThresholdsConfig
from .constants import (
    MAX_MESSAGE_LENGTH,
    TELEGRAM_API_TIMEOUT,
    TELEGRAM_RETRY_COUNT,
    TELEGRAM_RETRY_DELAY,
)
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
        # Cache server info on initialization to avoid repeated lookups
        self._server_name = None
        self._server_location = None
        self._server_identifier = None

    def _get_server_name(self) -> str:
        """Get server name (auto-detect if needed, cached)."""
        if self._server_name is None:
            if self.config.server.name == "auto":
                system_info = get_system_info()
                self._server_name = system_info["hostname"]
            else:
                self._server_name = self.config.server.name
        return self._server_name

    def _get_server_location(self) -> str:
        """Get server location (auto-detect if needed, cached)."""
        if self._server_location is None:
            if self.config.server.location == "auto":
                location = get_location_by_ip()
                self._server_location = location or "Unknown"
            else:
                self._server_location = self.config.server.location
        return self._server_location

    def _get_server_identifier(self) -> str:
        """Get server identifier (auto-detect if needed, cached)."""
        if self._server_identifier is None:
            if self.config.server.identifier == "auto":
                system_info = get_system_info()
                self._server_identifier = system_info["hostname"]
            else:
                self._server_identifier = self.config.server.identifier
        return self._server_identifier

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
            return "🚨❌", "Very Low / Очень низко"
        elif download_mbps < thresholds.low:
            return "⚠️🐌", "Low / Низко"
        elif download_mbps < thresholds.medium:
            return "✅🚗", "Normal / Нормально"
        elif download_mbps < thresholds.good:
            return "👍🛜", "Good / Хорошо"
        else:
            return "🚀⚡", "Excellent / Отлично"

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
                "📊 <b>Internet Speed Report / Отчет о скорости интернета</b>\n\n"
                f"🖥 <b>Server / Сервер:</b> {server_name}"
            )
            if server_location != "Unknown":
                message += f" ({server_location})"
            message += "\n"

            if description:
                message += f"📝 <b>Description / Описание:</b> {description}\n"

            message += (
                f"🆔 <b>ID:</b> {server_id}\n"
                f"🕐 <b>Time / Время:</b> {timestamp}\n\n"
                f"❌ <b>Error / Ошибка:</b> {result.error_message}\n\n"
                f"💻 <b>OS / ОС:</b> {system_info['os']} {system_info['os_version']}"
            )
            return message

        # Success message
        emoji, status_text = self._get_status_emoji(result.download_mbps)

        message = (
            "📊 <b>Internet Speed Report / Отчет о скорости интернета</b>\n\n"
            f"🖥 <b>Server / Сервер:</b> {server_name}"
        )
        if server_location != "Unknown":
            message += f" ({server_location})"
        message += "\n"

        if description:
            message += f"📝 <b>Description / Описание:</b> {description}\n"

        message += (
            f"🆔 <b>ID:</b> {server_id}\n"
            f"🕐 <b>Time / Время:</b> {timestamp}\n\n"
            f"📶 <b>Results / Результаты:</b>\n"
            f"⬇️ <b>Download / Загрузка:</b> {format_speed(result.download_mbps)}\n"
            f"⬆️ <b>Upload / Отдача:</b> {format_speed(result.upload_mbps)}\n"
            f"📡 <b>Ping / Пинг:</b> {format_ping(result.ping_ms)}\n\n"
            f"📈 <b>Status / Статус:</b> {emoji} {status_text}\n\n"
        )

        if result.server_location:
            message += f"🌐 <b>Test Server / Тестовый сервер:</b> {result.server_location}\n"

        if result.isp:
            message += f"🏢 <b>ISP / Провайдер:</b> {result.isp}\n"

        message += f"💻 <b>OS / ОС:</b> {system_info['os']} {system_info['os_version']}"

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

    async def _send_to_recipient(self, bot: Bot, chat_id: str, message: str) -> bool:
        """
        Send message to a single recipient with retry logic.
        
        Args:
            bot: Bot instance
            chat_id: Chat or user ID
            message: Message text
            
        Returns:
            True if sent successfully
        """
        for attempt in range(TELEGRAM_RETRY_COUNT):
            try:
                await asyncio.wait_for(
                    bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.HTML,
                    ),
                    timeout=TELEGRAM_API_TIMEOUT,
                )
                logger.info(f"Message sent successfully to {chat_id}")
                return True
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout sending to {chat_id} (attempt {attempt + 1}/{TELEGRAM_RETRY_COUNT})")
                
            except TelegramAPIError as e:
                logger.error(f"Telegram API error for {chat_id} (attempt {attempt + 1}/{TELEGRAM_RETRY_COUNT}): {e}")
                
            except Exception as e:
                logger.error(f"Error sending to {chat_id} (attempt {attempt + 1}/{TELEGRAM_RETRY_COUNT}): {e}")
            
            if attempt < TELEGRAM_RETRY_COUNT - 1:
                await asyncio.sleep(TELEGRAM_RETRY_DELAY)
        
        return False

    async def send_notification(self, result: SpeedtestResult) -> bool:
        """
        Send speedtest result to Telegram (async) with retry logic.

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

        message = self._format_message(result)
        
        # Validate message length
        if len(message) > MAX_MESSAGE_LENGTH:
            logger.warning(f"Message too long ({len(message)} chars), truncating...")
            message = message[:MAX_MESSAGE_LENGTH - 3] + "..."

        # Send to all configured recipients
        async with Bot(token=self.config.telegram.bot_token) as bot:
            success_count = 0
            total_recipients = len(self.config.telegram.chat_ids)
            
            # Send to all chat_ids (supports both groups and personal messages)
            for chat_id in self.config.telegram.chat_ids:
                if await self._send_to_recipient(bot, chat_id, message):
                    success_count += 1
            
            if success_count > 0:
                logger.info(f"Notification sent to {success_count}/{total_recipients} recipients")
                return True
            else:
                logger.error(f"Failed to send notification to any recipient ({total_recipients} total)")
                return False

    def send_notification_sync(self, result: SpeedtestResult) -> bool:
        """
        Send speedtest result to Telegram (sync wrapper).
        
        Thread-safe synchronous wrapper that properly manages event loop.

        Args:
            result: Speedtest result to send

        Returns:
            True if notification was sent successfully

        Example:
            >>> notifier = TelegramNotifier(config)
            >>> notifier.send_notification_sync(result)
        """
        try:
            # Create new event loop for thread safety
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.send_notification(result))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error in sync wrapper: {e}")
            return False

