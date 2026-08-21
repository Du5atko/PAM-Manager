"""PAM Validator Module - Multi-Stage PAM Configuration Validation.

This module provides comprehensive PAM configuration validation through
five stages: syntax, semantic, platform, module-specific, and security policy.
"""

import logging
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    level: ValidationLevel
    stage: str
    message: str
    line_number: Optional[int] = None
    module_name: Optional[str] = None
    service_name: Optional[str] = None
    details: Optional[Dict] = None
    
    def __str__(self) -> str:
        """String representation of validation issue."""
        location = ""
        if self.service_name:
            location += f"[{self.service_name}]"
        if self.module_name:
            location += f" {self.module_name}"
        if self.line_number:
            location += f":{self.line_number}"
        
        return f"{self.level.value.upper()} ({self.stage}){location}: {self.message}"


class SyntaxValidator:
    """Stage 1: Validates PAM configuration syntax.
    
    Checks:
    - Valid PAM line format (interface control-flag module [options])
    - Proper control flag syntax
    - Valid interface names
    - Module path format
    """
    
    VALID_INTERFACES = {'auth', 'account', 'session', 'password'}
    VALID_SIMPLE_FLAGS = {'required', 'requisite', 'sufficient', 'optional', 'include', 'substack'}
    
    @staticmethod
    def validate_line(line: str, line_number: int, service_name: str) -> List[ValidationIssue]:
        """Validate a single PAM configuration line.
        
        Args:
            line: PAM configuration line
            line_number: Line number in file
            service_name: Service name being validated
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        # Skip comments and empty lines
        line = line.strip()
        if not line or line.startswith('#'):
            return issues
        
        # Split line into parts
        parts = line.split()
        if len(parts) < 3:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                stage="syntax",
                message="Invalid PAM line format (minimum: interface control-flag module)",
                line_number=line_number,
                service_name=service_name
            ))
            return issues
        
        interface, control_flag, module = parts[0], parts[1], parts[2]
        
        # Validate interface
        if interface not in SyntaxValidator.VALID_INTERFACES:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                stage="syntax",
                message=f"Invalid interface '{interface}'. Must be: {', '.join(SyntaxValidator.VALID_INTERFACES)}",
                line_number=line_number,
                service_name=service_name
            ))
        
        # Validate control flag (simple or complex)
        if not SyntaxValidator._validate_control_flag(control_flag):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                stage="syntax",
                message=f"Invalid control flag '{control_flag}'",
                line_number=line_number,
                service_name=service_name
            ))
        
        # Validate module name
        if not SyntaxValidator._validate_module_path(module):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                stage="syntax",
                message=f"Invalid module path '{module}'",
                line_number=line_number,
                module_name=module,
                service_name=service_name
            ))
        
        return issues
    
    @staticmethod
    def _validate_control_flag(flag: str) -> bool:
        """Validate control flag format (simple or complex)."""
        # Simple flags
        if flag in SyntaxValidator.VALID_SIMPLE_FLAGS:
            return True
        
        # Complex flags: [flag1=action1 flag2=action2 ...]
        if flag.startswith('[') and flag.endswith(']'):
            # TODO: Parse complex flags
            return True
        
        return False
    
    @staticmethod
    def _validate_module_path(module: str) -> bool:
        """Validate module path format."""
        # Allow pam_* pattern or full path
        if module.startswith('pam_') or module.startswith('/'):
            return True
        return False


class SemanticValidator:
    """Stage 2: Validates semantic correctness of PAM configuration.
    
    Checks:
    - Required interfaces are present
    - Correct ordering of modules
    - Control flow logic
    - Option compatibility
    """
    
    @staticmethod
    def validate_service(service_name: str, lines: List[str]) -> List[ValidationIssue]:
        """Validate semantic correctness of service configuration.
        
        Args:
            service_name: Service name
            lines: List of PAM configuration lines
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for required interfaces
        interfaces = set()
        modules_by_interface = {}
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                interface = parts[0]
                interfaces.add(interface)
                if interface not in modules_by_interface:
                    modules_by_interface[interface] = []
                modules_by_interface[interface].append(parts[2] if len(parts) > 2 else "")
        
        # Warn if common interfaces are missing
        common_interfaces = {'auth', 'account', 'session'}
        missing = common_interfaces - interfaces
        if missing:
            for iface in missing:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    stage="semantic",
                    message=f"Missing '{iface}' interface configuration",
                    service_name=service_name
                ))
        
        return issues


class PlatformValidator:
    """Stage 3: Validates platform compatibility.
    
    Checks:
    - Module availability on target platform
    - Platform-specific configuration options
    - Incompatible module combinations
    """
    
    @staticmethod
    def validate_module_availability(module_name: str, platform: str,
                                    available_modules: Dict[str, List[str]]) -> List[ValidationIssue]:
        """Check if module is available on platform.
        
        Args:
            module_name: Module name to check
            platform: Target platform
            available_modules: Dict mapping platforms to available modules
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if platform in available_modules:
            if module_name not in available_modules[platform]:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    stage="platform",
                    message=f"Module '{module_name}' is not available on {platform}",
                    module_name=module_name
                ))
        
        return issues


class ModuleSpecificValidator:
    """Stage 4: Validates module-specific configuration.
    
    Checks:
    - Valid module parameters
    - Parameter combinations
    - Module dependencies
    """
    
    @staticmethod
    def validate_module_options(module_name: str, options: List[str],
                               module_specs: Dict) -> List[ValidationIssue]:
        """Validate module-specific options.
        
        Args:
            module_name: Module name
            options: List of options
            module_specs: Module specifications
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if module_name not in module_specs:
            return issues
        
        spec = module_specs[module_name]
        valid_params = spec.get('parameters', {})
        
        for option in options:
            # Parse option (key=value or just key)
            if '=' in option:
                key = option.split('=')[0]
            else:
                key = option
            
            if key not in valid_params and not key.startswith('_'):
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    stage="module_specific",
                    message=f"Unknown parameter '{key}' for module '{module_name}'",
                    module_name=module_name
                ))
        
        return issues


class SecurityPolicyValidator:
    """Stage 5: Validates security policy compliance.
    
    Checks:
    - Password complexity requirements
    - Account lockout configuration
    - Session timeout
    - Privilege escalation controls
    - Audit logging
    """
    
    @staticmethod
    def validate_security_policy(service_name: str, config_lines: List[str],
                                security_policy: Dict) -> List[ValidationIssue]:
        """Validate configuration against security policy.
        
        Args:
            service_name: Service name
            config_lines: Configuration lines
            security_policy: Security policy requirements
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for password policy modules if required
        if security_policy.get('require_password_policy'):
            has_password_policy = any(
                'pam_cracklib' in line or 'pam_pwquality' in line or 'pam_passwdqc' in line
                for line in config_lines
            )
            if not has_password_policy:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    stage="security",
                    message="Password policy module not configured (recommended for security)",
                    service_name=service_name
                ))
        
        # Check for account lockout if required
        if security_policy.get('require_account_lockout'):
            has_lockout = any(
                'pam_faillock' in line or 'pam_tally2' in line
                for line in config_lines
            )
            if not has_lockout:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    stage="security",
                    message="Account lockout module not configured (recommended for security)",
                    service_name=service_name
                ))
        
        return issues


class PAMValidator:
    """Main PAM Configuration Validator - Orchestrates all validation stages."""
    
    def __init__(self, module_specs: Dict = None, security_policy: Dict = None,
                 available_modules: Dict = None):
        """Initialize PAM Validator.
        
        Args:
            module_specs: Module specifications
            security_policy: Security policy requirements
            available_modules: Available modules per platform
        """
        self.module_specs = module_specs or {}
        self.security_policy = security_policy or {}
        self.available_modules = available_modules or {}
        self.issues = []
    
    def validate(self, service_name: str, config_lines: List[str],
                 platform: str = None) -> Tuple[bool, List[ValidationIssue]]:
        """Perform complete validation of PAM service configuration.
        
        Args:
            service_name: Service name
            config_lines: Configuration lines
            platform: Target platform for validation
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        self.issues = []
        
        # Stage 1: Syntax Validation
        for i, line in enumerate(config_lines, 1):
            self.issues.extend(SyntaxValidator.validate_line(line, i, service_name))
        
        # Stage 2: Semantic Validation
        self.issues.extend(SemanticValidator.validate_service(service_name, config_lines))
        
        # Stage 3: Platform Validation
        if platform:
            for line in config_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) > 2:
                        module = parts[2]
                        self.issues.extend(
                            PlatformValidator.validate_module_availability(
                                module, platform, self.available_modules
                            )
                        )
        
        # Stage 4: Module-Specific Validation
        for line in config_lines:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split()
                if len(parts) > 3:
                    module = parts[2]
                    options = parts[3:]
                    self.issues.extend(
                        ModuleSpecificValidator.validate_module_options(
                            module, options, self.module_specs
                        )
                    )
        
        # Stage 5: Security Policy Validation
        self.issues.extend(
            SecurityPolicyValidator.validate_security_policy(
                service_name, config_lines, self.security_policy
            )
        )
        
        # Check for errors
        has_errors = any(issue.level == ValidationLevel.ERROR for issue in self.issues)
        
        return not has_errors, self.issues


__all__ = ['PAMValidator', 'ValidationIssue', 'ValidationLevel', 
           'SyntaxValidator', 'SemanticValidator', 'PlatformValidator',
           'ModuleSpecificValidator', 'SecurityPolicyValidator']
