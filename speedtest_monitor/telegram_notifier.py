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
from .utils import get_system_info, get_location_by_ip
from speedtest_monitor.message_formatter import MessageFormatter

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
                    report = self.aggregator.build_report()
                    text = MessageFormatter.format_master_report(
                        report, 
                        style=prefs.view_mode, 
                        lang=prefs.language,
                        status_config=self.config.status_config
                    )
                    
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

    def _calculate_status_key(self, download_mbps: float) -> str:
        """Calculate status key based on download speed."""
        thresholds = self.config.thresholds
        if download_mbps < thresholds.very_low:
            return "very_low"
        elif download_mbps < thresholds.low:
            return "low"
        elif download_mbps < thresholds.medium:
            return "normal"
        elif download_mbps < thresholds.good:
            return "good"
        return "excellent"

    def _format_message(self, result: SpeedtestResult, language: str = "ru", style: Optional[str] = None) -> str:
        """
        Format speedtest result message.

        Args:
            result: Speedtest result to format
            language: Language code ("en" or "ru")
            style: Message style ("compact" or "detailed"). If None, uses config or default.

        Returns:
            Formatted message text
        """
        server_info = {
            "name": self._get_server_name(),
            "location": self._get_server_location(),
            "id": self._get_server_identifier(),
            "description": self.config.server.description
        }
        
        status_key = "unknown"
        if result.success:
            status_key = self._calculate_status_key(result.download_mbps)

        # Use provided style, or configured style, or default to detailed
        if not style:
            style = self.config.telegram.message_style if hasattr(self.config.telegram, "message_style") else "detailed"

        return MessageFormatter.format_single_result(
            result=result,
            style=style,
            lang=language,
            server_info=server_info,
            status_config=self.config.status_config,
            status_key=status_key
        )

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

    async def _send_to_recipient(self, bot: Bot, chat_id: str, message: str, reply_markup: Optional[InlineKeyboardMarkup] = None) -> bool:
        """
        Send message to a single recipient with retry logic.
        
        Args:
            bot: Bot instance
            chat_id: Chat or user ID
            message: Message text
            reply_markup: Optional keyboard markup
            
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
                        reply_markup=reply_markup,
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
                # Determine language and style from preferences
                lang = self.config.telegram.language if hasattr(self.config.telegram, "language") else "ru"
                view_mode = "detailed" # Default fallback
                
                try:
                    cid = int(chat_id)
                    defaults = ChatPreferences(
                        chat_id=cid,
                        language=lang,
                        view_mode="detailed", # Default for single mode
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    prefs = ensure_default_preferences(cid, defaults)
                    lang = prefs.language
                    view_mode = prefs.view_mode
                except ValueError:
                    # If chat_id is not an int, fallback to default
                    pass

                message = self._format_message(result, lang, style=view_mode)
                # keyboard = self._get_keyboard(lang, view_mode) # Buttons don't work in single mode (no daemon)
                
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
                message = MessageFormatter.format_master_report(
                    report, 
                    style=prefs.view_mode, 
                    lang=prefs.language,
                    status_config=self.config.status_config
                )
                
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

