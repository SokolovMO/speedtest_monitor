"""
Telegram notification module.

Handles sending formatted messages to Telegram.
"""

import asyncio
import time
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from speedtest_monitor.chat_prefs import (
    ChatPreferences,
    ensure_default_preferences,
    get_chat_preferences,
    set_chat_language,
    set_chat_view_mode,
)
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
from .localization import get_label

logger = get_logger()


class TelegramNotifier:
    """
    Sends formatted speedtest results to Telegram.

    Handles message formatting, status determination, and error handling.
    """

    def __init__(self, config: Config, aggregator=None):
        """
        Initialize Telegram notifier.

        Args:
            config: Application configuration
            aggregator: Optional Aggregator instance (needed for callbacks to re-render reports)
        """
        self.config = config
        self.aggregator = aggregator
        self.dp = Dispatcher()
        self._setup_handlers()
        
        # Cache server info on initialization to avoid repeated lookups
        self._server_name = None
        self._server_location = None
        self._server_identifier = None

    def _setup_handlers(self):
        """Register Telegram handlers."""
        self.dp.callback_query.register(self._handle_callback, F.data.startswith("pref:"))

    def _get_keyboard(self, current_lang: str, current_view: str) -> InlineKeyboardMarkup:
        """Generate inline keyboard for settings."""
        # Language buttons
        lang_ru = "✅ 🌐 ru" if current_lang == "ru" else "🌐 ru"
        lang_en = "✅ 🌐 en" if current_lang == "en" else "🌐 en"
        
        # View mode buttons
        view_compact = "✅ 📄 compact" if current_view == "compact" else "📄 compact"
        view_detailed = "✅ 📋 detailed" if current_view == "detailed" else "📋 detailed"
        
        keyboard = [
            [
                InlineKeyboardButton(text=lang_ru, callback_data="pref:lang:ru"),
                InlineKeyboardButton(text=lang_en, callback_data="pref:lang:en"),
            ],
            [
                InlineKeyboardButton(text=view_compact, callback_data="pref:view:compact"),
                InlineKeyboardButton(text=view_detailed, callback_data="pref:view:detailed"),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    async def _handle_callback(self, callback: CallbackQuery):
        """Handle preference change callbacks."""
        try:
            if not callback.data or not callback.message:
                return

            # data format: pref:type:value
            parts = callback.data.split(":")
            if len(parts) != 3:
                return
                
            _, pref_type, value = parts
            chat_id = callback.message.chat.id
            
            if pref_type == "lang":
                set_chat_language(chat_id, value)
            elif pref_type == "view":
                set_chat_view_mode(chat_id, value)
            
            # Re-render report if aggregator is available
            if self.aggregator:
                prefs = get_chat_preferences(chat_id)
                if prefs:
                    from speedtest_monitor.view_renderer import render_compact, render_detailed
                    
                    report = self.aggregator.build_report()
                    if prefs.view_mode == "detailed":
                        text = render_detailed(report, prefs.language)
                    else:
                        text = render_compact(report, prefs.language)
                    
                    keyboard = self._get_keyboard(prefs.language, prefs.view_mode)
                    
                    # Edit message
                    # Check if message is accessible (it should be for callbacks)
                    if hasattr(callback.message, "edit_text"):
                        await callback.message.edit_text(
                            text=text,
                            reply_markup=keyboard,
                            parse_mode=ParseMode.HTML
                        )
            
            await callback.answer("Preferences updated")
            
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            await callback.answer("Error updating preferences")

    async def start_polling(self):
        """Start Telegram bot polling."""
        if not self.config.telegram.bot_token:
            return
            
        bot = Bot(token=self.config.telegram.bot_token)
        logger.info("Starting Telegram bot polling...")
        try:
            await self.dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Polling error: {e}")
        finally:
            await bot.session.close()

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

    def _get_status_emoji(self, download_mbps: float, language: str) -> tuple[str, str]:
        """
        Determine status emoji and text based on download speed.

        Args:
            download_mbps: Download speed in Mbps
            language: Language code ("en" or "ru")

        Returns:
            Tuple of (emoji, status_text)
        """
        thresholds = self.config.thresholds
        status_key = "excellent"

        if download_mbps < thresholds.very_low:
            status_key = "very_low"
        elif download_mbps < thresholds.low:
            status_key = "low"
        elif download_mbps < thresholds.medium:
            status_key = "normal"
        elif download_mbps < thresholds.good:
            status_key = "good"

        # Try to get from config
        if self.config.status_config and status_key in self.config.status_config.single_node_statuses:
            status_cfg = self.config.status_config.single_node_statuses[status_key]
            emoji = status_cfg.emoji
            text = status_cfg.label.get(language)
            if not text:
                text = get_label(f"status_{status_key}", language)
            return emoji, text

        # Fallback to hardcoded defaults
        defaults = {
            "very_low": ("🚨❌", get_label("status_very_low", language)),
            "low": ("⚠️🐌", get_label("status_low", language)),
            "normal": ("✅🚗", get_label("status_normal", language)),
            "good": ("👍🛜", get_label("status_good", language)),
            "excellent": ("🚀⚡", get_label("status_excellent", language)),
        }
        
        return defaults.get(status_key, ("❓", "Unknown"))

    def _format_message(self, result: SpeedtestResult, language: str) -> str:
        """
        Format speedtest result as Telegram message.

        Args:
            result: Speedtest result to format
            language: Language code ("en" or "ru")

        Returns:
            Formatted message text
        """
        server_name = self._get_server_name()
        server_location = self._get_server_location()
        server_id = self._get_server_identifier()
        description = self.config.server.description

        system_info = get_system_info()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report_title = get_label("report_title", language)

        if not result.success:
            # Error message
            message = (
                f"📊 <b>{report_title}</b>\n\n"
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
        emoji, status_text = self._get_status_emoji(result.download_mbps, language)
        
        # Localized labels
        lbl_download = get_label("download", language)
        lbl_upload = get_label("upload", language)
        lbl_ping = get_label("ping", language)
        lbl_status = get_label("status", language)
        lbl_test_server = get_label("test_server", language)
        lbl_isp = get_label("isp", language)
        lbl_os = get_label("os", language)

        message = (
            f"📊 <b>{report_title}</b>\n\n"
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
            f"⬇️ <b>{lbl_download}:</b> {format_speed(result.download_mbps)}\n"
            f"⬆️ <b>{lbl_upload}:</b> {format_speed(result.upload_mbps)}\n"
            f"📡 <b>{lbl_ping}:</b> {format_ping(result.ping_ms)}\n\n"
            f"📈 <b>{lbl_status}:</b> {emoji} {status_text}\n\n"
        )

        if result.server_location:
            message += f"🌐 <b>{lbl_test_server}:</b> {result.server_location}\n"

        if result.isp:
            message += f"🏢 <b>{lbl_isp}:</b> {result.isp}\n"

        message += f"💻 <b>{lbl_os}:</b> {system_info['os']} {system_info['os_version']}"

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

        # Send to all configured recipients
        async with Bot(token=self.config.telegram.bot_token) as bot:
            success_count = 0
            total_recipients = len(self.config.telegram.chat_ids)
            
            # Send to all chat_ids (supports both groups and personal messages)
            for chat_id in self.config.telegram.chat_ids:
                # Determine language
                lang = "ru" # Default
                try:
                    cid = int(chat_id)
                    defaults = ChatPreferences(
                        chat_id=cid,
                        language="ru",
                        view_mode="compact",
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    prefs = ensure_default_preferences(cid, defaults)
                    lang = prefs.language
                except ValueError:
                    # If chat_id is not an int, fallback to default
                    pass

                message = self._format_message(result, lang)
                
                # Validate message length
                if len(message) > MAX_MESSAGE_LENGTH:
                    logger.warning(f"Message too long ({len(message)} chars), truncating...")
                    message = message[:MAX_MESSAGE_LENGTH - 3] + "..."

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

    async def send_aggregated_report(self, report) -> bool:
        """
        Send aggregated report to all master targets.
        
        Args:
            report: AggregatedReport object
            
        Returns:
            True if at least one message sent successfully
        """
        if not self.config.master or not self.config.master.telegram_targets:
            logger.warning("No telegram targets configured for master mode")
            return False

        from speedtest_monitor.view_renderer import render_compact, render_detailed

        async with Bot(token=self.config.telegram.bot_token) as bot:
            success_count = 0
            targets = self.config.master.telegram_targets
            
            for target in targets:
                # Ensure preferences exist
                defaults = ChatPreferences(
                    chat_id=target.chat_id,
                    language=target.default_language,
                    view_mode=target.default_view_mode,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                prefs = ensure_default_preferences(target.chat_id, defaults)
                
                # Render message
                if prefs.view_mode == "detailed":
                    message = render_detailed(report, prefs.language, self.config.status_config)
                else:
                    message = render_compact(report, prefs.language, self.config.status_config)
                
                keyboard = self._get_keyboard(prefs.language, prefs.view_mode)
                
                # Send message with keyboard
                try:
                    await bot.send_message(
                        chat_id=target.chat_id,
                        text=message,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard
                    )
                    success_count += 1
                    logger.info(f"Message sent successfully to {target.chat_id}")
                except Exception as e:
                    logger.error(f"Error sending to {target.chat_id}: {e}")
            
            if success_count > 0:
                logger.info(f"Aggregated report sent to {success_count}/{len(targets)} recipients")
                return True
            else:
                logger.error("Failed to send aggregated report to any recipient")
                return False

