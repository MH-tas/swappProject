#!/usr/bin/env python3
"""
Cisco Device Management Module
Professional Cisco switch management with comprehensive error handling and logging.

Author: Professional Network Management Team
Version: 2.0.0
Date: 2024-12-20
"""

import re
import time
import logging
import threading
import asyncio
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from functools import wraps
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Import our performance modules
from config import config
from cache_manager import cache_manager


# Professional logging configuration
import logging.handlers
import os

def setup_professional_logging():
    """Setup professional logging with rotation and performance optimizations"""
    # Ensure log directory exists
    log_dir = config.logging.log_dir
    os.makedirs(log_dir, exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.logging.level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler (if enabled)
    if config.logging.enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation (if enabled)
    if config.logging.enable_file:
        log_file = os.path.join(log_dir, 'cisco_manager.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.logging.max_file_size,
            backupCount=config.logging.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(config.logging.format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Performance logger (separate file)
    perf_logger = logging.getLogger('performance')
    perf_file = os.path.join(log_dir, 'performance.log')
    perf_handler = logging.handlers.RotatingFileHandler(
        perf_file, maxBytes=5*1024*1024, backupCount=3
    )
    perf_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    perf_handler.setFormatter(perf_formatter)
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)

# Setup logging
setup_professional_logging()
logger = logging.getLogger(__name__)
perf_logger = logging.getLogger('performance')


def performance_monitor(operation_name: str):
    """Decorator to monitor operation performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation_id = f"{operation_name}_{int(start_time)}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                perf_logger.info(f"{operation_name} completed in {duration:.3f}s")
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                perf_logger.error(f"{operation_name} failed after {duration:.3f}s: {e}")
                raise
                
        return wrapper
    return decorator


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, 
                    backoff_factor: float = 2.0):
    """Decorator for automatic retry with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"Final attempt failed for {func.__name__}: {e}")
                        raise
                    
                    wait_time = delay * (backoff_factor ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                                 f"Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    
        return wrapper
    return decorator


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


class CiscoManagerError(Exception):
    """Custom exception for Cisco Manager operations"""
    pass


class CiscoManager:
    """
    Professional Cisco device management class with comprehensive error handling,
    logging, monitoring, caching, and performance optimizations.
    """
    
    def __init__(self):
        """Initialize the Professional Cisco Manager"""
        self.connection = None
        self.connected = False
        self.device_info = {}
        self.callbacks = {}
        self.last_error = None
        self.connection_lock = threading.RLock()
        
        # Performance optimizations
        self.command_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=config.performance.max_concurrent_commands,
            thread_name_prefix="cisco_cmd"
        )
        
        # Connection health monitoring
        self.last_command_time = 0
        self.connection_health = True
        self.health_check_interval = 30
        
        # Statistics
        self.stats = {
            'commands_executed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'connection_attempts': 0,
            'successful_connections': 0,
            'errors': 0
        }
        
        logger.info("Professional CiscoManager initialized with caching and performance optimizations")
    
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
        Establish connection to Cisco device with comprehensive error handling
        
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
                self.stats['connection_attempts'] += 1
                logger.info(f"Attempting professional connection to {host}:{port}")
                
                # Check cache for recent connection info
                cache_key = (host, username, 'connection_info')
                cached_info = cache_manager.device_cache.get(cache_key)
                if cached_info:
                    logger.debug("Using cached connection optimization")
                
                # Use optimized configuration from config manager
                device_config = config.get_device_config(host, username, password, secret)
                
                # Establish connection with performance monitoring
                connection_start = time.time()
                self.connection = ConnectHandler(**device_config)
                connection_time = time.time() - connection_start
                perf_logger.info(f"Connection established in {connection_time:.3f}s")
                
                # Test connection with basic command
                logger.debug("Testing connection with 'show version'")
                test_output = self.connection.send_command('show version', 
                                                         delay_factor=3, 
                                                         read_timeout=60,
                                                         cmd_verify=False)
                if not test_output or len(test_output) < 50:
                    raise CiscoManagerError("Connection test failed - no valid output")
                
                if 'Invalid' in test_output or 'Unknown command' in test_output:
                    raise CiscoManagerError("Connection test failed - invalid command response")
                
                logger.debug("Connection test successful")
                
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
                self.stats['successful_connections'] += 1
                
                # Get basic device information with caching
                self.device_info = self._get_basic_device_info()
                
                # Cache successful connection info
                cache_manager.device_cache.set(cache_key, {
                    'device_info': self.device_info,
                    'connection_time': connection_time,
                    'optimization_hints': device_config
                }, ttl=300)
                
                logger.info(f"Successfully connected to {host} (stats: {self.stats})")
                self.trigger_callback('connected', self.device_info)
                
                return True
                
            except NetmikoAuthenticationException as e:
                self.stats['errors'] += 1
                error_msg = f"Authentication failed for {host}: {str(e)}"
                logger.error(error_msg)
                self.last_error = error_msg
                self.connection_health = False
                self.trigger_callback('connection_failed', error_msg)
                return False
                
            except NetmikoTimeoutException as e:
                self.stats['errors'] += 1
                error_msg = f"Connection timeout to {host}: {str(e)}"
                logger.error(error_msg)
                self.last_error = error_msg
                self.connection_health = False
                self.trigger_callback('connection_failed', error_msg)
                return False
                
            except Exception as e:
                self.stats['errors'] += 1
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
            logger.debug("Setting up terminal for Cisco device")
            
            # Disable paging to prevent more prompts
            self.connection.send_command("terminal length 0", 
                                       delay_factor=2, 
                                       read_timeout=30,
                                       cmd_verify=False)
            
            # Set terminal width for better formatting
            self.connection.send_command("terminal width 0", 
                                       delay_factor=2, 
                                       read_timeout=30,
                                       cmd_verify=False)
            
            # Clear any pending output
            self.connection.clear_buffer()
            
            logger.debug("Terminal setup completed")
            
        except Exception as e:
            logger.warning(f"Terminal setup failed (not critical): {e}")
    
    def _get_basic_device_info(self) -> Dict[str, str]:
        """Get basic device information"""
        try:
            version_output = self.send_command("show version")
            info = {}
            
            # Parse hostname
            hostname_match = re.search(r'(\S+) uptime is', version_output)
            if hostname_match:
                info['hostname'] = hostname_match.group(1)
            
            # Parse model
            model_patterns = [
                r'Model number\s*:\s*(.+)',
                r'cisco\s+(\S+)\s+\(',
                r'Hardware:\s*(\S+)'
            ]
            for pattern in model_patterns:
                match = re.search(pattern, version_output, re.IGNORECASE)
                if match:
                    info['model'] = match.group(1).strip()
                    break
            
            # Parse serial number
            serial_patterns = [
                r'System serial number\s*:\s*(\S+)',
                r'Processor board ID\s+(\S+)'
            ]
            for pattern in serial_patterns:
                match = re.search(pattern, version_output, re.IGNORECASE)
                if match:
                    info['serial'] = match.group(1).strip()
                    break
            
            # Parse IOS version
            ios_match = re.search(r'Version\s+(\S+)', version_output)
            if ios_match:
                info['ios_version'] = ios_match.group(1)
            
            # Parse uptime
            uptime_match = re.search(r'uptime is\s+(.+)', version_output)
            if uptime_match:
                info['uptime'] = uptime_match.group(1).strip()
            
            logger.debug(f"Device info collected: {info}")
            return info
            
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
            
        Returns:
            str: Command output
            
        Raises:
            CiscoManagerError: If command fails or device not connected
        """
        if not self.connected or not self.connection:
            raise CiscoManagerError("Device not connected")
        
        # Check cache for command result
        if use_cache:
            cache_key = (self.connection.host, command, delay_factor)
            cached_result = cache_manager.command_cache.get(cache_key)
            if cached_result:
                self.stats['cache_hits'] += 1
                logger.debug(f"Command '{command}' served from cache")
                return cached_result
            else:
                self.stats['cache_misses'] += 1
        
        try:
            self.stats['commands_executed'] += 1
            self.last_command_time = time.time()
            logger.debug(f"Sending command: {command} (delay_factor={delay_factor})")
            
            # Clear buffer before sending command
            try:
                self.connection.clear_buffer()
            except:
                pass  # Not critical if this fails
            
            # Optimized timeout for faster response
            read_timeout = 60 if delay_factor > 2 else 30  # Reduced for speed
            
            # Try with different approaches for better compatibility
            try:
                output = self.connection.send_command(
                    command, 
                    expect_string=expect_string,
                    delay_factor=delay_factor,
                    max_loops=1500,  # Further increased max loops
                    read_timeout=read_timeout,
                    cmd_verify=False,  # Don't verify command echo
                    strip_prompt=False,  # Don't try to strip prompt automatically
                    strip_command=False  # Don't try to strip command automatically
                )
            except Exception as first_error:
                logger.warning(f"First attempt failed: {first_error}")
                
                # Second attempt with even longer timeout
                try:
                    time.sleep(1)  # Small delay
                    output = self.connection.send_command_timing(
                        command,
                        delay_factor=delay_factor + 2,
                        read_timeout=read_timeout + 30
                    )
                except Exception as second_error:
                    logger.error(f"Second attempt also failed: {second_error}")
                    raise first_error  # Raise the original error
            
            logger.debug(f"Command output length: {len(output)} characters")
            
            # Basic validation
            if output is None:
                raise CiscoManagerError("Command returned None")
            
            # Clean the output
            output = output.strip()
            
            # Remove common prompt artifacts
            lines = output.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                # Skip empty lines and lines that look like prompts
                if line and not line.endswith('#') and not line.endswith('>'):
                    cleaned_lines.append(line)
            
            final_output = '\n'.join(cleaned_lines) if cleaned_lines else output
            
            # Cache the result if caching is enabled
            if use_cache and final_output:
                cache_key = (self.connection.host, command, delay_factor)
                cache_manager.command_cache.set(cache_key, final_output, ttl=60)
                logger.debug(f"Cached result for command '{command}'")
            
            return final_output
            
        except Exception as e:
            self.stats['errors'] += 1
            error_msg = f"Command '{command}' failed: {str(e)}"
            logger.error(error_msg)
            raise CiscoManagerError(error_msg)
    
    def send_config_commands(self, commands: List[str]) -> str:
        """
        Send configuration commands
        
        Args:
            commands: List of configuration commands
            
        Returns:
            str: Configuration output
        """
        if not self.connected or not self.connection:
            raise CiscoManagerError("Device not connected")
        
        try:
            logger.info(f"Sending config commands: {commands}")
            output = self.connection.send_config_set(commands)
            logger.info("Configuration commands sent successfully")
            return output
            
        except Exception as e:
            error_msg = f"Configuration failed: {str(e)}"
            logger.error(error_msg)
            raise CiscoManagerError(error_msg)
    
    def get_device_info(self) -> Dict[str, str]:
        """Get comprehensive device information"""
        if not self.device_info:
            self.device_info = self._get_basic_device_info()
        return self.device_info.copy()
    
    @performance_monitor("interface_status")
    def get_interfaces_status(self, use_cache: bool = True, fast_mode: bool = True) -> Dict[str, Dict[str, str]]:
        """
        Get interface status information with optimized performance and enhanced debugging
        
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
                    self.stats['cache_hits'] += 1
                    logger.debug(f"Retrieved {len(cached_interfaces)} interfaces from cache")
                    return cached_interfaces
                else:
                    self.stats['cache_misses'] += 1
            
            logger.debug(f"Getting interface status from device (fast_mode={fast_mode})")
            
            # Use multiple command strategy with enhanced debugging
            interfaces = {}
            commands_tried = []
            
            # Method 1: Try 'show interfaces status' - most detailed
            try:
                logger.debug("Trying Method 1: 'show interfaces status'")
                commands_tried.append("show interfaces status")
                start_time = time.time()
                
                status_output = self.send_command("show interfaces status", 
                                                delay_factor=2,  # Increased for reliability
                                                use_cache=True)
                
                # DEBUG: Log the actual output for troubleshooting
                logger.debug(f"Raw output length: {len(status_output) if status_output else 0} characters")
                if status_output:
                    # Log first few lines for debugging
                    lines = status_output.split('\n')[:10]  # First 10 lines only
                    logger.debug(f"First 10 lines of output:\n" + '\n'.join(f"  {i+1}: '{line}'" for i, line in enumerate(lines)))
                
                parse_start = time.time()
                
                if status_output and len(status_output) > 100:  # Increased minimum length
                    if fast_mode:
                        interfaces.update(self._parse_interface_status_fast_enhanced(status_output))
                    else:
                        interfaces.update(self._parse_interface_status_enhanced(status_output))
                    
                    parse_time = time.time() - parse_start
                    logger.info(f"Method 1 SUCCESS: Parsed {len(interfaces)} interfaces in {parse_time:.2f}s")
                else:
                    logger.warning(f"Method 1 FAILED: Output too short ({len(status_output) if status_output else 0} chars)")
                    
            except Exception as e:
                logger.warning(f"Method 1 FAILED with exception: {e}")
                interfaces = {}
            
            # Method 2: Fallback to 'show ip interface brief' if Method 1 failed or returned few results
            if len(interfaces) < 5:  # Assume at least 5 interfaces on a switch
                try:
                    logger.debug("Trying Method 2: 'show ip interface brief'")
                    commands_tried.append("show ip interface brief")
                    
                    brief_output = self.send_command("show ip interface brief", 
                                                   delay_factor=2, 
                                                   use_cache=True)
                    
                    # DEBUG: Log the actual output
                    logger.debug(f"Method 2 - Raw output length: {len(brief_output) if brief_output else 0} characters")
                    if brief_output:
                        lines = brief_output.split('\n')[:8]  # First 8 lines
                        logger.debug(f"First 8 lines of brief output:\n" + '\n'.join(f"  {i+1}: '{line}'" for i, line in enumerate(lines)))
                    
                    if brief_output and len(brief_output) > 50:
                        if fast_mode:
                            method2_interfaces = self._parse_interface_brief_fast_enhanced(brief_output)
                        else:
                            method2_interfaces = self._parse_interface_brief_enhanced(brief_output)
                        
                        # Merge or replace interfaces
                        if len(method2_interfaces) > len(interfaces):
                            interfaces = method2_interfaces
                            logger.info(f"Method 2 SUCCESS: Got {len(interfaces)} interfaces (replaced Method 1)")
                        else:
                            logger.info(f"Method 2: Got {len(method2_interfaces)} interfaces (keeping Method 1)")
                
                except Exception as e:
                    logger.warning(f"Method 2 FAILED with exception: {e}")
            
            # Method 3: Emergency fallback to basic 'show interfaces'
            if len(interfaces) < 3:  # Really minimal expectation
                try:
                    logger.debug("Trying Method 3: 'show interfaces | include Gigabit'")
                    commands_tried.append("show interfaces | include Gigabit")
                    
                    basic_output = self.send_command("show interfaces | include Gigabit", 
                                                   delay_factor=3, 
                                                   use_cache=True)
                    
                    logger.debug(f"Method 3 - Raw output length: {len(basic_output) if basic_output else 0} characters")
                    if basic_output:
                        lines = basic_output.split('\n')[:5]
                        logger.debug(f"First 5 lines of basic output:\n" + '\n'.join(f"  {i+1}: '{line}'" for i, line in enumerate(lines)))
                    
                    if basic_output:
                        method3_interfaces = self._parse_basic_interfaces_enhanced(basic_output)
                        if len(method3_interfaces) > len(interfaces):
                            interfaces = method3_interfaces
                            logger.info(f"Method 3 SUCCESS: Got {len(interfaces)} interfaces")
                
                except Exception as e:
                    logger.warning(f"Method 3 FAILED with exception: {e}")
            
            # If all methods failed, create a diagnostic entry
            if not interfaces:
                logger.error(f"ALL METHODS FAILED! Commands tried: {', '.join(commands_tried)}")
                interfaces = {
                    "DIAGNOSTIC_ERROR": {
                        "status": "All parsing methods failed",
                        "vlan": f"Commands tried: {', '.join(commands_tried)}",
                        "duplex": "Check logs for details",
                        "speed": "Debug mode enabled",
                        "type": "Error",
                        "description": "Enable debug logging and check switch compatibility"
                    }
                }
            
            # Skip enrichment in fast mode for speed, but log the decision
            if not fast_mode and interfaces and len(interfaces) > 0 and "DIAGNOSTIC_ERROR" not in interfaces:
                try:
                    logger.debug("Attempting to enrich interface data with descriptions")
                    self._enrich_with_switchport_info_fast(interfaces)
                    logger.debug("Interface enrichment completed")
                except Exception as e:
                    logger.debug(f"Enrichment skipped due to error: {e}")
            
            # Cache the results with appropriate TTL
            if interfaces and use_cache and "DIAGNOSTIC_ERROR" not in interfaces:
                cache_key = (self.connection.host if self.connection else 'unknown', 'interfaces', fast_mode)
                ttl = 30 if fast_mode else config.performance.cache_ttl
                cache_manager.interface_cache.set(cache_key, interfaces, ttl=ttl)
                logger.debug(f"Cached {len(interfaces)} interfaces (TTL: {ttl}s)")
            
            total_time = time.time() - (start_time if 'start_time' in locals() else time.time())
            logger.info(f"Interface retrieval completed in {total_time:.2f}s - {len(interfaces)} interfaces found")
            return interfaces
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"CRITICAL ERROR in get_interfaces_status: {e}")
            return {
                "CRITICAL_ERROR": {
                    "status": f"Exception: {str(e)}",
                    "vlan": "Critical parsing failure",
                    "duplex": "Check connection and device compatibility",
                    "speed": "Restart application",
                    "type": "Fatal Error",
                    "description": "Contact system administrator"
                }
            }

    def _parse_interface_status_enhanced(self, output: str) -> Dict[str, Dict[str, str]]:
        """Enhanced parsing of 'show interfaces status' output with better format detection"""
        interfaces = {}
        lines = output.split('\n')
        
        logger.debug(f"Enhanced parsing: Processing {len(lines)} lines")
        
        # Look for header line with multiple possible formats
        header_found = False
        header_line_index = -1
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Multiple header patterns for different Cisco versions
            header_patterns = [
                ('Port' in line and 'Status' in line),
                ('Interface' in line and 'Status' in line),
                ('Port' in line and 'Name' in line),
                ('Port' in line and 'VLAN' in line),
            ]
            
            if any(header_patterns):
                header_found = True
                header_line_index = i
                logger.debug(f"Header found at line {i+1}: '{line}'")
                break
        
        if not header_found:
            logger.warning("No header found in output, trying to parse without header detection")
        
        # Parse interface lines
        interfaces_found = 0
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines and separators
            if not line or line.startswith('-') or line.startswith('='):
                continue
                
            # Skip header and lines before header
            if header_found and i <= header_line_index:
                continue
            
            # Parse interface status line with enhanced regex
            parts = line.split()
            
            # Must have at least interface name and status
            if len(parts) >= 2:
                interface = parts[0]
                
                # Enhanced interface name detection
                interface_patterns = [
                    interface.startswith('Gi'),  # GigabitEthernet
                    interface.startswith('Fa'),  # FastEthernet  
                    interface.startswith('Te'),  # TenGigabitEthernet
                    interface.startswith('TwoGi'),  # TwoGigabitEthernet
                    interface.startswith('FortyGi'),  # FortyGigabitEthernet
                    interface.startswith('Et'),  # Ethernet (generic)
                    re.match(r'[A-Za-z]+\d+/\d+/\d+', interface),  # Generic pattern like Gi1/0/1
                ]
                
                if any(interface_patterns):
                    status = parts[1] if len(parts) > 1 else 'unknown'
                    vlan = parts[2] if len(parts) > 2 else 'unknown'
                    duplex = parts[3] if len(parts) > 3 else 'unknown'
                    speed = parts[4] if len(parts) > 4 else 'unknown'
                    port_type = ' '.join(parts[5:]) if len(parts) > 5 else 'unknown'
                    
                    interfaces[interface] = {
                        'status': status,
                        'vlan': vlan,
                        'duplex': duplex,
                        'speed': speed,
                        'type': port_type,
                        'description': '',
                        'raw_line': line
                    }
                    interfaces_found += 1
                    
                    # Debug log for first few interfaces
                    if interfaces_found <= 3:
                        logger.debug(f"Parsed interface {interfaces_found}: {interface} -> {status}/{vlan}/{duplex}/{speed}")
        
        logger.debug(f"Enhanced parsing completed: {interfaces_found} interfaces found")
        return interfaces

    def _parse_interface_status_fast_enhanced(self, output: str) -> Dict[str, Dict[str, str]]:
        """Ultra fast parsing with enhanced format detection"""
        interfaces = {}
        lines = output.split('\n')
        
        logger.debug(f"Fast enhanced parsing: Processing {len(lines)} lines")
        
        interfaces_found = 0
        for line in lines:
            # Quick skip for obvious non-data lines
            if (not line or 
                line.startswith('-') or 
                line.startswith('=') or
                'Port' in line or 
                'Name' in line or
                'Interface' in line or
                len(line.strip()) < 10):  # Too short to be a data line
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                interface = parts[0]
                
                # Enhanced quick interface validation - more permissive
                valid_interface = (
                    interface and 
                    len(interface) > 2 and
                    (interface[0] in 'GFTE' or  # Common first letters
                     '/' in interface or        # Contains slash (common in Cisco naming)
                     interface.lower().startswith('et'))  # Ethernet variants
                )
                
                if valid_interface:
                    status = parts[1]
                    
                    interfaces[interface] = {
                        'status': status,
                        'vlan': parts[2] if len(parts) > 2 else 'unknown',
                        'duplex': parts[3] if len(parts) > 3 else 'auto',
                        'speed': parts[4] if len(parts) > 4 else 'auto',
                        'type': 'Ethernet',
                        'description': ''
                    }
                    interfaces_found += 1
                    
                    # Debug first few
                    if interfaces_found <= 3:
                        logger.debug(f"Fast parsed {interfaces_found}: {interface} -> {status}")
        
        logger.debug(f"Fast enhanced parsing completed: {interfaces_found} interfaces found")
        return interfaces

    def _parse_interface_brief_enhanced(self, output: str) -> Dict[str, Dict[str, str]]:
        """Enhanced parsing of 'show ip interface brief' output"""
        interfaces = {}
        lines = output.split('\n')
        
        logger.debug(f"Brief enhanced parsing: Processing {len(lines)} lines")
        
        header_found = False
        interfaces_found = 0
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Look for header with multiple patterns
            if (('Interface' in line and ('IP-Address' in line or 'Status' in line)) or
                ('Interface' in line and 'Protocol' in line)):
                header_found = True
                logger.debug(f"Brief header found: '{line}'")
                continue
                
            # Skip separator lines
            if '---' in line or line.startswith('-') or line.startswith('='):
                continue
            
            # Only process lines after header is found (if we found one)
            if not header_found and 'Interface' not in output:
                # No header found in entire output, try to parse anyway
                pass
            elif not header_found:
                continue
            
            parts = line.split()
            if len(parts) >= 4:  # Interface, IP, Method, Status
                interface = parts[0]
                
                # Enhanced interface validation for brief output
                if (interface and 
                    (interface.startswith(('Gi', 'Fa', 'Te', 'TwoGi', 'FortyGi', 'Et')) or
                     '/' in interface)):
                    
                    ip_address = parts[1] if len(parts) > 1 else 'unassigned'
                    method = parts[2] if len(parts) > 2 else 'unknown'
                    status = parts[3] if len(parts) > 3 else 'unknown'
                    protocol = parts[4] if len(parts) > 4 else 'unknown'
                    
                    interfaces[interface] = {
                        'status': status,
                        'protocol': protocol,
                        'ip_address': ip_address,
                        'method': method,
                        'vlan': 'unknown',
                        'duplex': 'unknown',
                        'speed': 'unknown',
                        'type': 'Ethernet',
                        'description': '',
                        'raw_line': line
                    }
                    interfaces_found += 1
                    
                    if interfaces_found <= 3:
                        logger.debug(f"Brief parsed {interfaces_found}: {interface} -> {status}/{protocol}")
        
        logger.debug(f"Brief enhanced parsing completed: {interfaces_found} interfaces found")
        return interfaces

    def _parse_interface_brief_fast_enhanced(self, output: str) -> Dict[str, Dict[str, str]]:
        """Ultra fast enhanced parsing of 'show ip interface brief' output"""
        interfaces = {}
        lines = output.split('\n')
        
        interfaces_found = 0
        for line in lines:
            if (not line or 
                'Interface' in line or 
                '---' in line or
                len(line.strip()) < 15):  # Brief lines are typically longer
                continue
                
            parts = line.split()
            if len(parts) >= 4:
                interface = parts[0]
                
                # Quick enhanced validation
                if (interface and 
                    len(interface) > 2 and
                    (interface[0] in 'GFTE' or '/' in interface)):
                    
                    status = parts[3]  # Status is typically 4th column
                    
                    interfaces[interface] = {
                        'status': status,
                        'protocol': parts[4] if len(parts) > 4 else 'unknown',
                        'vlan': 'unknown',
                        'duplex': 'unknown',
                        'speed': 'unknown',
                        'type': 'Ethernet',
                        'description': ''
                    }
                    interfaces_found += 1
        
        logger.debug(f"Brief fast enhanced parsing: {interfaces_found} interfaces found")
        return interfaces

    def _parse_basic_interfaces_enhanced(self, output: str) -> Dict[str, Dict[str, str]]:
        """Enhanced parsing of basic 'show interfaces' output"""
        interfaces = {}
        lines = output.split('\n')
        
        logger.debug(f"Basic enhanced parsing: Processing {len(lines)} lines")
        
        interfaces_found = 0
        for line in lines:
            line = line.strip()
            
            # Look for interface status lines with enhanced patterns
            interface_patterns = [
                line.startswith('GigabitEthernet'),
                line.startswith('FastEthernet'),
                line.startswith('TenGigabitEthernet'),
                line.startswith('Ethernet'),
                re.match(r'^[A-Za-z]+\d+/\d+/\d+\s+is\s+', line)  # Generic pattern
            ]
            
            if any(interface_patterns):
                # Parse line like: "GigabitEthernet1/0/1 is down, line protocol is down (notconnect)"
                parts = line.split()
                if len(parts) >= 3:
                    interface = parts[0]
                    
                    # Enhanced status determination
                    line_lower = line.lower()
                    if 'is up' in line_lower and 'line protocol is up' in line_lower:
                        status = 'connected'
                    elif 'is up' in line_lower:
                        status = 'up'
                    elif 'notconnect' in line_lower:
                        status = 'notconnect'
                    elif 'is down' in line_lower:
                        status = 'down'
                    elif 'administratively down' in line_lower:
                        status = 'disabled'
                    else:
                        status = 'unknown'
                    
                    interfaces[interface] = {
                        'status': status,
                        'vlan': 'unknown',
                        'duplex': 'unknown',
                        'speed': 'unknown',
                        'type': 'Ethernet',
                        'description': '',
                        'raw_line': line
                    }
                    interfaces_found += 1
                    
                    if interfaces_found <= 3:
                        logger.debug(f"Basic parsed {interfaces_found}: {interface} -> {status}")
        
        logger.debug(f"Basic enhanced parsing completed: {interfaces_found} interfaces found")
        return interfaces
    
    def _enrich_with_switchport_info_fast(self, interfaces: Dict[str, Dict[str, str]]) -> None:
        """Fast enrichment with switchport info - only essential data"""
        try:
            # Skip enrichment if too many interfaces (performance)
            if len(interfaces) > 48:  # Typical 48-port switch
                logger.debug("Skipping enrichment for large interface count (performance)")
                return
                
            # Get basic switchport info with minimal processing
            try:
                output = self.send_command("show interfaces description", delay_factor=1, use_cache=True)
                self._parse_descriptions_fast(interfaces, output)
            except Exception as e:
                logger.debug(f"Description enrichment failed: {e}")
                
        except Exception as e:
            logger.debug(f"Fast enrichment failed: {e}")
    
    def _parse_descriptions_fast(self, interfaces: Dict[str, Dict[str, str]], output: str) -> None:
        """Fast parsing of interface descriptions"""
        lines = output.split('\n')
        
        for line in lines:
            if not line or 'Interface' in line or '---' in line:
                continue
                
            parts = line.split(None, 2)  # Split on first 2 whitespaces only
            if len(parts) >= 3:
                interface = parts[0]
                description = parts[2] if len(parts) > 2 else ''
                
                if interface in interfaces:
                    interfaces[interface]['description'] = description

    def _enrich_with_switchport_info(self, interfaces: Dict[str, Dict[str, str]]) -> None:
        """Enrich interface data with switchport information"""
        try:
            # Get switchport information
            switchport_output = self.send_command("show interfaces switchport")
            current_interface = None
            
            for line in switchport_output.split('\n'):
                line = line.strip()
                
                # Check for interface line
                if line.startswith('Name:'):
                    current_interface = line.split(':')[1].strip()
                elif current_interface and current_interface in interfaces:
                    # Parse switchport data
                    if 'Administrative Mode:' in line:
                        mode = line.split(':')[1].strip()
                        interfaces[current_interface]['admin_mode'] = mode
                    elif 'Access Mode VLAN:' in line:
                        vlan = line.split(':')[1].split()[0]
                        if vlan.isdigit():
                            interfaces[current_interface]['vlan'] = vlan
                    elif 'Administrative private-vlan' in line:
                        interfaces[current_interface]['pvlan'] = line.split(':')[1].strip()
                        
        except Exception as e:
            logger.warning(f"Could not enrich switchport info: {e}")
    
    def get_interface_details(self, interface: str) -> Dict[str, Any]:
        """Get detailed information for a specific interface"""
        try:
            details = {}
            
            # Get interface status
            status_cmd = f"show interfaces {interface}"
            output = self.send_command(status_cmd)
            details['status_output'] = output
            
            # Parse status information
            details.update(self._parse_interface_details(output))
            
            # Get switchport info
            try:
                switchport_cmd = f"show interfaces {interface} switchport"
                switchport_output = self.send_command(switchport_cmd)
                details['switchport_output'] = switchport_output
                details.update(self._parse_switchport_details(switchport_output))
            except Exception as e:
                logger.debug(f"No switchport info for {interface}: {e}")
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting details for {interface}: {e}")
            return {}
    
    def _parse_interface_details(self, output: str) -> Dict[str, str]:
        """Parse detailed interface information"""
        details = {}
        
        # Parse various interface parameters
        patterns = {
            'mtu': r'MTU\s+(\d+)',
            'bandwidth': r'BW\s+(\d+)',
            'description': r'Description:\s*(.+)',
            'duplex': r'(\w+)-duplex',
            'speed': r'(\d+)Mb/s',
            'media_type': r'media type is\s+(.+)',
            'input_errors': r'(\d+)\s+input errors',
            'output_errors': r'(\d+)\s+output errors',
            'collisions': r'(\d+)\s+collisions',
            'late_collisions': r'(\d+)\s+late collision',
            'input_packets': r'(\d+)\s+packets input',
            'output_packets': r'(\d+)\s+packets output'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                details[key] = match.group(1).strip()
        
        return details
    
    def _parse_switchport_details(self, output: str) -> Dict[str, str]:
        """Parse switchport configuration details"""
        details = {}
        
        patterns = {
            'admin_mode': r'Administrative Mode:\s*(.+)',
            'operational_mode': r'Operational Mode:\s*(.+)',
            'access_vlan': r'Access Mode VLAN:\s*(\d+)',
            'trunk_native_vlan': r'Trunking Native Mode VLAN:\s*(\d+)',
            'trunk_vlans': r'Trunking VLANs Enabled:\s*(.+)',
            'voice_vlan': r'Voice VLAN:\s*(\d+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                details[key] = match.group(1).strip()
        
        return details
    
    @performance_monitor("enable_interface")
    @retry_on_failure(max_attempts=2)
    def enable_interface(self, interface: str) -> bool:
        """Enable an interface"""
        try:
            commands = [
                f"interface {interface}",
                "no shutdown"
            ]
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
            commands = [
                f"interface {interface}",
                "shutdown"
            ]
            self.send_config_commands(commands)
            logger.info(f"Interface {interface} disabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable interface {interface}: {e}")
            return False
    
    def set_interface_description(self, interface: str, description: str) -> bool:
        """Set interface description"""
        try:
            commands = [
                f"interface {interface}",
                f"description {description}"
            ]
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
    
    @performance_monitor("mac_table")
    def get_mac_address_table(self, use_cache: bool = True) -> List[Dict[str, str]]:
        """Get MAC address table"""
        try:
            # Check cache first
            if use_cache:
                cache_key = (self.connection.host if self.connection else 'unknown', 'mac_table')
                cached_result = cache_manager.mac_cache.get(cache_key)
                if cached_result:
                    self.stats['cache_hits'] += 1
                    return cached_result
                else:
                    self.stats['cache_misses'] += 1
            
            output = self.send_command("show mac address-table")
            result = self._parse_mac_table(output)
            
            # Cache the result
            if use_cache and result:
                cache_key = (self.connection.host if self.connection else 'unknown', 'mac_table')
                cache_manager.mac_cache.set(cache_key, result, ttl=120)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting MAC address table: {e}")
            return []
    
    def _parse_mac_table(self, output: str) -> List[Dict[str, str]]:
        """Parse MAC address table output"""
        entries = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or 'Vlan' in line or '---' in line or 'Mac Address' in line:
                continue
            
            parts = line.split()
            if len(parts) >= 4:
                entry = {
                    'vlan': parts[0],
                    'mac_address': parts[1],
                    'type': parts[2],
                    'ports': ' '.join(parts[3:])
                }
                entries.append(entry)
        
        return entries
    
    def get_arp_table(self) -> List[Dict[str, str]]:
        """Get ARP table"""
        try:
            output = self.send_command("show arp")
            return self._parse_arp_table(output)
            
        except Exception as e:
            logger.error(f"Error getting ARP table: {e}")
            return []
    
    def _parse_arp_table(self, output: str) -> List[Dict[str, str]]:
        """Parse ARP table output"""
        entries = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or 'Protocol' in line or 'Internet' in line:
                if not line.startswith('Internet'):
                    continue
            
            parts = line.split()
            if len(parts) >= 6 and parts[0] == 'Internet':
                entry = {
                    'ip_address': parts[1],
                    'age': parts[2],
                    'mac_address': parts[3],
                    'type': parts[4],
                    'interface': parts[5]
                }
                entries.append(entry)
        
        return entries
    
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
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            stats = {}
            
            # CPU usage
            try:
                cpu_output = self.send_command("show processes cpu")
                cpu_match = re.search(r'CPU utilization for five seconds: (\d+)%', cpu_output)
                if cpu_match:
                    stats['cpu_usage'] = int(cpu_match.group(1))
            except Exception:
                pass
            
            # Memory usage
            try:
                memory_output = self.send_command("show memory")
                used_match = re.search(r'Used:\s*(\d+)', memory_output)
                free_match = re.search(r'Free:\s*(\d+)', memory_output)
                if used_match and free_match:
                    used = int(used_match.group(1))
                    free = int(free_match.group(1))
                    total = used + free
                    stats['memory_used'] = used
                    stats['memory_free'] = free
                    stats['memory_total'] = total
                    stats['memory_usage_percent'] = (used / total) * 100 if total > 0 else 0
            except Exception:
                pass
            
            # Interface counts
            try:
                interfaces = self.get_interfaces_status()
                stats['total_interfaces'] = len(interfaces)
                stats['active_interfaces'] = len([i for i in interfaces.values() if i.get('status', '').lower() in ['connected', 'up']])
                stats['inactive_interfaces'] = stats['total_interfaces'] - stats['active_interfaces']
            except Exception:
                pass
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.connected and self.connection is not None
    
    def get_last_error(self) -> Optional[str]:
        """Get last error message"""
        return self.last_error
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        cache_stats = cache_manager.get_all_stats()
        
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = (self.stats['cache_hits'] / max(1, total_requests)) * 100
        
        return {
            'connection_stats': {
                'connection_attempts': self.stats['connection_attempts'],
                'successful_connections': self.stats['successful_connections'],
                'success_rate': (self.stats['successful_connections'] / max(1, self.stats['connection_attempts'])) * 100,
                'connection_health': self.connection_health,
                'last_command_time': self.last_command_time
            },
            'command_stats': {
                'commands_executed': self.stats['commands_executed'],
                'cache_hits': self.stats['cache_hits'],
                'cache_misses': self.stats['cache_misses'],
                'cache_hit_rate': round(cache_hit_rate, 2),
                'errors': self.stats['errors'],
                'error_rate': (self.stats['errors'] / max(1, self.stats['commands_executed'])) * 100
            },
            'cache_stats': cache_stats,
            'memory_usage': {
                'total_cache_memory': sum(
                    stats['memory_usage'] for stats in cache_stats.values()
                ),
                'cache_efficiency': sum(
                    stats['hit_rate'] for stats in cache_stats.values()
                ) / len(cache_stats) if cache_stats else 0
            }
        }
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        cache_manager.clear_all()
        self.stats['cache_hits'] = 0
        self.stats['cache_misses'] = 0
        logger.info("All caches cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health = {
            'connection_healthy': self.connection_health,
            'connected': self.connected,
            'last_command_age': time.time() - self.last_command_time if self.last_command_time else None,
            'cache_healthy': True,
            'memory_usage_ok': True
        }
        
        # Check cache health
        cache_stats = cache_manager.get_all_stats()
        total_memory = sum(stats['memory_usage'] for stats in cache_stats.values())
        if total_memory > 100 * 1024 * 1024:  # 100MB threshold
            health['memory_usage_ok'] = False
            health['cache_healthy'] = False
        
        # Check connection staleness
        if health['last_command_age'] and health['last_command_age'] > 300:  # 5 minutes
            health['connection_stale'] = True
        
        return health 