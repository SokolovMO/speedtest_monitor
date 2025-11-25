"""
Tests for Chat Preferences module.
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
from speedtest_monitor.chat_prefs import (
    ChatPreferences,
    get_chat_preferences,
    set_chat_language,
    set_chat_view_mode,
    ensure_default_preferences,
    _init_db
)

@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database path."""
    db_path = tmp_path / "test_chat_prefs.db"
    with patch("speedtest_monitor.chat_prefs.DB_PATH", db_path):
        yield db_path

def test_ensure_default_preferences(temp_db):
    """Test creating default preferences."""
    chat_id = 123
    defaults = ChatPreferences(
        chat_id=chat_id,
        language="en",
        view_mode="compact",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    prefs = ensure_default_preferences(chat_id, defaults)
    assert prefs.chat_id == chat_id
    assert prefs.language == "en"
    assert prefs.view_mode == "compact"
    
    # Verify persistence
    fetched = get_chat_preferences(chat_id)
    assert fetched is not None
    assert fetched.chat_id == chat_id

def test_update_preferences(temp_db):
    """Test updating preferences."""
    chat_id = 456
    defaults = ChatPreferences(
        chat_id=chat_id,
        language="en",
        view_mode="compact",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    ensure_default_preferences(chat_id, defaults)
    
    set_chat_language(chat_id, "ru")
    prefs = get_chat_preferences(chat_id)
    assert prefs is not None
    assert prefs.language == "ru"
    
    set_chat_view_mode(chat_id, "detailed")
    prefs = get_chat_preferences(chat_id)
    assert prefs is not None
    assert prefs.view_mode == "detailed"

def test_get_nonexistent_preferences(temp_db):
    """Test getting preferences for unknown chat."""
    prefs = get_chat_preferences(999)
    assert prefs is None
