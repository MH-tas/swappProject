"""
Cisco Manager Data Models
==========================
Data classes and models for Cisco switch management.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class DeviceConnection:
    """Device connection configuration"""
    host: str
    username: str
    password: str
    device_type: str = 'cisco_ios'
    port: int = 22
    secret: Optional[str] = None
    timeout: int = 60
    session_timeout: int = 60

@dataclass
class InterfaceInfo:
    """Interface information structure"""
    name: str
    status: str
    vlan: str
    speed: str
    duplex: str
    type: str
    description: str = ""
    raw_data: str = ""

@dataclass
class PerformanceStats:
    """Performance statistics data"""
    commands_executed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    connection_attempts: int = 0
    successful_connections: int = 0
    errors: int = 0
    avg_response_time: float = 0.0

@dataclass
class DeviceInfo:
    """Basic device information"""
    hostname: str = ""
    model: str = ""
    serial: str = ""
    ios_version: str = ""
    uptime: str = "" 