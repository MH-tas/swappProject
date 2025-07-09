��#!/usr/bin/env python3
"""
Professional Cisco Device Management Module
Enterprise-grade Cisco switch management with comprehensive error handling and logging.
"""

import re
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cisco_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CiscoManagerError(Exception):
    """Custom exception for Cisco Manager operations"""
    pass

class CiscoManager:
    """Professional Cisco device management class"""
    
    def __init__(self):
        """Initialize the Cisco Manager"""
        self.connection = None
        self.connected = False
        self.device_info = {}
        self.callbacks = {}
        self.last_error = None
        self.connection_lock = threading.Lock()
        logger.info("CiscoManager initialized")
    
    def register_callback(self, event: str, callback):
        """Register callback for events"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        logger.debug(f"Callback registered for event: {event}")
    
    def trigger_callback(self, event: str, data: Any = None):
        """Trigger registered callbacks"""
        try:
            if event in self.callbacks:
                for callback in self.callbacks[event]:
                    if callable(callback):
                        callback(data)
        except Exception as e:
            logger.error(f"Error triggering callback for {event}: {e}")
    
    def connect(self, host: str, username: str, password: str, 
                device_type: str = 'cisco_ios', port: int = 22, 
                secret: Optional[str] = None) -> bool:
        """Establish connection to Cisco device"""
        with self.connection_lock:
            try:
                logger.info(f"Attempting to connect to {host}:{port}")
                
                device_config = {
                    'device_type': device_type,
                    'host': host,
                    'username': username,
                    'password': password,
                    'port': port,
                    'timeout': 60,
                    'session_timeout': 60,
                    'global_delay_factor': 2,
                    'conn_timeout': 30
                }
                
                if secret:
                    device_config['secret'] = secret
                
                self.connection = ConnectHandler(**device_config)
                
                # Test connection
                test_output = self.connection.send_command('show version', delay_factor=2)
                if not test_output or 'Invalid' in test_output:
                    raise CiscoManagerError("Connection test failed")
                
                if secret:
                    self.connection.enable()
                    logger.info("Entered enable mode")
                
                self.connected = True
                self.last_error = None
                self.device_info = self._get_basic_device_info()
                
                logger.info(f"Successfully connected to {host}")
                self.trigger_callback('connected', self.device_info)
                return True
                
            except Exception as e:
                error_msg = f"Connection failed: {str(e)}"
                logger.error(error_msg)
                self.last_error = error_msg
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
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return {}
    
    def send_command(self, command: str, expect_string: Optional[str] = None, 
                    delay_factor: int = 1) -> str:
        """Send command to device with error handling"""
        if not self.connected or not self.connection:
            raise CiscoManagerError("Device not connected")
        
        try:
            logger.debug(f"Sending command: {command}")
            output = self.connection.send_command(
                command, 
                expect_string=expect_string,
                delay_factor=delay_factor,
                max_loops=500
            )
            return output
            
        except Exception as e:
            error_msg = f"Command '{command}' failed: {str(e)}"
            logger.error(error_msg)
            raise CiscoManagerError(error_msg)
    
    def send_config_commands(self, commands: List[str]) -> str:
        """Send configuration commands"""
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
    
    def get_interfaces_status(self) -> Dict[str, Dict[str, str]]:
        """Get comprehensive interface status information"""
        try:
            interfaces = {}
            
            # Primary method: show interfaces status
            try:
                status_output = self.send_command("show interfaces status")
                interfaces.update(self._parse_interface_status(status_output))
            except Exception:
                # Fallback method
                brief_output = self.send_command("show ip interface brief")
                interfaces.update(self._parse_interface_brief(brief_output))
            
            # Enrich with switchport information
            try:
                self._enrich_with_switchport_info(interfaces)
            except Exception:
                pass
            
            return interfaces
            
        except Exception as e:
            logger.error(f"Error getting interface status: {e}")
            return {}
    
    def _parse_interface_status(self, output: str) -> Dict[str, Dict[str, str]]:
        """Parse 'show interfaces status' output"""
        interfaces = {}
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('Port') or line.startswith('-'):
                continue
            
            parts = line.split()
            if len(parts) >= 4:
                interface = parts[0]
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
                    'description': ''
                }
        
        return interfaces
    
    def _parse_interface_brief(self, output: str) -> Dict[str, Dict[str, str]]:
        """Parse 'show ip interface brief' output"""
        interfaces = {}
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or 'Interface' in line or line.startswith('-'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                interface = parts[0]
                status = 'up' if 'up' in line.lower() else 'down'
                
                interfaces[interface] = {
                    'status': status,
                    'vlan': 'unknown',
                    'duplex': 'unknown',
                    'speed': 'unknown',
                    'type': 'unknown',
                    'description': ''
                }
        
        return interfaces
    
    def _enrich_with_switchport_info(self, interfaces: Dict[str, Dict[str, str]]):
        """Enrich interface information with switchport details"""
        try:
            switchport_output = self.send_command("show interfaces switchport")
            current_interface = None
            
            for line in switchport_output.split('\n'):
                line = line.strip()
                
                if line.startswith('Name:'):
                    current_interface = line.split('Name:')[1].strip()
                elif 'Access Mode VLAN:' in line and current_interface:
                    vlan_match = re.search(r'Access Mode VLAN:\s*(\d+)', line)
                    if vlan_match and current_interface in interfaces:
                        interfaces[current_interface]['vlan'] = vlan_match.group(1)
        
        except Exception:
            pass
    
    def get_cpu_memory_usage(self) -> Dict[str, Any]:
        """Get CPU and memory usage"""
        try:
            cpu_info = {
                'cpu_usage': 'N/A',
                'memory_usage': 'N/A',
                'total_memory': 0,
                'used_memory': 0
            }
            
            # Get CPU usage
            try:
                cpu_output = self.send_command("show processes cpu sorted")
                for line in cpu_output.split('\n'):
                    if 'CPU utilization' in line:
                        patterns = [r'five seconds:\s*(\d+)%', r'(\d+)%']
                        for pattern in patterns:
                            match = re.search(pattern, line)
                            if match:
                                cpu_info['cpu_usage'] = f"{match.group(1)}%"
                                break
                        if cpu_info['cpu_usage'] != 'N/A':
                            break
            except Exception:
                pass
            
            # Get memory usage
            try:
                memory_output = self.send_command("show memory statistics")
                for line in memory_output.split('\n'):
                    if 'Processor Pool' in line or 'Head' in line:
                        total_match = re.search(r'Total:\s*(\d+)', line)
                        used_match = re.search(r'Used:\s*(\d+)', line)
                        
                        if total_match and used_match:
                            total_mem = int(total_match.group(1))
                            used_mem = int(used_match.group(1))
                            cpu_info['total_memory'] = total_mem
                            cpu_info['used_memory'] = used_mem
                            
                            if total_mem > 0:
                                usage_pct = (used_mem / total_mem) * 100
                                cpu_info['memory_usage'] = f"{usage_pct:.1f}%"
                            break
            except Exception:
                pass
            
            return cpu_info
            
        except Exception:
            return {
                'cpu_usage': 'N/A',
                'memory_usage': 'N/A',
                'total_memory': 0,
                'used_memory': 0
            }
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive device status"""
        status_data = {
            'device_info': self.get_device_info(),
            'interfaces': {},
            'vlans': {},
            'interface_vlans': {},
            'temperature': {},
            'power': {},
            'fans': {},
            'cpu_memory': {}
        }
        
        try:
            status_data['interfaces'] = self.get_interfaces_status()
        except Exception:
            pass
        
        try:
            vlans, interface_vlans = self.get_detailed_vlan_info()
            status_data['vlans'] = vlans
            status_data['interface_vlans'] = interface_vlans
        except Exception:
            pass
        
        try:
            status_data['cpu_memory'] = self.get_cpu_memory_usage()
        except Exception:
            pass
        
        return status_data
    
    def get_detailed_vlan_info(self) -> Tuple[Dict[str, Dict], Dict[str, str]]:
        """Get detailed VLAN information"""
        try:
            vlan_output = self.send_command("show vlan brief")
            vlans = {}
            
            lines = vlan_output.split('\n')
            for line in lines:
                if re.match(r'^\d+', line):
                    parts = line.split()
                    if len(parts) >= 3:
                        vlan_id = parts[0]
                        vlan_name = parts[1]
                        status = parts[2]
                        
                        vlans[vlan_id] = {
                            'name': vlan_name,
                            'status': status,
                            'ports': []
                        }
            
            return vlans, {}
            
        except Exception:
            return {}, {}
    
    def set_interface_status(self, interface: str, status: str) -> str:
        """Set interface administrative status"""
        try:
            commands = [
                f"interface {interface}",
                "shutdown" if status.lower() == "down" else "no shutdown",
                "exit"
            ]
            result = self.send_config_commands(commands)
            logger.info(f"Interface {interface} set to {status}")
            return result
        except Exception as e:
            raise CiscoManagerError(f"Failed to set interface status: {str(e)}")
    
    def set_interface_vlan(self, interface: str, vlan_id: str) -> str:
        """Set interface VLAN"""
        try:
            commands = [
                f"interface {interface}",
                f"switchport access vlan {vlan_id}",
                "exit"
            ]
            result = self.send_config_commands(commands)
            logger.info(f"Interface {interface} VLAN set to {vlan_id}")
            return result
        except Exception as e:
            raise CiscoManagerError(f"Failed to set interface VLAN: {str(e)}")
    
    def set_interface_description(self, interface: str, description: str) -> str:
        """Set interface description"""
        try:
            commands = [
                f"interface {interface}",
                f"description {description}",
                "exit"
            ]
            result = self.send_config_commands(commands)
            logger.info(f"Interface {interface} description set")
            return result
        except Exception as e:
            raise CiscoManagerError(f"Failed to set interface description: {str(e)}")
    
    def create_vlan(self, vlan_id: str, vlan_name: str) -> str:
        """Create a new VLAN"""
        try:
            commands = [
                f"vlan {vlan_id}",
                f"name {vlan_name}",
                "exit"
            ]
            result = self.send_config_commands(commands)
            logger.info(f"VLAN {vlan_id} ({vlan_name}) created")
            return result
        except Exception as e:
            raise CiscoManagerError(f"Failed to create VLAN: {str(e)}")
    
    def delete_vlan(self, vlan_id: str) -> str:
        """Delete a VLAN"""
        try:
            commands = [f"no vlan {vlan_id}"]
            result = self.send_config_commands(commands)
            logger.info(f"VLAN {vlan_id} deleted")
            return result
        except Exception as e:
            raise CiscoManagerError(f"Failed to delete VLAN: {str(e)}")
    
    def ping(self, target: str, count: int = 5) -> str:
        """Ping from device"""
        try:
            command = f"ping {target}"
            if count != 5:
                command += f" repeat {count}"
            return self.send_command(command, delay_factor=2)
        except Exception as e:
            raise CiscoManagerError(f"Ping failed: {str(e)}")
    
    def traceroute(self, target: str) -> str:
        """Traceroute from device"""
        try:
            return self.send_command(f"traceroute {target}", delay_factor=3)
        except Exception as e:
            raise CiscoManagerError(f"Traceroute failed: {str(e)}")
    
    def get_mac_address_table(self) -> List[Dict[str, str]]:
        """Get MAC address table"""
        try:
            output = self.send_command("show mac address-table")
            mac_table = []
            
            for line in output.split('\n'):
                line = line.strip()
                if re.match(r'^\d+', line):
                    parts = line.split()
                    if len(parts) >= 4:
                        mac_table.append({
                            'vlan': parts[0],
                            'mac_address': parts[1],
                            'type': parts[2],
                            'interface': parts[3]
                        })
            
            return mac_table
        except Exception:
            return []
    
    def get_arp_table(self) -> List[Dict[str, str]]:
        """Get ARP table"""
        try:
            output = self.send_command("show arp")
            arp_table = []
            
            for line in output.split('\n'):
                line = line.strip()
                if re.match(r'Internet', line):
                    parts = line.split()
                    if len(parts) >= 6:
                        arp_table.append({
                            'address': parts[1],
                            'age': parts[2],
                            'mac_address': parts[3],
                            'type': parts[4],
                            'interface': parts[5]
                        })
            
            return arp_table
        except Exception:
            return []
    
    def get_running_config(self) -> str:
        """Get running configuration"""
        try:
            return self.send_command("show running-config")
        except Exception as e:
            raise CiscoManagerError(f"Failed to get running config: {str(e)}")
    
    def save_config(self) -> str:
        """Save running configuration to startup"""
        try:
            output = self.send_command("write memory", delay_factor=3)
            logger.info("Configuration saved")
            return output
        except Exception as e:
            raise CiscoManagerError(f"Failed to save config: {str(e)}")
    
    def backup_config(self, filename: Optional[str] = None) -> str:
        """Backup device configuration"""
        try:
            config = self.send_command("show running-config")
            
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                serial = self.device_info.get('serial', 'unknown')
                filename = f"backup_{serial}_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(config)
            
            logger.info(f"Configuration backed up to {filename}")
            return filename
        except Exception as e:
            raise CiscoManagerError(f"Backup failed: {str(e)}")
    
    def get_interface_statistics(self) -> List[Dict[str, Any]]:
        """Get detailed interface statistics"""
        try:
            output = self.send_command("show interfaces")
            interfaces = []
            current_interface = None
            
            for line in output.split('\n'):
                line = line.strip()
                
                if line.startswith(('GigabitEthernet', 'FastEthernet', 'TenGigabitEthernet')):
                    if current_interface:
                        interfaces.append(current_interface)
                    
                    parts = line.split()
                    interface_name = parts[0]
                    status = 'up' if 'up' in line.lower() else 'down'
                    
                    current_interface = {
                        'interface': interface_name,
                        'status': status,
                        'rx_packets': 0,
                        'tx_packets': 0,
                        'rx_bytes': 0,
                        'tx_bytes': 0,
                        'errors': 0
                    }
                
                elif current_interface:
                    if 'packets input' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                current_interface['rx_packets'] = int(parts[0])
                                current_interface['rx_bytes'] = int(parts[3])
                            except ValueError:
                                pass
                    
                    elif 'packets output' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                current_interface['tx_packets'] = int(parts[0])
                                current_interface['tx_bytes'] = int(parts[3])
                            except ValueError:
                                pass
            
            if current_interface:
                interfaces.append(current_interface)
            
            return interfaces
        except Exception:
            return []
