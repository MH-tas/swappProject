"""
Cisco Manager - Clean Modular Edition
=====================================
Professional Cisco switch management with clean architecture.
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Import our modular components
from cisco_exceptions import CiscoManagerError, CiscoConnectionError, CiscoCommandError
from cisco_models import DeviceConnection, PerformanceStats
from cisco_decorators import performance_monitor, retry_on_failure
from cisco_parsers import CiscoParser
import config
import cache_manager

# Setup logging
logger = logging.getLogger('cisco_manager')
perf_logger = logging.getLogger('performance')

class CiscoManager:
    """Clean, modular Cisco device management"""
    
    def __init__(self):
        """Initialize the Cisco Manager"""
        self.connection = None
        self.connected = False
        self.device_info = {}
        self.last_error = None
        self.connection_health = True
        self.last_command_time = time.time()
        self.connection_lock = threading.RLock()
        self.callbacks = {}
        
        # Performance statistics
        self.stats = PerformanceStats()
        
        # Initialize parser
        self.parser = CiscoParser()
        
        logger.info("Clean CiscoManager initialized")
    
    def register_callback(self, event: str, callback) -> None:
        """Register callback for events"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    def trigger_callback(self, event: str, data: Any = None) -> None:
        """Trigger registered callbacks"""
        try:
            if event in self.callbacks:
                for callback in self.callbacks[event]:
                    if callable(callback):
                        callback(data)
        except Exception as e:
            logger.error(f"Callback error for {event}: {e}")
    
    @performance_monitor("connection")
    def connect(self, host: str, username: str, password: str, 
                device_type: str = 'cisco_ios', port: int = 22, 
                secret: Optional[str] = None) -> bool:
        """Connect to Cisco device"""
        with self.connection_lock:
            try:
                self.stats.connection_attempts += 1
                logger.info(f"Connecting to {host}:{port}")
                
                # Get device configuration
                device_config = config.get_device_config(host, username, password, secret)
                
                # Establish connection
                self.connection = ConnectHandler(**device_config)
                
                # Test connection
                test_output = self.connection.send_command('show version', delay_factor=3)
                if not test_output or len(test_output) < 50:
                    raise CiscoConnectionError("Connection test failed")
                
                # Enter enable mode if needed
                if secret:
                    self.connection.enable()
                
                # Setup terminal
                self._setup_terminal()
                
                self.connected = True
                self.connection_health = True
                self.stats.successful_connections += 1
                
                # Get device info
                self.device_info = self._get_device_info()
                
                logger.info(f"Connected to {host}")
                self.trigger_callback('connected', self.device_info)
                return True
                
            except Exception as e:
                self.stats.errors += 1
                error_msg = f"Connection failed: {str(e)}"
                logger.error(error_msg)
                self.last_error = error_msg
                self.trigger_callback('connection_failed', error_msg)
                return False
    
    def disconnect(self) -> bool:
        """Disconnect from device"""
        with self.connection_lock:
            try:
                if self.connection:
                    self.connection.disconnect()
                
                self.connection = None
                self.connected = False
                self.device_info = {}
                self.trigger_callback('disconnected')
                return True
                
            except Exception as e:
                logger.error(f"Disconnect error: {e}")
                return False
    
    def _setup_terminal(self) -> None:
        """Setup terminal for better output"""
        try:
            self.connection.send_command("terminal length 0", cmd_verify=False)
            self.connection.send_command("terminal width 0", cmd_verify=False)
            self.connection.clear_buffer()
        except Exception as e:
            logger.warning(f"Terminal setup failed: {e}")
    
    def _get_device_info(self) -> Dict[str, str]:
        """Get basic device information"""
        try:
            version_output = self.send_command("show version")
            return self.parser.parse_device_info(version_output)
        except Exception:
            return {}
    
    @performance_monitor("send_command")
    def send_command(self, command: str, delay_factor: int = 1, use_cache: bool = False) -> str:
        """Send command to device"""
        if not self.connected:
            raise CiscoCommandError("Device not connected")
        
        # Check cache
        if use_cache:
            cache_key = (self.connection.host, command)
            cached = cache_manager.command_cache.get(cache_key)
            if cached:
                self.stats.cache_hits += 1
                return cached
            self.stats.cache_misses += 1
        
        try:
            self.stats.commands_executed += 1
            
            output = self.connection.send_command(
                command,
                delay_factor=delay_factor,
                read_timeout=30,
                cmd_verify=False
            )
            
            # Cache result
            if use_cache and output:
                cache_manager.command_cache.set(cache_key, output, ttl=60)
            
            return output.strip()
            
        except Exception as e:
            self.stats.errors += 1
            raise CiscoCommandError(f"Command failed: {e}")
    
    @performance_monitor("interface_status")
    def get_interfaces_status(self, fast_mode: bool = True) -> Dict[str, Dict[str, str]]:
        """Get interface status with multiple fallback methods"""
        try:
            logger.debug("Getting interface status")
            
            # Method 1: show interfaces status
            try:
                output = self.send_command("show interfaces status", delay_factor=2, use_cache=True)
                logger.debug(f"Method 1 output: {len(output)} chars")
                
                if output and len(output) > 100:
                    if fast_mode:
                        interfaces = self.parser.parse_interface_status_fast(output)
                    else:
                        interfaces = self.parser.parse_interface_status_enhanced(output)
                    
                    if len(interfaces) > 0:
                        logger.info(f"Method 1 SUCCESS: {len(interfaces)} interfaces")
                        return interfaces
                
            except Exception as e:
                logger.warning(f"Method 1 failed: {e}")
            
            # Method 2: show ip interface brief
            try:
                output = self.send_command("show ip interface brief", delay_factor=2, use_cache=True)
                logger.debug(f"Method 2 output: {len(output)} chars")
                
                if output:
                    interfaces = self.parser.parse_interface_brief(output)
                    if len(interfaces) > 0:
                        logger.info(f"Method 2 SUCCESS: {len(interfaces)} interfaces")
                        return interfaces
                
            except Exception as e:
                logger.warning(f"Method 2 failed: {e}")
            
            # Method 3: Basic interfaces
            try:
                output = self.send_command("show interfaces | include Gigabit", delay_factor=3)
                if output:
                    interfaces = self.parser.parse_basic_interfaces(output)
                    if len(interfaces) > 0:
                        logger.info(f"Method 3 SUCCESS: {len(interfaces)} interfaces")
                        return interfaces
                
            except Exception as e:
                logger.warning(f"Method 3 failed: {e}")
            
            # All methods failed
            logger.error("All interface parsing methods failed")
            return {
                "ERROR": {
                    "status": "All parsing methods failed",
                    "vlan": "Check device compatibility",
                    "duplex": "Enable debug logging",
                    "speed": "Contact administrator",
                    "type": "Error",
                    "description": "Interface parsing failed"
                }
            }
            
        except Exception as e:
            logger.error(f"Interface status error: {e}")
            return {"CRITICAL_ERROR": {"status": str(e), "vlan": "Critical error", "duplex": "N/A", "speed": "N/A", "type": "Error", "description": "Critical failure"}}
    
    # Interface management
    @performance_monitor("enable_interface")
    def enable_interface(self, interface: str) -> bool:
        """Enable interface"""
        try:
            commands = [f"interface {interface}", "no shutdown"]
            self.connection.send_config_set(commands)
            logger.info(f"Enabled interface {interface}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable {interface}: {e}")
            return False
    
    @performance_monitor("disable_interface")
    def disable_interface(self, interface: str) -> bool:
        """Disable interface"""
        try:
            commands = [f"interface {interface}", "shutdown"]
            self.connection.send_config_set(commands)
            logger.info(f"Disabled interface {interface}")
            return True
        except Exception as e:
            logger.error(f"Failed to disable {interface}: {e}")
            return False
    
    def set_interface_description(self, interface: str, description: str) -> bool:
        """Set interface description"""
        try:
            commands = [f"interface {interface}", f"description {description}"]
            self.connection.send_config_set(commands)
            return True
        except Exception as e:
            logger.error(f"Failed to set description: {e}")
            return False
    
    def set_interface_vlan(self, interface: str, vlan: int) -> bool:
        """Set interface VLAN"""
        try:
            commands = [
                f"interface {interface}",
                "switchport mode access",
                f"switchport access vlan {vlan}"
            ]
            self.connection.send_config_set(commands)
            return True
        except Exception as e:
            logger.error(f"Failed to set VLAN: {e}")
            return False
    
    # Utility methods
    def get_mac_address_table(self) -> List[Dict[str, str]]:
        """Get MAC address table"""
        try:
            output = self.send_command("show mac address-table")
            return self.parser.parse_mac_table(output)
        except Exception:
            return []
    
    def save_config(self) -> bool:
        """Save configuration"""
        try:
            output = self.send_command("write memory")
            return "OK" in output or "success" in output.lower()
        except Exception:
            return False
    
    # Status methods
    def is_connected(self) -> bool:
        """Check connection status"""
        return self.connected and self.connection is not None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'commands_executed': self.stats.commands_executed,
            'cache_hits': self.stats.cache_hits,
            'cache_misses': self.stats.cache_misses,
            'connection_attempts': self.stats.connection_attempts,
            'successful_connections': self.stats.successful_connections,
            'errors': self.stats.errors,
            'cache_hit_ratio': (self.stats.cache_hits / max(1, self.stats.cache_hits + self.stats.cache_misses)) * 100,
            'connection_health': self.connection_health
        }
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        cache_manager.clear_all_caches()
        logger.info("Caches cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """System health check"""
        health = {
            'connected': self.is_connected(),
            'connection_health': self.connection_health,
            'last_error': self.last_error,
            'stats': self.get_performance_stats()
        }
        
        if self.is_connected():
            try:
                self.send_command("show clock", delay_factor=1)
                health['connectivity_test'] = 'PASS'
            except:
                health['connectivity_test'] = 'FAIL'
                health['connection_health'] = False
        
        return health 