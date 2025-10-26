"""
Utility functions for the speedtest monitor.

Common helper functions used across the application.
"""

import platform
import socket
from typing import Dict, Optional

import requests


def get_system_info() -> Dict[str, str]:
    """
    Get system information (OS, hostname, etc.).

    Returns:
        Dictionary with system information

    Example:
        >>> info = get_system_info()
        >>> print(info['hostname'])
        'web-server-01'
    """
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.release(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
    }


def get_public_ip() -> Optional[str]:
    """
    Get public IP address of the server.

    Returns:
        Public IP address or None if failed

    Example:
        >>> ip = get_public_ip()
        >>> print(ip)
        '192.168.1.1'
    """
    try:
        response = requests.get("https://api.ipify.org", timeout=5)
        return response.text.strip()
    except Exception:
        return None


def get_location_by_ip(ip: Optional[str] = None) -> Optional[str]:
    """
    Get approximate location by IP address.

    Args:
        ip: IP address to lookup. If None, uses current public IP

    Returns:
        Location string or None if failed

    Example:
        >>> location = get_location_by_ip()
        >>> print(location)
        'Moscow, Russia'
    """
    if ip is None:
        ip = get_public_ip()

    if not ip:
        return None

    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        data = response.json()
        city = data.get("city", "")
        country = data.get("country_name", "")
        if city and country:
            return f"{city}, {country}"
        elif country:
            return country
        return None
    except Exception:
        return None


def format_speed(speed_mbps: float) -> str:
    """
    Format speed in Mbps with proper unit.

    Args:
        speed_mbps: Speed in megabits per second

    Returns:
        Formatted speed string

    Example:
        >>> format_speed(1500.5)
        '1.50 Gbps'
        >>> format_speed(50.3)
        '50.30 Mbps'
    """
    if speed_mbps >= 1000:
        return f"{speed_mbps / 1000:.2f} Gbps"
    return f"{speed_mbps:.2f} Mbps"


def format_ping(ping_ms: float) -> str:
    """
    Format ping time with proper unit.

    Args:
        ping_ms: Ping time in milliseconds

    Returns:
        Formatted ping string

    Example:
        >>> format_ping(15.5)
        '15.50 ms'
    """
    return f"{ping_ms:.2f} ms"
