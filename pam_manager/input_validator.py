"""Unified Input Validator Module for PAM Manager.

Combines validation methods from multiple validator classes into a single,
comprehensive input validation module.
"""

import re
from typing import Tuple


class InputValidator:
    """Validates GUI and configuration inputs to prevent injection attacks.
    
    This class provides unified input validation for:
    - Service names (PAM service names from /etc/pam.d/)
    - Module names (PAM module names)
    - Parameter keys and values
    - PAM control flags
    - PAM interfaces (auth, account, session, password)
    - Configuration options
    - Filenames and paths
    """
    
    # Validation configuration
    MAX_SERVICE_NAME_LEN = 255
    MAX_MODULE_NAME_LEN = 255
    MAX_PARAM_NAME_LEN = 100
    MAX_PARAM_VALUE_LEN = 1000
    MAX_FILENAME_LEN = 100
    
    VALID_INTERFACES = {'auth', 'account', 'session', 'password'}
    VALID_CONTROL_FLAGS = {'required', 'requisite', 'sufficient', 'optional', 'include', 'substack'}
    RESERVED_NAMES = {'system', 'root', 'admin', 'system-auth', 'system-account', 'debug', 'trace'}
    DANGEROUS_CHARS = {'$', '(', ')', '`', ';', '|', '&', '<', '>', "'", '"', '\\'}
    
    # ========================================================================
    # Service Name Validation
    # ========================================================================
    
    @staticmethod
    def validate_service_name(name: str) -> Tuple[bool, str]:
        """Validate PAM service name.
        
        Service names are used in /etc/pam.d/ filenames and must follow
        strict naming conventions to avoid security issues.
        
        Args:
            name: Service name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return False, "Service name cannot be empty"
        
        if len(name) > InputValidator.MAX_SERVICE_NAME_LEN:
            return False, f"Service name too long (max {InputValidator.MAX_SERVICE_NAME_LEN} characters)"
        
        if len(name) < 1:
            return False, "Service name too short (min 1 character)"
        
        # Allow alphanumeric, dash, underscore only
        if not all(c.isalnum() or c in '-_' for c in name):
            return False, "Service name can only contain alphanumeric, dash, and underscore"
        
        # Cannot start with digit
        if name[0].isdigit():
            return False, "Service name cannot start with a digit"
        
        # Check reserved names
        if name.lower() in InputValidator.RESERVED_NAMES:
            return False, f"Service name '{name}' is reserved"
        
        return True, ""
    
    # ========================================================================
    # Module Name Validation
    # ========================================================================
    
    @staticmethod
    def validate_module_name(name: str, max_length: int = None) -> Tuple[bool, str]:
        """Validate PAM module name.
        
        Args:
            name: Module name to validate
            max_length: Maximum allowed length (uses default if None)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if max_length is None:
            max_length = InputValidator.MAX_MODULE_NAME_LEN
            
        if not name or len(name) == 0:
            return False, "Module name cannot be empty"
        
        if len(name) > max_length:
            return False, f"Module name exceeds {max_length} characters"
        
        # Prevent path traversal
        if '..' in name or '/' in name or '\\' in name:
            return False, "Module name cannot contain path separators (.., /, \\)"
        
        # Allow alphanumeric, underscore, hyphen only
        if not re.match(r'^[a-zA-Z0-9_\-]+$', name):
            return False, "Module name contains invalid characters (only alphanumeric, underscore, hyphen allowed)"
        
        # Module names typically start with pam_
        if not name.startswith('pam_') and not name.startswith('pam-'):
            return False, "Module name should start with 'pam_' or 'pam-'"
        
        return True, ""
    
    # ========================================================================
    # Parameter Validation
    # ========================================================================
    
    @staticmethod
    def validate_param_name(name: str, max_length: int = None) -> Tuple[bool, str]:
        """Validate parameter name for GUI input.
        
        Args:
            name: Parameter name to validate
            max_length: Maximum allowed length (uses default if None)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if max_length is None:
            max_length = InputValidator.MAX_PARAM_NAME_LEN
            
        if not name or len(name) == 0:
            return False, "Parameter name cannot be empty"
        
        if len(name) > max_length:
            return False, f"Parameter name exceeds {max_length} characters"
        
        # Allow alphanumeric, underscore, hyphen, equals (for key=value)
        if not re.match(r'^[a-zA-Z0-9_\-=]+$', name):
            return False, "Parameter contains invalid characters (only alphanumeric, underscore, hyphen allowed)"
        
        return True, ""
    
    @staticmethod
    def validate_parameter_key(key: str) -> Tuple[bool, str]:
        """Validate parameter key name.
        
        Args:
            key: Parameter key to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not key:
            return False, "Parameter key cannot be empty"
        
        if not all(c.isalnum() or c == '_' for c in key):
            return False, "Parameter key can only contain alphanumeric and underscore"
        
        if key.lower() in InputValidator.RESERVED_NAMES:
            return False, f"Parameter key '{key}' is reserved"
        
        return True, ""
    
    @staticmethod
    def validate_parameter_value(value: str, max_length: int = None) -> Tuple[bool, str]:
        """Validate parameter value for security.
        
        Args:
            value: Parameter value to validate
            max_length: Maximum allowed length (uses default if None)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if max_length is None:
            max_length = InputValidator.MAX_PARAM_VALUE_LEN
            
        if len(value) > max_length:
            return False, f"Parameter value too long (max {max_length} characters)"
        
        # Check for shell injection attempts
        if any(char in value for char in InputValidator.DANGEROUS_CHARS):
            return False, "Parameter value contains potentially dangerous characters"
        
        return True, ""
    
    # ========================================================================
    # Control Flag and Interface Validation
    # ========================================================================
    
    @staticmethod
    def validate_control_flag(flag: str) -> Tuple[bool, str]:
        """Validate PAM control flag.
        
        Args:
            flag: Control flag to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if flag not in InputValidator.VALID_CONTROL_FLAGS:
            return False, f"Invalid control flag '{flag}'. Must be one of: {', '.join(sorted(InputValidator.VALID_CONTROL_FLAGS))}"
        return True, ""
    
    @staticmethod
    def validate_interface(interface: str) -> Tuple[bool, str]:
        """Validate PAM interface.
        
        Args:
            interface: Interface to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if interface not in InputValidator.VALID_INTERFACES:
            return False, f"Invalid interface '{interface}'. Must be one of: {', '.join(sorted(InputValidator.VALID_INTERFACES))}"
        return True, ""
    
    # ========================================================================
    # Configuration Option Validation
    # ========================================================================
    
    @staticmethod
    def validate_config_option_value(option: str, value: str) -> Tuple[bool, str]:
        """Validate configuration option value based on option type.
        
        Args:
            option: Configuration option name
            value: Configuration option value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not option or not value:
            return False, "Configuration option and value cannot be empty"
        
        # Check for injection attacks
        if any(char in value for char in InputValidator.DANGEROUS_CHARS):
            return False, "Configuration value contains dangerous characters"
        
        # Validate by option type
        if option.endswith("_port"):
            try:
                port = int(value)
                if not (1 <= port <= 65535):
                    return False, "Port must be between 1 and 65535"
            except ValueError:
                return False, "Port must be a valid integer"
        
        elif option.endswith("_timeout"):
            try:
                timeout = int(value)
                if timeout < 0:
                    return False, "Timeout must be non-negative"
            except ValueError:
                return False, "Timeout must be a valid integer"
        
        elif option.endswith("_path"):
            # Path validation - no shell injection
            if any(char in value for char in {'`', '$', '(', ')'}):
                return False, "Path contains dangerous characters"
        
        return True, ""
    
    # ========================================================================
    # Filename and Path Sanitization
    # ========================================================================
    
    @staticmethod
    def sanitize_filename(name: str, max_length: int = None) -> str:
        """Sanitize filename by removing dangerous characters.
        
        Args:
            name: Filename to sanitize
            max_length: Maximum allowed length (uses default if None)
            
        Returns:
            Sanitized filename
        """
        if max_length is None:
            max_length = InputValidator.MAX_FILENAME_LEN
            
        # Remove forbidden characters
        forbidden = {'/', '\\', '?', '*', '!', ':', '"', '<', '>', '|', ';'}
        result = ''.join(c if c not in forbidden else '_' for c in name)
        
        # Replace spaces with underscores
        result = result.replace(' ', '_')
        
        # Truncate to reasonable length
        result = result[:max_length]
        
        return result
    
    # ========================================================================
    # Batch Validation Methods
    # ========================================================================
    
    @staticmethod
    def validate_all_params(params: dict) -> Tuple[bool, str]:
        """Validate all parameters at once.
        
        Args:
            params: Dictionary of parameters to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        for key, value in params.items():
            # Validate key
            is_valid, msg = InputValidator.validate_parameter_key(key)
            if not is_valid:
                return False, f"Parameter key '{key}': {msg}"
            
            # Validate value
            is_valid, msg = InputValidator.validate_parameter_value(str(value))
            if not is_valid:
                return False, f"Parameter value '{value}': {msg}"
        
        return True, ""


__all__ = ['InputValidator']
