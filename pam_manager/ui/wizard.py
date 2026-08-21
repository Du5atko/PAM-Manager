"""Configuration Wizard for interactive PAM setup - Phase 4."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import logging

from pam_manager.platform.metadata import Platform, PlatformMetadata
from pam_manager.platform.config_generator import PlatformConfigGenerator


logger = logging.getLogger(__name__)


@dataclass
class WizardState:
    """Wizard configuration state."""
    current_step: int = 0
    platform: Optional[Platform] = None
    services: List[str] = None
    hardened_mode: bool = False
    modules: List[str] = None
    backup_enabled: bool = True
    auto_restart: bool = False
    notes: str = ""
    
    def __post_init__(self):
        if self.services is None:
            self.services = []
        if self.modules is None:
            self.modules = []


class ConfigurationWizard:
    """Interactive PAM configuration wizard."""
    
    STEPS = [
        "platform_selection",
        "service_selection",
        "module_selection",
        "security_level",
        "backup_verification",
        "review_and_apply",
    ]
    
    SERVICES = {
        "sshd": "SSH Daemon - Secure Shell",
        "login": "Login Service",
        "sudo": "Sudo",
        "su": "Su",
    }
    
    SECURITY_PRESETS = {
        "basic": "Basic authentication (pam_unix only)",
        "moderate": "Moderate security (faillock + password quality)",
        "hardened": "Hardened security (comprehensive protection)",
        "paranoid": "Paranoid mode (maximum security)",
    }
    
    def __init__(self):
        """Initialize wizard."""
        self.state = WizardState()
        self.steps_completed = 0
    
    def get_platform_selection(self) -> Dict[str, str]:
        """
        Get platform selection options.
        
        Returns:
            Dict[str, str]: Platform name -> description mapping
        """
        platforms = {}
        for platform in Platform:
            category = (
                "Linux" if PlatformMetadata.is_linux(platform) else
                "BSD" if PlatformMetadata.is_bsd(platform) else
                "macOS"
            )
            pm = PlatformMetadata.get_package_manager(platform)
            platforms[platform.value] = f"{category} ({pm})"
        
        return platforms
    
    def set_platform(self, platform_value: str) -> Tuple[bool, str]:
        """
        Set wizard platform.
        
        Args:
            platform_value: Platform enum value
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.state.platform = Platform[platform_value.upper()]
            logger.info(f"Platform set to {self.state.platform.value}")
            return (True, f"Platform set to {self.state.platform.value}")
        except KeyError:
            return (False, f"Invalid platform: {platform_value}")
    
    def get_service_selection(self) -> Dict[str, str]:
        """
        Get available services based on platform.
        
        Returns:
            Dict[str, str]: Service name -> description
        """
        services = {}
        
        for service, description in self.SERVICES.items():
            # Filter services for platform
            if service in ["sudo", "su"] and self.state.platform and PlatformMetadata.is_bsd(self.state.platform):
                continue  # BSD might not have these
            
            services[service] = description
        
        return services
    
    def set_services(self, service_list: List[str]) -> Tuple[bool, str]:
        """
        Set wizard services.
        
        Args:
            service_list: List of service names
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        valid_services = set(self.get_service_selection().keys())
        invalid = [s for s in service_list if s not in valid_services]
        
        if invalid:
            return (False, f"Invalid services: {invalid}")
        
        self.state.services = service_list
        logger.info(f"Services set to: {service_list}")
        return (True, f"Services: {', '.join(service_list)}")
    
    def get_module_selection(self) -> Dict[str, List[str]]:
        """
        Get available modules by category.
        
        Returns:
            Dict[str, List[str]]: Category -> modules
        """
        if not self.state.platform:
            return {}
        
        modules_by_category = {
            "authentication": ["pam_unix"],
            "account_lockout": [],
            "password_quality": [],
            "logging": ["pam_lastlog"],
            "session": ["pam_env"],
        }
        
        # Get modules by category
        for category, variants in [
            ("account_lockout", ["account_lockout"]),
            ("password_quality", ["password_quality"]),
        ]:
            for variant_type in variants:
                variants_list = PlatformMetadata.get_module_variants(variant_type, self.state.platform)
                if variants_list:
                    modules_by_category[category] = variants_list
        
        return modules_by_category
    
    def set_modules(self, module_list: List[str]) -> Tuple[bool, str]:
        """
        Set wizard modules.
        
        Args:
            module_list: List of module names
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        self.state.modules = module_list
        logger.info(f"Modules set to: {module_list}")
        return (True, f"Modules: {', '.join(module_list)}")
    
    def get_security_levels(self) -> Dict[str, str]:
        """
        Get available security presets.
        
        Returns:
            Dict[str, str]: Preset name -> description
        """
        return self.SECURITY_PRESETS
    
    def set_security_level(self, level: str) -> Tuple[bool, str]:
        """
        Set security level.
        
        Args:
            level: Security level (basic, moderate, hardened, paranoid)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if level not in self.SECURITY_PRESETS:
            return (False, f"Invalid security level: {level}")
        
        self.state.hardened_mode = level in ["hardened", "paranoid"]
        logger.info(f"Security level: {level}")
        return (True, f"Security level: {level}")
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get configuration summary for review.
        
        Returns:
            Dict[str, any]: Configuration summary
        """
        return {
            "platform": self.state.platform.value if self.state.platform else "Not selected",
            "services": self.state.services,
            "modules": self.state.modules,
            "hardened": self.state.hardened_mode,
            "backup_enabled": self.state.backup_enabled,
            "auto_restart": self.state.auto_restart,
            "notes": self.state.notes,
        }
    
    def generate_configuration(self) -> Tuple[bool, Dict[str, str], str]:
        """
        Generate final PAM configuration.
        
        Returns:
            Tuple[bool, Dict[str, str], str]: (success, config_dict, message)
        """
        if not self.state.platform:
            return (False, {}, "Platform not selected")
        
        if not self.state.services:
            return (False, {}, "No services selected")
        
        try:
            gen = PlatformConfigGenerator(self.state.platform)
            
            if self.state.hardened_mode:
                configs = gen.generate_security_hardened_config()
            else:
                configs = {}
                for service in self.state.services:
                    if service == "sshd":
                        if PlatformMetadata.is_linux(self.state.platform):
                            configs["sshd"] = gen.generate_linux_sshd_config()
                        else:
                            configs["sshd"] = gen.generate_bsd_sshd_config()
                    elif service == "login":
                        configs["login"] = gen.generate_login_config()
                    elif service == "sudo":
                        configs["sudo"] = gen.generate_sudo_config()
                    elif service == "su":
                        configs["su"] = gen.generate_su_config()
            
            message = f"Generated configuration for {len(configs)} services"
            return (True, configs, message)
        
        except Exception as e:
            logger.error(f"Configuration generation failed: {e}")
            return (False, {}, f"Generation failed: {str(e)}")
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """
        Validate configuration.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, warnings)
        """
        warnings = []
        
        if not self.state.platform:
            return (False, ["Platform not selected"])
        
        if not self.state.services:
            return (False, ["No services selected"])
        
        if not self.state.modules:
            warnings.append("No additional modules selected (only pam_unix)")
        
        if self.state.hardened_mode and not self.state.backup_enabled:
            warnings.append("Hardened mode without backup enabled - risky!")
        
        return (True, warnings)
    
    def get_progress(self) -> Tuple[int, int]:
        """
        Get wizard progress.
        
        Returns:
            Tuple[int, int]: (current_step, total_steps)
        """
        return (self.state.current_step, len(self.STEPS))
    
    def next_step(self) -> bool:
        """Advance to next step."""
        if self.state.current_step < len(self.STEPS) - 1:
            self.state.current_step += 1
            return True
        return False
    
    def previous_step(self) -> bool:
        """Go back to previous step."""
        if self.state.current_step > 0:
            self.state.current_step -= 1
            return True
        return False
    
    def get_current_step_name(self) -> str:
        """Get name of current step."""
        return self.STEPS[self.state.current_step] if self.state.current_step < len(self.STEPS) else "complete"
    
    def get_step_instructions(self, step_name: str) -> str:
        """Get instructions for a step."""
        instructions = {
            "platform_selection": "Select your operating system platform",
            "service_selection": "Choose which PAM services to configure",
            "module_selection": "Select additional PAM modules",
            "security_level": "Choose security hardening level",
            "backup_verification": "Verify backup settings",
            "review_and_apply": "Review configuration and apply",
        }
        return instructions.get(step_name, "")
