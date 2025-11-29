"""
Localization module.

Contains language dictionaries and helper functions for text formatting.
"""

from typing import Dict

LABELS = {
    "en": {
        "report_title": "📊 Internet Speed Report",
        "summary_header": "Summary",
        "download": "Download",
        "upload": "Upload",
        "ping": "Ping",
        "status": "Status",
        "test_server": "Test Server",
        "isp": "ISP",
        "os": "OS",
        "offline": "No data",
        "ok": "Good",
        "degraded": "Degraded",
        "last_hour": "last hour",
        "status_very_low": "Very Low",
        "status_low": "Low",
        "status_normal": "Normal",
        "status_good": "Good",
        "status_excellent": "Excellent",
    },
    "ru": {
        "report_title": "📊 Отчет о скорости интернета",
        "summary_header": "Итоги",
        "download": "Загрузка",
        "upload": "Отдача",
        "ping": "Пинг",
        "status": "Статус",
        "test_server": "Тестовый сервер",
        "isp": "Провайдер",
        "os": "ОС",
        "offline": "Нет данных",
        "ok": "Хорошо",
        "degraded": "Просадка",
        "last_hour": "последний час",
        "status_very_low": "Очень низко",
        "status_low": "Низко",
        "status_normal": "Нормально",
        "status_good": "Хорошо",
        "status_excellent": "Отлично",
    },
}


def get_label(key: str, language: str = "en") -> str:
    """
    Get localized label for a key.
    
    Args:
        key: Label key
        language: Language code ("en" or "ru")
        
    Returns:
        Localized string or key if not found
    """
    lang_dict = LABELS.get(language, LABELS["en"])
    return lang_dict.get(key, key)
