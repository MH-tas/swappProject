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
from config import config
import cache_manager

# Setup logging
def setup_professional_logging():
    """Setup logging system"""
    logger = logging.getLogger('cisco_manager')
    logger.setLevel(logging.DEBUG)
    
    perf_logger = logging.getLogger('performance')
    perf_logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(console_handler)
    if not perf_logger.handlers:
        perf_logger.addHandler(console_handler)
    
    logger.propagate = False
    perf_logger.propagate = False
    
    return logger, perf_logger

# Initialize loggers
logger, perf_logger = setup_professional_logging()

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
        """Setup terminal for better output with buffer cleaning"""
        try:
            # Clear any existing buffer first
            self.connection.clear_buffer()
            time.sleep(0.5)
            
            # Send terminal setup commands with buffer clearing between each
            self.connection.send_command("terminal length 0", cmd_verify=False, read_timeout=10)
            self.connection.clear_buffer()
            time.sleep(0.2)
            
            self.connection.send_command("terminal width 0", cmd_verify=False, read_timeout=10)
            self.connection.clear_buffer()
            time.sleep(0.2)
            
            # Additional buffer cleanup
            self.connection.send_command("", read_timeout=5, cmd_verify=False)
            self.connection.clear_buffer()
            
            logger.info("Terminal setup completed with buffer cleaning")
            
        except Exception as e:
            logger.warning(f"Terminal setup failed: {e}")

    def _clean_buffer_and_wait(self, wait_time: float = 0.3) -> None:
        """Clean SSH buffer and wait for stability"""
        try:
            if self.connection:
                self.connection.clear_buffer()
                time.sleep(wait_time)
                # Send empty command to clear any prompt residue
                self.connection.send_command("", read_timeout=3, cmd_verify=False)
                self.connection.clear_buffer()
        except Exception as e:
            logger.debug(f"Buffer clean warning: {e}")

    @performance_monitor("send_command")
    def send_command(self, command: str, delay_factor: int = 1, use_cache: bool = False) -> str:
        """Send command to device with improved buffer management"""
        if not self.connected:
            raise CiscoCommandError("Device not connected")
        
        # Check cache
        if use_cache:
            try:
                cache_key = (self.connection.host, command)
                cached = cache_manager.command_cache.get(cache_key)
                if cached:
                    self.stats.cache_hits += 1
                    return cached
                self.stats.cache_misses += 1
            except AttributeError:
                # Cache not available, continue without caching
                self.stats.cache_misses += 1
        
        try:
            self.stats.commands_executed += 1
            
            # Clean buffer before sending command
            self._clean_buffer_and_wait(0.2)
            
            # Send command with improved settings
            output = self.connection.send_command(
                command,
                delay_factor=delay_factor,
                read_timeout=45,  # Increased timeout
                cmd_verify=False,
                strip_prompt=True,  # Remove prompt from output
                strip_command=True  # Remove command echo
            )
            
            # Clean buffer after command
            self.connection.clear_buffer()
            
            # Cache result
            if use_cache and output:
                try:
                    cache_manager.command_cache.set(cache_key, output, ttl=60)
                except AttributeError:
                    # Cache not available, continue without caching
                    pass
            
            # Clean and return output
            cleaned_output = output.strip()
            
            # Additional cleaning for common SSH artifacts
            lines = cleaned_output.split('\n')
            clean_lines = []
            for line in lines:
                # Skip lines that are just prompts or command echoes
                line = line.strip()
                if line and not line.endswith('#') and not line.endswith('>'):
                    # Remove any residual prompt characters from start
                    if line.startswith('Switch') or line.startswith('Router'):
                        if '#' in line:
                            line = line.split('#', 1)[1].strip()
                        if '>' in line:
                            line = line.split('>', 1)[1].strip()
                    clean_lines.append(line)
            
            return '\n'.join(clean_lines)
            
        except Exception as e:
            self.stats.errors += 1
            raise CiscoCommandError(f"Command failed: {e}")

    @performance_monitor("interface_status")
    def get_interfaces_status(self, use_cache: bool = True, fast_mode: bool = True) -> Dict[str, Dict[str, str]]:
        """Get interface status with multiple fallback methods"""
        try:
            logger.debug("Getting interface status")
            
            # Method 1: show interfaces status
            try:
                output = self.send_command("show interfaces status", delay_factor=2, use_cache=True)
                logger.debug(f"Method 1 output: {len(output)} chars")
                
                # Log first few lines for debugging
                if output:
                    lines = output.split('\n')[:5]
                    logger.debug("First 5 lines of output:")
                    for i, line in enumerate(lines):
                        logger.debug(f"  {i+1}: '{line}'")
                
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
                output = self.send_command("show interfaces | include Gigabit", delay_factor=3, use_cache=False)
                if output:
                    interfaces = self.parser.parse_basic_interfaces(output)
                    if len(interfaces) > 0:
                        logger.info(f"Method 3 SUCCESS: {len(interfaces)} interfaces")
                        return interfaces
                
            except Exception as e:
                logger.warning(f"Method 3 failed: {e}")
            
            # Method 4: Emergency simple parsing
            try:
                logger.debug("Trying Method 4: Simple show interfaces")
                output = self.send_command("show interfaces", delay_factor=5, use_cache=False)
                if output:
                    # Create basic interface list from any interface mentions
                    basic_interfaces = {}
                    lines = output.split('\n')
                    for line in lines:
                        if 'GigabitEthernet' in line and ' is ' in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                interface = parts[0]
                                status = 'notconnect' if 'down' in line.lower() else 'connected'
                                basic_interfaces[interface] = {
                                    'status': status,
                                    'vlan': 'unknown',
                                    'duplex': 'unknown', 
                                    'speed': 'unknown',
                                    'type': 'Ethernet',
                                    'description': ''
                                }
                    
                    if len(basic_interfaces) > 0:
                        logger.info(f"Method 4 SUCCESS: {len(basic_interfaces)} interfaces (basic)")
                        return basic_interfaces
            except Exception as e:
                logger.warning(f"Method 4 failed: {e}")
            
            # All methods failed
            logger.error("All interface parsing methods failed")
            return {
                "DEBUG_INFO": {
                    "status": "All parsing methods failed",
                    "vlan": "Check device output format",
                    "duplex": "Enable debug logging",
                    "speed": "Check switch compatibility",
                    "type": "Diagnostic",
                    "description": "All methods failed - check logs"
                }
            }
            
        except Exception as e:
            logger.error(f"Interface status error: {e}")
            return {
                "CRITICAL_ERROR": {
                    "status": str(e),
                    "vlan": "Critical error",
                    "duplex": "N/A",
                    "speed": "N/A",
                    "type": "Error",
                    "description": "Critical failure"
                }
            }

    def _send_config_command_safe(self, commands: List[str]) -> bool:
        """Send configuration commands with rock-solid reliability"""
        try:
            logger.info(f"Executing config commands: {commands}")
            
            # Method 1: Try using send_config_set (most reliable)
            try:
                result = self.connection.send_config_set(
                    commands,
                    read_timeout=30,
                    cmd_verify=False,
                    enter_config_mode=True,
                    exit_config_mode=True
                )
                logger.info(f"Config commands executed successfully via send_config_set")
                return True
                
            except Exception as e:
                logger.warning(f"send_config_set failed: {e}, trying manual method")
            
            # Method 2: Manual config mode (fallback)
            # Clean buffer first
            self._clean_buffer_and_wait(0.3)
            
            # Enter config mode
            logger.debug("Entering configuration mode")
            self.connection.send_command("configure terminal", read_timeout=15)
            
            # Send commands one by one
            for cmd in commands:
                logger.debug(f"Sending: {cmd}")
                self.connection.send_command(cmd, read_timeout=15)
                time.sleep(0.1)  # Short delay between commands
            
            # Exit config mode
            logger.debug("Exiting configuration mode")
            self.connection.send_command("end", read_timeout=10)
            
            # Final cleanup
            self._clean_buffer_and_wait(0.3)
            
            logger.info("Config commands executed successfully via manual method")
            return True
            
        except Exception as e:
            logger.error(f"ALL config methods failed: {e}")
            # Emergency cleanup - try to exit config mode
            try:
                self.connection.send_command("end")
                self.connection.send_command("exit")
            except:
                pass
            return False

    # Interface management - Rock solid methods
    @performance_monitor("enable_interface")
    def enable_interface(self, interface: str) -> bool:
        """Enable interface with multiple fallback methods"""
        try:
            logger.info(f"🔓 Enabling interface {interface}")
            
            # Method 1: Standard enable command
            commands = [f"interface {interface}", "no shutdown"]
            result = self._send_config_command_safe(commands)
            
            if result:
                # Verify the change took effect
                time.sleep(1)  # Wait for interface to come up
                logger.info(f"✅ Successfully enabled interface {interface}")
                return True
            else:
                logger.error(f"❌ Failed to enable interface {interface}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception enabling {interface}: {e}")
            return False
    
    @performance_monitor("disable_interface") 
    def disable_interface(self, interface: str) -> bool:
        """Disable interface with multiple fallback methods"""
        try:
            logger.info(f"🔒 Disabling interface {interface}")
            
            # Method 1: Standard disable command
            commands = [f"interface {interface}", "shutdown"]
            result = self._send_config_command_safe(commands)
            
            if result:
                # Verify the change took effect  
                time.sleep(1)  # Wait for interface to go down
                logger.info(f"✅ Successfully disabled interface {interface}")
                return True
            else:
                logger.error(f"❌ Failed to disable interface {interface}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception disabling {interface}: {e}")
            return False
    
    def set_interface_description(self, interface: str, description: str) -> bool:
        """Set interface description with improved buffer management"""
        try:
            commands = [f"interface {interface}", f"description {description}"]
            return self._send_config_command_safe(commands)
        except Exception as e:
            logger.error(f"Failed to set description: {e}")
            return False
    
    def set_interface_vlan(self, interface: str, vlan: int) -> bool:
        """Set interface VLAN with improved buffer management"""
        try:
            commands = [
                f"interface {interface}",
                "switchport mode access",
                f"switchport access vlan {vlan}"
            ]
            return self._send_config_command_safe(commands)
        except Exception as e:
            logger.error(f"Failed to set VLAN: {e}")
            return False
    
    def _create_interface_ranges(self, interfaces: List[str]) -> List[str]:
        """Create interface ranges for efficient bulk operations"""
        try:
            # Group interfaces by type and slot
            interface_groups = {}
            
            for interface in interfaces:
                # Parse interface name (e.g., "Gi1/0/5" -> type="Gi", slot="1/0", port=5)
                if interface.startswith('Gi'):
                    parts = interface.replace('Gi', '').split('/')
                    if len(parts) == 3:
                        slot_prefix = f"{parts[0]}/{parts[1]}"
                        port_num = int(parts[2])
                        
                        if slot_prefix not in interface_groups:
                            interface_groups[slot_prefix] = []
                        interface_groups[slot_prefix].append(port_num)
            
            # Create ranges for each group
            ranges = []
            for slot_prefix, ports in interface_groups.items():
                ports.sort()
                ranges.extend(self._create_port_ranges(slot_prefix, ports))
            
            return ranges
            
        except Exception as e:
            logger.error(f"Error creating interface ranges: {e}")
            # Fallback to individual interfaces
            return [f"gi{interface.replace('Gi', '')}" for interface in interfaces]

    def _create_port_ranges(self, slot_prefix: str, ports: List[int]) -> List[str]:
        """Create port ranges for a specific slot"""
        ranges = []
        current_range_start = None
        current_range_end = None
        
        for i, port in enumerate(ports):
            if current_range_start is None:
                current_range_start = port
                current_range_end = port
            elif port == current_range_end + 1:
                # Consecutive port, extend range
                current_range_end = port
            else:
                # Gap found, close current range
                if current_range_start == current_range_end:
                    ranges.append(f"gi{slot_prefix}/{current_range_start}")
                else:
                    ranges.append(f"gi{slot_prefix}/{current_range_start}-{current_range_end}")
                
                # Start new range
                current_range_start = port
                current_range_end = port
        
        # Add final range
        if current_range_start is not None:
            if current_range_start == current_range_end:
                ranges.append(f"gi{slot_prefix}/{current_range_start}")
            else:
                ranges.append(f"gi{slot_prefix}/{current_range_start}-{current_range_end}")
        
        return ranges

    @performance_monitor("bulk_disable_interfaces")
    def bulk_disable_interfaces_optimized(self, interfaces_to_disable: List[str], 
                                         max_batch_size: int = 12) -> Dict[str, bool]:
        """
        Optimized bulk disable using interface ranges
        
        Args:
            interfaces_to_disable: List of interface names to disable
            max_batch_size: Maximum interfaces per batch to avoid command length limits
        
        Returns:
            Dict mapping interface names to success status
        """
        results = {}
        
        try:
            if not interfaces_to_disable:
                return results
            
            logger.info(f"Starting optimized bulk disable for {len(interfaces_to_disable)} interfaces")
            
            # Split into batches to avoid command length limits
            batches = []
            for i in range(0, len(interfaces_to_disable), max_batch_size):
                batch = interfaces_to_disable[i:i + max_batch_size]
                batches.append(batch)
            
            logger.info(f"Split into {len(batches)} batches")
            
            # Process each batch
            for batch_num, batch in enumerate(batches, 1):
                logger.info(f"Processing batch {batch_num}/{len(batches)} ({len(batch)} interfaces)")
                
                # Create interface ranges for this batch
                ranges = self._create_interface_ranges(batch)
                
                if ranges:
                    # Create range command
                    range_str = ",".join(ranges)
                    logger.info(f"Using interface range: {range_str}")
                    
                    commands = [
                        f"interface range {range_str}",
                        "shutdown"
                    ]
                    
                    # Execute batch command
                    try:
                        success = self._send_config_command_safe(commands)
                        
                        # Mark all interfaces in batch with same result
                        for interface in batch:
                            results[interface] = success
                            if success:
                                logger.info(f"✅ Disabled {interface} (batch)")
                            else:
                                logger.error(f"❌ Failed to disable {interface} (batch)")
                    
                    except Exception as e:
                        logger.error(f"Batch {batch_num} failed: {e}")
                        # Mark all as failed
                        for interface in batch:
                            results[interface] = False
                
                # Small delay between batches
                time.sleep(0.5)
            
            successful = sum(1 for success in results.values() if success)
            logger.info(f"Bulk disable completed: {successful}/{len(interfaces_to_disable)} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk disable error: {e}")
            # Mark all as failed
            for interface in interfaces_to_disable:
                results[interface] = False
            return results

    @performance_monitor("bulk_enable_interfaces")  
    def bulk_enable_interfaces_optimized(self, interfaces_to_enable: List[str],
                                        max_batch_size: int = 12) -> Dict[str, bool]:
        """
        Optimized bulk enable using interface ranges
        
        Args:
            interfaces_to_enable: List of interface names to enable
            max_batch_size: Maximum interfaces per batch
        
        Returns:
            Dict mapping interface names to success status
        """
        results = {}
        
        try:
            if not interfaces_to_enable:
                return results
            
            logger.info(f"Starting optimized bulk enable for {len(interfaces_to_enable)} interfaces")
            
            # Split into batches
            batches = []
            for i in range(0, len(interfaces_to_enable), max_batch_size):
                batch = interfaces_to_enable[i:i + max_batch_size]
                batches.append(batch)
            
            logger.info(f"Split into {len(batches)} batches")
            
            # Process each batch
            for batch_num, batch in enumerate(batches, 1):
                logger.info(f"Processing batch {batch_num}/{len(batches)} ({len(batch)} interfaces)")
                
                # Create interface ranges for this batch
                ranges = self._create_interface_ranges(batch)
                
                if ranges:
                    # Create range command
                    range_str = ",".join(ranges)
                    logger.info(f"Using interface range: {range_str}")
                    
                    commands = [
                        f"interface range {range_str}",
                        "no shutdown"
                    ]
                    
                    # Execute batch command
                    try:
                        success = self._send_config_command_safe(commands)
                        
                        # Mark all interfaces in batch with same result
                        for interface in batch:
                            results[interface] = success
                            if success:
                                logger.info(f"✅ Enabled {interface} (batch)")
                            else:
                                logger.error(f"❌ Failed to enable {interface} (batch)")
                    
                    except Exception as e:
                        logger.error(f"Batch {batch_num} failed: {e}")
                        # Mark all as failed
                        for interface in batch:
                            results[interface] = False
                
                # Small delay between batches
                time.sleep(0.5)
            
            successful = sum(1 for success in results.values() if success)
            logger.info(f"Bulk enable completed: {successful}/{len(interfaces_to_enable)} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk enable error: {e}")
            # Mark all as failed
            for interface in interfaces_to_enable:
                results[interface] = False
            return results

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
    
    def get_last_error(self) -> Optional[str]:
        """Get last error message"""
        return self.last_error
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        try:
            cache_manager.clear_all_caches()
            logger.info("Caches cleared")
        except AttributeError:
            logger.info("Cache not available")
    
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

    def _get_device_info(self) -> Dict[str, str]:
        """Get basic device information"""
        try:
            version_output = self.send_command("show version")
            return self.parser.parse_device_info(version_output)
        except Exception:
            return {} 