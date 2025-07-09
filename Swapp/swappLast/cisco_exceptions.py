"""
Cisco Manager Custom Exceptions
================================
Custom exception classes for Cisco switch management operations.
"""

class CiscoManagerError(Exception):
    """Base exception for Cisco Manager operations"""
    pass

class CiscoConnectionError(CiscoManagerError):
    """Raised when connection to Cisco device fails"""
    pass

class CiscoCommandError(CiscoManagerError):
    """Raised when command execution fails"""
    pass

class CiscoParsingError(CiscoManagerError):
    """Raised when output parsing fails"""
    pass

class CiscoConfigError(CiscoManagerError):
    """Raised when configuration operations fail"""
    pass 