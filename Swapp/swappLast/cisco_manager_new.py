"""
Cisco Manager - Main Module
============================
Modular Cisco switch management system with clean architecture.
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Import our custom modules
from cisco_exceptions import CiscoManagerError, CiscoConnectionError, CiscoCommandError
from cisco_models import DeviceConnection, InterfaceInfo, PerformanceStats, DeviceInfo
from cisco_decorators import performance_monitor, retry_on_failure
from cisco_parsers import CiscoParser
import config
import cache_manager

# Setup logging
logger = logging.getLogger('cisco_manager')
perf_logger = logging.getLogger('performance')

class CiscoManager:
    """Professional Cisco device management with modular architecture"""
    
    def __init__(self):
        """Initialize the Cisco Manager with optimized settings"""
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
        
        logger.info("Modular CiscoManager initialized successfully")
    
    def register_callback(self, event: str, callback) -> None:
        """Register callback for events"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        logger.debug(f"Callback registered for event: {event}")
    
    def trigger_callback(self, event: str, data: Any = None) -> None:
        """Trigger registered callbacks"""
        try:
            if event in self.callbacks:
                for callback in self.callbacks[event]:
                    if callable(callback):
                        callback(data)
        except Exception as e:
            logger.error(f"Error triggering callback for {event}: {e}")
    
    @performance_monitor("connection")
    @retry_on_failure(max_attempts=config.performance.command_retry_attempts)
    def connect(self, host: str, username: str, password: str, 
                device_type: str = 'cisco_ios', port: int = 22, 
                secret: Optional[str] = None) -> bool:
        """
        Establish connection to Cisco device
        
        Args:
            host: Device IP address or hostname
            username: SSH username
            password: SSH password
            device_type: Device type (default: cisco_ios)
            port: SSH port (default: 22)
            secret: Enable secret (optional)
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        with self.connection_lock:
            try:
                self.stats.connection_attempts += 1
                logger.info(f"Connecting to {host}:{port}")
                
                # Get optimized device configuration
                device_config = config.get_device_config(host, username, password, secret)
                
                # Establish connection
                connection_start = time.time()
                self.connection = ConnectHandler(**device_config)
                connection_time = time.time() - connection_start
                perf_logger.info(f"Connection established in {connection_time:.3f}s")
                
                # Test connection
                test_output = self.connection.send_command('show version', 
                                                         delay_factor=3, 
                                                         read_timeout=60,
                                                         cmd_verify=False)
                if not test_output or len(test_output) < 50:
                    raise CiscoConnectionError("Connection test failed - no valid output")
                
                # Enter enable mode if secret provided
                if secret:
                    self.connection.enable()
                    logger.info("Entered enable mode")
                
                # Setup terminal for better compatibility
                self._setup_terminal()
                
                self.connected = True
                self.last_error = None
                self.connection_health = True
                self.last_command_time = time.time()
                self.stats.successful_connections += 1
                
                # Get basic device information
                self.device_info = self._get_device_info()
                
                logger.info(f"Successfully connected to {host}")
                self.trigger_callback('connected', self.device_info)
                
                return True
                
            except NetmikoAuthenticationException as e:
                self.stats.errors += 1
                error_msg = f"Authentication failed for {host}: {str(e)}"
                logger.error(error_msg)
                self.last_error = error_msg
                self.connection_health = False
                self.trigger_callback('connection_failed', error_msg)
                return False
                
            except NetmikoTimeoutException as e:
                self.stats.errors += 1
                error_msg = f"Connection timeout to {host}: {str(e)}"
                logger.error(error_msg)
                self.last_error = error_msg
                self.connection_health = False
                self.trigger_callback('connection_failed', error_msg)
                return False
                
            except Exception as e:
                self.stats.errors += 1
                error_msg = f"Connection failed to {host}: {str(e)}"
                logger.error(error_msg)
                self.last_error = error_msg
                self.connection_health = False
                self.trigger_callback('connection_failed', error_msg)
                return False
    
    def disconnect(self) -> bool:
        """Safely disconnect from device"""
        with self.connection_lock:
            try:
                if self.connection:
                    self.connection.disconnect()
                    logger.info("Disconnected from device")
                
                self.connection = None
                self.connected = False
                self.device_info = {}
                self.trigger_callback('disconnected')
                return True
                
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
                return False
    
    def _setup_terminal(self) -> None:
        """Setup terminal for optimal command execution"""
        try:
            logger.debug("Setting up terminal")
            
            # Disable paging
            self.connection.send_command("terminal length 0", 
                                       delay_factor=2, 
                                       read_timeout=30,
                                       cmd_verify=False)
            
            # Set terminal width
            self.connection.send_command("terminal width 0", 
                                       delay_factor=2, 
                                       read_timeout=30,
                                       cmd_verify=False)
            
            # Clear buffer
            self.connection.clear_buffer()
            logger.debug("Terminal setup completed")
            
        except Exception as e:
            logger.warning(f"Terminal setup failed (not critical): {e}")
    
    def _get_device_info(self) -> Dict[str, str]:
        """Get basic device information"""
        try:
            version_output = self.send_command("show version")
            return self.parser.parse_device_info(version_output)
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return {}
    
    @performance_monitor("send_command")
    def send_command(self, command: str, expect_string: Optional[str] = None, 
                    delay_factor: int = 1, use_cache: bool = False) -> str:
        """
        Send command to device with error handling
        
        Args:
            command: CLI command to send
            expect_string: Expected string in response
            delay_factor: Delay multiplier for slow commands
            use_cache: Whether to use cached results
            
        Returns:
            str: Command output
            
        Raises:
            CiscoCommandError: If command fails or device not connected
        """
        if not self.connected or not self.connection:
            raise CiscoCommandError("Device not connected")
        
        # Check cache for command result
        if use_cache:
            cache_key = (self.connection.host, command, delay_factor)
            cached_result = cache_manager.command_cache.get(cache_key)
            if cached_result:
                self.stats.cache_hits += 1
                logger.debug(f"Command '{command}' served from cache")
                return cached_result
            else:
                self.stats.cache_misses += 1
        
        try:
            self.stats.commands_executed += 1
            self.last_command_time = time.time()
            logger.debug(f"Sending command: {command}")
            
            # Clear buffer before sending command
            try:
                self.connection.clear_buffer()
            except:
                pass  # Not critical if this fails
            
            # Send command with optimized parameters
            read_timeout = 60 if delay_factor > 2 else 30
            
            output = self.connection.send_command(
                command, 
                expect_string=expect_string,
                delay_factor=delay_factor,
                max_loops=1500,
                read_timeout=read_timeout,
                cmd_verify=False,
                strip_prompt=False,
                strip_command=False
            )
            
            logger.debug(f"Command output length: {len(output)} characters")
            
            # Basic validation
            if output is None:
                raise CiscoCommandError("Command returned None")
            
            # Clean the output
            output = output.strip()
            
            # Cache the result if caching is enabled
            if use_cache and output:
                cache_key = (self.connection.host, command, delay_factor)
                cache_manager.command_cache.set(cache_key, output, ttl=60)
                logger.debug(f"Cached result for command '{command}'")
            
            return output
            
        except Exception as e:
            self.stats.errors += 1
            error_msg = f"Command '{command}' failed: {str(e)}"
            logger.error(error_msg)
            raise CiscoCommandError(error_msg)
    
    def send_config_commands(self, commands: List[str]) -> str:
        """Send configuration commands"""
        if not self.connected or not self.connection:
            raise CiscoCommandError("Device not connected")
        
        try:
            logger.info(f"Sending config commands: {commands}")
            output = self.connection.send_config_set(commands)
            logger.info("Configuration commands sent successfully")
            return output
            
        except Exception as e:
            error_msg = f"Configuration failed: {str(e)}"
            logger.error(error_msg)
            raise CiscoCommandError(error_msg)
    
    @performance_monitor("interface_status")
    def get_interfaces_status(self, use_cache: bool = True, fast_mode: bool = True) -> Dict[str, Dict[str, str]]:
        """
        Get interface status information with enhanced debugging
        
        Args:
            use_cache: Use cached results if available
            fast_mode: Use fast parsing (less detailed but much faster)
        
        Returns:
            Dict: Interface name -> status information
        """
        try:
            # Check cache first
            if use_cache:
                cache_key = (self.connection.host if self.connection else 'unknown', 'interfaces', fast_mode)
                cached_interfaces = cache_manager.interface_cache.get(cache_key)
                if cached_interfaces:
                    self.stats.cache_hits += 1
                    logger.debug(f"Retrieved {len(cached_interfaces)} interfaces from cache")
                    return cached_interfaces
                else:
                    self.stats.cache_misses += 1
            
            logger.debug(f"Getting interface status from device (fast_mode={fast_mode})")
            
            # Try multiple commands with fallback strategy
            interfaces = {}
            commands_tried = []
            
            # Method 1: 'show interfaces status'
            try:
                logger.debug("Trying Method 1: 'show interfaces status'")
                commands_tried.append("show interfaces status")
                
                output = self.send_command("show interfaces status", delay_factor=2, use_cache=True)
                
                # DEBUG: Log output for troubleshooting
                logger.debug(f"Method 1 - Output length: {len(output) if output else 0} characters")
                if output:
                    lines = output.split('\n')[:5]
                    logger.debug(f"First 5 lines:\n" + '\n'.join(f"  {i+1}: '{line}'" for i, line in enumerate(lines)))
                
                if output and len(output) > 100:
                    if fast_mode:
                        interfaces = self.parser.parse_interface_status_fast(output)
                    else:
                        interfaces = self.parser.parse_interface_status_enhanced(output)
                    
                    logger.info(f"Method 1 SUCCESS: {len(interfaces)} interfaces")
                
            except Exception as e:
                logger.warning(f"Method 1 failed: {e}")
            
            # Method 2: Fallback to 'show ip interface brief'
            if len(interfaces) < 5:
                try:
                    logger.debug("Trying Method 2: 'show ip interface brief'")
                    commands_tried.append("show ip interface brief")
                    
                    output = self.send_command("show ip interface brief", delay_factor=2, use_cache=True)
                    
                    logger.debug(f"Method 2 - Output length: {len(output) if output else 0} characters")
                    
                    if output and len(output) > 50:
                        method2_interfaces = self.parser.parse_interface_brief(output)
                        if len(method2_interfaces) > len(interfaces):
                            interfaces = method2_interfaces
                            logger.info(f"Method 2 SUCCESS: {len(interfaces)} interfaces")
                
                except Exception as e:
                    logger.warning(f"Method 2 failed: {e}")
            
            # Method 3: Emergency fallback
            if len(interfaces) < 3:
                try:
                    logger.debug("Trying Method 3: Basic interfaces")
                    commands_tried.append("show interfaces | include Gigabit")
                    
                    output = self.send_command("show interfaces | include Gigabit", delay_factor=3, use_cache=True)
                    
                    if output:
                        method3_interfaces = self.parser.parse_basic_interfaces(output)
                        if len(method3_interfaces) > len(interfaces):
                            interfaces = method3_interfaces
                            logger.info(f"Method 3 SUCCESS: {len(interfaces)} interfaces")
                
                except Exception as e:
                    logger.warning(f"Method 3 failed: {e}")
            
            # If all methods failed, create diagnostic info
            if not interfaces:
                logger.error(f"ALL METHODS FAILED! Commands tried: {', '.join(commands_tried)}")
                interfaces = {
                    "DEBUG_INFO": {
                        "status": "Parsing failed - check logs",
                        "vlan": f"Commands: {', '.join(commands_tried)}",
                        "duplex": "Enable debug logging",
                        "speed": "Check device compatibility",
                        "type": "Diagnostic",
                        "description": "All parsing methods failed"
                    }
                }
            
            # Cache results
            if interfaces and use_cache and "DEBUG_INFO" not in interfaces:
                cache_key = (self.connection.host if self.connection else 'unknown', 'interfaces', fast_mode)
                ttl = 30 if fast_mode else config.performance.cache_ttl
                cache_manager.interface_cache.set(cache_key, interfaces, ttl=ttl)
                logger.debug(f"Cached {len(interfaces)} interfaces")
            
            logger.info(f"Interface retrieval completed - {len(interfaces)} interfaces found")
            return interfaces
            
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"CRITICAL ERROR in get_interfaces_status: {e}")
            return {
                "CRITICAL_ERROR": {
                    "status": f"Exception: {str(e)}",
                    "vlan": "Critical parsing failure",
                    "duplex": "Check connection",
                    "speed": "Restart application",
                    "type": "Fatal Error",
                    "description": "Contact administrator"
                }
            }
    
    # Interface management methods
    @performance_monitor("enable_interface")
    @retry_on_failure(max_attempts=2)
    def enable_interface(self, interface: str) -> bool:
        """Enable an interface"""
        try:
            commands = [f"interface {interface}", "no shutdown"]
            self.send_config_commands(commands)
            logger.info(f"Interface {interface} enabled")
            return True
        except Exception as e:
            logger.error(f"Failed to enable interface {interface}: {e}")
            return False
    
    @performance_monitor("disable_interface")
    @retry_on_failure(max_attempts=2)
    def disable_interface(self, interface: str) -> bool:
        """Disable an interface"""
        try:
            commands = [f"interface {interface}", "shutdown"]
            self.send_config_commands(commands)
            logger.info(f"Interface {interface} disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable interface {interface}: {e}")
            return False
    
    def set_interface_description(self, interface: str, description: str) -> bool:
        """Set interface description"""
        try:
            commands = [f"interface {interface}", f"description {description}"]
            self.send_config_commands(commands)
            logger.info(f"Description set for interface {interface}: {description}")
            return True
        except Exception as e:
            logger.error(f"Failed to set description for interface {interface}: {e}")
            return False
    
    def set_interface_vlan(self, interface: str, vlan: int) -> bool:
        """Set interface access VLAN"""
        try:
            commands = [
                f"interface {interface}",
                "switchport mode access",
                f"switchport access vlan {vlan}"
            ]
            self.send_config_commands(commands)
            logger.info(f"VLAN {vlan} set for interface {interface}")
            return True
        except Exception as e:
            logger.error(f"Failed to set VLAN for interface {interface}: {e}")
            return False
    
    # Utility methods
    def get_mac_address_table(self, use_cache: bool = True) -> List[Dict[str, str]]:
        """Get MAC address table"""
        try:
            if use_cache:
                cache_key = (self.connection.host if self.connection else 'unknown', 'mac_table')
                cached_result = cache_manager.mac_cache.get(cache_key)
                if cached_result:
                    self.stats.cache_hits += 1
                    return cached_result
                else:
                    self.stats.cache_misses += 1
            
            output = self.send_command("show mac address-table")
            result = self.parser.parse_mac_table(output)
            
            if use_cache and result:
                cache_key = (self.connection.host if self.connection else 'unknown', 'mac_table')
                cache_manager.mac_cache.set(cache_key, result, ttl=120)
            
            return result
        except Exception as e:
            logger.error(f"Error getting MAC address table: {e}")
            return []
    
    def get_arp_table(self) -> List[Dict[str, str]]:
        """Get ARP table"""
        try:
            output = self.send_command("show arp")
            return self.parser.parse_arp_table(output)
        except Exception as e:
            logger.error(f"Error getting ARP table: {e}")
            return []
    
    def save_config(self) -> bool:
        """Save running configuration"""
        try:
            output = self.send_command("write memory")
            if "OK" in output or "success" in output.lower():
                logger.info("Configuration saved successfully")
                return True
            else:
                logger.warning("Configuration save may have failed")
                return False
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    # Status and monitoring methods
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.connected and self.connection is not None
    
    def get_last_error(self) -> Optional[str]:
        """Get last error message"""
        return self.last_error
    
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
            'connection_health': self.connection_health,
            'last_command_time': self.last_command_time
        }
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        cache_manager.clear_all_caches()
        logger.info("All caches cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        health = {
            'connected': self.is_connected(),
            'connection_health': self.connection_health,
            'last_error': self.last_error,
            'stats': self.get_performance_stats()
        }
        
        # Test basic connectivity if connected
        if self.is_connected():
            try:
                test_output = self.send_command("show clock", delay_factor=1)
                health['connectivity_test'] = 'PASS' if test_output else 'FAIL'
            except:
                health['connectivity_test'] = 'FAIL'
                health['connection_health'] = False
        
        return health 