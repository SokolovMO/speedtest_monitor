"""
Tests for the Localization module.
"""

import pytest
from speedtest_monitor.localization import LABELS, get_label

def test_labels_consistency():
    """Ensure all keys in English dictionary exist in Russian dictionary."""
    en_keys = set(LABELS["en"].keys())
    ru_keys = set(LABELS["ru"].keys())
    
    missing_in_ru = en_keys - ru_keys
    missing_in_en = ru_keys - en_keys
    
    assert not missing_in_ru, f"Missing keys in RU: {missing_in_ru}"
    assert not missing_in_en, f"Missing keys in EN: {missing_in_en}"

def test_get_label():
    """Test label retrieval."""
    assert get_label("report_title", "en") == "📊 Internet Speed Report"
    assert get_label("report_title", "ru") == "📊 Отчет о скорости интернета"
    
    # Fallback to EN
    assert get_label("report_title", "fr") == "📊 Internet Speed Report"
    
    # Missing key returns key
    assert get_label("unknown_key", "en") == "unknown_key"
