"""
Cisco Output Parsers
====================
Functions to parse various Cisco command outputs into structured data.
"""

import re
import logging
from typing import Dict, List

logger = logging.getLogger('cisco_manager')

class CiscoParser:
    """Main parser class for Cisco command outputs"""
    
    @staticmethod
    def parse_interface_status_enhanced(output: str) -> Dict[str, Dict[str, str]]:
        """Enhanced parsing of 'show interfaces status' output"""
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

    @staticmethod
    def parse_interface_status_fast(output: str) -> Dict[str, Dict[str, str]]:
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

    @staticmethod
    def parse_interface_brief(output: str) -> Dict[str, Dict[str, str]]:
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

    @staticmethod
    def parse_basic_interfaces(output: str) -> Dict[str, Dict[str, str]]:
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

    @staticmethod
    def parse_mac_table(output: str) -> List[Dict[str, str]]:
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

    @staticmethod
    def parse_arp_table(output: str) -> List[Dict[str, str]]:
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

    @staticmethod
    def parse_device_info(output: str) -> Dict[str, str]:
        """Parse device information from show version"""
        info = {}
        
        # Parse hostname
        hostname_match = re.search(r'(\S+) uptime is', output)
        if hostname_match:
            info['hostname'] = hostname_match.group(1)
        
        # Parse model
        model_patterns = [
            r'Model number\s*:\s*(.+)',
            r'cisco\s+(\S+)\s+\(',
            r'Hardware:\s*(\S+)'
        ]
        for pattern in model_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                info['model'] = match.group(1).strip()
                break
        
        # Parse serial number
        serial_patterns = [
            r'System serial number\s*:\s*(\S+)',
            r'Processor board ID\s+(\S+)'
        ]
        for pattern in serial_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                info['serial'] = match.group(1).strip()
                break
        
        # Parse IOS version
        ios_match = re.search(r'Version\s+(\S+)', output)
        if ios_match:
            info['ios_version'] = ios_match.group(1)
        
        # Parse uptime
        uptime_match = re.search(r'uptime is\s+(.+)', output)
        if uptime_match:
            info['uptime'] = uptime_match.group(1).strip()
        
        return info 