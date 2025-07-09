#!/usr/bin/env python3
"""
Professional Configuration Management
Centralized configuration for Cisco Switch Manager

Author: Professional Network Management Team
Version: 2.0.0
Date: 2024-12-20
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ConnectionConfig:
    """Connection configuration with optimized defaults"""
    timeout: int = 120
    session_timeout: int = 120
    global_delay_factor: int = 3  # Optimized from 5
    conn_timeout: int = 45
    read_timeout: int = 60
    max_loops: int = 1000
    keepalive: int = 30
    fast_cli: bool = False
    auto_connect: bool = True
    
    # Buffer management settings
    clear_buffer_delay: float = 0.3
    cmd_verify: bool = False
    strip_prompt: bool = True
    strip_command: bool = True
    normalize: bool = True
    use_textfsm: bool = False
    
    # SSH timing settings for buffer stability
    config_mode_delay: float = 0.5
    command_delay: float = 0.2
    exit_config_delay: float = 0.3


@dataclass
class UIConfig:
    """UI configuration settings"""
    window_width: int = 1600
    window_height: int = 1000
    min_width: int = 1200
    min_height: int = 800
    theme: str = 'clam'
    font_family: str = 'Segoe UI'
    font_size: int = 9
    console_font: str = 'Consolas'
    auto_refresh_interval: int = 2  # seconds (faster default)
    notification_limit: int = 100
    log_display_lines: int = 500


@dataclass
class PerformanceConfig:
    """Performance optimization settings"""
    cache_ttl: int = 30  # seconds
    max_concurrent_commands: int = 3
    command_retry_attempts: int = 2
    interface_batch_size: int = 50
    background_refresh: bool = True
    lazy_loading: bool = True
    compression: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = 'INFO'
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_dir: str = 'logs'
    enable_console: bool = True
    enable_file: bool = True
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class ConfigManager:
    """Professional configuration manager with persistence"""
    
    def __init__(self):
        self.config_file = Path("cisco_manager_config.json")
        self.connection = ConnectionConfig()
        self.ui = UIConfig()
        self.performance = PerformanceConfig()
        self.logging = LoggingConfig()
        
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Update configurations
                if 'connection' in data:
                    self.connection = ConnectionConfig(**data['connection'])
                if 'ui' in data:
                    self.ui = UIConfig(**data['ui'])
                if 'performance' in data:
                    self.performance = PerformanceConfig(**data['performance'])
                if 'logging' in data:
                    self.logging = LoggingConfig(**data['logging'])
                    
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            # Use defaults
    
    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            config_data = {
                'connection': asdict(self.connection),
                'ui': asdict(self.ui),
                'performance': asdict(self.performance),
                'logging': asdict(self.logging)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.connection = ConnectionConfig()
        self.ui = UIConfig()
        self.performance = PerformanceConfig()
        self.logging = LoggingConfig()
        self.save_config()
    
    def get_device_config(self, host: str, username: str, password: str, 
                         secret: Optional[str] = None) -> Dict[str, Any]:
        """Get optimized device configuration"""
        return {
            'device_type': 'cisco_ios',
            'host': host,
            'username': username,
            'password': password,
            'secret': secret,
            'port': 22,
            'timeout': self.connection.timeout,
            'session_timeout': self.connection.session_timeout,
            'global_delay_factor': self.connection.global_delay_factor,
            'conn_timeout': self.connection.conn_timeout,
            'read_timeout_override': self.connection.read_timeout,
            'fast_cli': self.connection.fast_cli,
            'auto_connect': self.connection.auto_connect,
            'keepalive': self.connection.keepalive
        }


# Global configuration instance
config = ConfigManager() 