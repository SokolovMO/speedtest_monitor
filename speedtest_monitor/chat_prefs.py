"""
Chat preferences storage module.

Manages per-chat settings (language, view mode) using SQLite.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path("chat_prefs.db")


@dataclass
class ChatPreferences:
    """User preferences for a specific chat."""
    chat_id: int
    language: str  # "ru" | "en"
    view_mode: str  # "compact" | "detailed"
    created_at: datetime
    updated_at: datetime


def _init_db():
    """Initialize the database table."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_prefs (
                chat_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL,
                view_mode TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
            """
        )


def get_chat_preferences(chat_id: int) -> Optional[ChatPreferences]:
    """
    Get preferences for a chat.
    
    Args:
        chat_id: Telegram chat ID
        
    Returns:
        ChatPreferences object or None if not found
    """
    _init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT chat_id, language, view_mode, created_at, updated_at FROM chat_prefs WHERE chat_id = ?",
            (chat_id,),
        )
        row = cursor.fetchone()
        if row:
            return ChatPreferences(
                chat_id=row[0],
                language=row[1],
                view_mode=row[2],
                created_at=datetime.fromisoformat(row[3]),
                updated_at=datetime.fromisoformat(row[4]),
            )
    return None


def set_chat_language(chat_id: int, language: str) -> None:
    """Update chat language."""
    _update_pref(chat_id, "language", language)


def set_chat_view_mode(chat_id: int, view_mode: str) -> None:
    """Update chat view mode."""
    _update_pref(chat_id, "view_mode", view_mode)


def _update_pref(chat_id: int, column: str, value: str) -> None:
    """Internal helper to update a single preference column."""
    _init_db()
    now = datetime.now()
    with sqlite3.connect(DB_PATH) as conn:
        # Check if exists
        cursor = conn.execute("SELECT 1 FROM chat_prefs WHERE chat_id = ?", (chat_id,))
        if cursor.fetchone():
            conn.execute(
                f"UPDATE chat_prefs SET {column} = ?, updated_at = ? WHERE chat_id = ?",
                (value, now.isoformat(), chat_id),
            )
        else:
            # Should be created via ensure_default_preferences first, but handle safe fallback
            defaults = {
                "language": "en",
                "view_mode": "compact",
                column: value
            }
            conn.execute(
                "INSERT INTO chat_prefs (chat_id, language, view_mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, defaults["language"], defaults["view_mode"], now.isoformat(), now.isoformat()),
            )


def ensure_default_preferences(chat_id: int, defaults: ChatPreferences) -> ChatPreferences:
    """
    Ensure preferences exist for a chat, creating them with defaults if needed.
    
    Args:
        chat_id: Telegram chat ID
        defaults: Default preferences to use if creating new record
        
    Returns:
        Current (existing or new) ChatPreferences
    """
    existing = get_chat_preferences(chat_id)
    if existing:
        return existing

    _init_db()
    now = datetime.now()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO chat_prefs (chat_id, language, view_mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (chat_id, defaults.language, defaults.view_mode, now.isoformat(), now.isoformat()),
        )
    
    return ChatPreferences(
        chat_id=chat_id,
        language=defaults.language,
        view_mode=defaults.view_mode,
        created_at=now,
        updated_at=now,
    )
