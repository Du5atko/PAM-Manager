"""Platform-specific configuration generation for PAM modules."""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict
import logging

from pam_manager.platform.metadata import (
    Platform,
    PlatformMetadata,
    PlatformModuleConfig,
    PAMFacility,
)


logger = logging.getLogger(__name__)


class PlatformConfigGenerator:
    """Generate platform-specific PAM configurations."""
    
    def __init__(self, platform: Platform):
        """
        Initialize configuration generator.
        
        Args:
            platform: Target platform
        """
        self.platform = platform
        self.config_path = PlatformMetadata.get_config_path(platform)
        self.module_paths = PlatformMetadata.get_module_paths(platform)
        self.package_manager = PlatformMetadata.get_package_manager(platform)
    
    def generate_module_path(self, module_name: str) -> str:
        """
        Generate full module path for platform.
        
        Args:
            module_name: PAM module name (without .so)
            
        Returns:
            str: Full module path
        """
        naming_pattern = PlatformMetadata.get_module_naming(self.platform)
        module_filename = naming_pattern.format(module=module_name)
        return f"{self.module_paths[0]}/{module_filename}"
    
    def generate_service_config(
        self, 
        service_name: str,
        pam_rules: List[str],
        facility: PAMFacility = PAMFacility.AUTH
    ) -> str:
        """
        Generate service-specific PAM configuration.
        
        Args:
            service_name: Service name (e.g., 'sshd', 'login')
            pam_rules: List of PAM rules
            facility: PAM facility type
            
        Returns:
            str: Generated configuration
        """
        config = f"# {service_name} PAM configuration\n"
        config += f"# Generated for {self.platform.value}\n"
        config += f"# Facility: {facility.value}\n\n"
        
        for rule in pam_rules:
            config += f"{rule}\n"
        
        return config
    
    def generate_module_line(
        self,
        module_name: str,
        control: str = "required",
        arguments: Optional[List[str]] = None,
        facility: PAMFacility = PAMFacility.AUTH
    ) -> str:
        """
        Generate a single PAM module line.
        
        Args:
            module_name: PAM module name
            control: Control flag (required, sufficient, optional, etc.)
            arguments: Module arguments
            facility: PAM facility
            
        Returns:
            str: Generated PAM line
        """
        module_path = self.generate_module_path(module_name)
        args_str = " ".join(arguments or [])
        
        if args_str:
            return f"{facility.value}\t{control}\t{module_path}\t{args_str}"
        else:
            return f"{facility.value}\t{control}\t{module_path}"
    
    def generate_linux_sshd_config(self) -> str:
        """Generate SSH daemon PAM configuration for Linux."""
        if not PlatformMetadata.is_linux(self.platform):
            logger.warning("Linux SSH config requested for non-Linux platform")
            return ""
        
        rules = [
            "# SSH authentication",
            "auth       required     pam_unix.so try_first_pass",
            "auth       optional     pam_faillock.so preauth silent audit deny=5 unlock_time=900",
            "",
            "# Account verification",
            "account    required     pam_unix.so",
            "account    required     pam_faillock.so",
            "",
            "# Session setup",
            "session    required     pam_unix.so",
            "session    optional     pam_lastlog.so showfailed",
            "",
            "# Password management",
            "password   required     pam_unix.so sha512 shadow remember=5",
        ]
        
        return self.generate_service_config("sshd", rules)
    
    def generate_bsd_sshd_config(self) -> str:
        """Generate SSH daemon PAM configuration for BSD."""
        if not PlatformMetadata.is_bsd(self.platform):
            logger.warning("BSD SSH config requested for non-BSD platform")
            return ""
        
        rules = [
            "# SSH authentication for BSD",
            "auth       required     pam_unix.so try_first_pass",
            "",
            "# Account verification",
            "account    required     pam_unix.so",
            "",
            "# Session setup",
            "session    required     pam_unix.so",
            "",
            "# Password management",
            "password   required     pam_unix.so sha512",
        ]
        
        return self.generate_service_config("sshd", rules)
    
    def generate_login_config(self) -> str:
        """Generate login service PAM configuration."""
        if PlatformMetadata.is_linux(self.platform):
            rules = [
                "# Login authentication",
                "auth       required     pam_unix.so",
                "auth       optional     pam_faillock.so preauth silent audit deny=5",
                "",
                "# Account verification",
                "account    required     pam_unix.so",
                "account    optional     pam_faillock.so",
                "",
                "# Session setup",
                "session    required     pam_unix.so",
                "session    optional     pam_lastlog.so showfailed",
                "session    optional     pam_motd.so motd=/etc/motd noupdate",
                "",
                "# Password management",
                "password   required     pam_unix.so sha512 shadow remember=5",
            ]
        else:  # BSD
            rules = [
                "# Login authentication",
                "auth       required     pam_unix.so",
                "",
                "# Account verification",
                "account    required     pam_unix.so",
                "",
                "# Session setup",
                "session    required     pam_unix.so",
                "",
                "# Password management",
                "password   required     pam_unix.so sha512",
            ]
        
        return self.generate_service_config("login", rules)
    
    def generate_security_hardened_config(self) -> Dict[str, str]:
        """
        Generate hardened security configuration for all services.
        
        Returns:
            Dict[str, str]: Service name -> configuration mapping
        """
        configs = {}
        
        # SSH daemon
        if PlatformMetadata.is_linux(self.platform):
            configs["sshd"] = self.generate_linux_sshd_config()
        else:
            configs["sshd"] = self.generate_bsd_sshd_config()
        
        # Login service
        configs["login"] = self.generate_login_config()
        
        # Additional services
        if PlatformMetadata.is_linux(self.platform):
            configs["sudo"] = self.generate_sudo_config()
            configs["su"] = self.generate_su_config()
        
        return configs
    
    def generate_sudo_config(self) -> str:
        """Generate sudo PAM configuration for Linux."""
        rules = [
            "# Sudo authentication",
            "auth       required     pam_unix.so try_first_pass",
            "auth       required     pam_env.so user_readenv=1",
            "",
            "# Account verification",
            "account    required     pam_unix.so",
            "",
            "# Session setup",
            "session    required     pam_unix.so",
            "session    optional     pam_lastlog.so showfailed",
        ]
        
        return self.generate_service_config("sudo", rules)
    
    def generate_su_config(self) -> str:
        """Generate su PAM configuration for Linux."""
        rules = [
            "# su authentication",
            "auth       sufficient   pam_unix.so use_first_pass",
            "auth       required     pam_rootok.so",
            "",
            "# Account verification",
            "account    required     pam_unix.so",
            "",
            "# Session setup",
            "session    required     pam_unix.so",
        ]
        
        return self.generate_service_config("su", rules)
    
    def generate_json_config(self, config_dict: Dict[str, str]) -> str:
        """
        Generate JSON representation of configurations.
        
        Args:
            config_dict: Service -> config mapping
            
        Returns:
            str: JSON representation
        """
        output = {
            "platform": self.platform.value,
            "config_path": self.config_path,
            "package_manager": self.package_manager,
            "module_paths": self.module_paths,
            "services": config_dict,
        }
        
        return json.dumps(output, indent=2)
    
    def get_module_installation_instructions(self, module_name: str) -> Dict[str, str]:
        """
        Get module installation instructions for platform.
        
        Args:
            module_name: PAM module name
            
        Returns:
            Dict[str, str]: Installation instructions
        """
        pm = self.package_manager
        
        instructions = {
            "platform": self.platform.value,
            "package_manager": pm,
        }
        
        # Package names by platform
        package_map = {
            "apt": f"libpam-{module_name.replace('_', '-')}",
            "dnf": f"pam-{module_name}",
            "yum": f"pam-{module_name}",
            "pacman": f"pam-{module_name}",
            "pkg": f"pam-{module_name}",
            "pkgin": f"pam-{module_name}",
            "brew": f"pam-{module_name}",
        }
        
        instructions["package"] = package_map.get(pm, module_name)
        
        # Installation commands
        install_commands = {
            "apt": f"sudo apt-get install {instructions['package']}",
            "dnf": f"sudo dnf install {instructions['package']}",
            "yum": f"sudo yum install {instructions['package']}",
            "pacman": f"sudo pacman -S {instructions['package']}",
            "pkg": f"sudo pkg install {instructions['package']}",
            "pkgin": f"pkgin install {instructions['package']}",
            "brew": f"brew install {instructions['package']}",
        }
        
        instructions["install_command"] = install_commands.get(pm, "Manual installation required")
        
        return instructions


class PlatformCompatibilityChecker:
    """Check module compatibility across platforms."""
    
    @staticmethod
    def get_compatible_modules(
        module_name: str,
        platform: Platform
    ) -> Tuple[bool, List[str]]:
        """
        Check if module is compatible with platform.
        
        Args:
            module_name: PAM module name
            platform: Target platform
            
        Returns:
            Tuple[bool, List[str]]: (is_compatible, alternatives_if_not)
        """
        # Get variants for common categories
        if "pwquality" in module_name or "cracklib" in module_name:
            variants = PlatformMetadata.get_module_variants("password_quality", platform)
            return (module_name in variants, [v for v in variants if v != module_name])
        
        if "faillock" in module_name or "tally" in module_name:
            variants = PlatformMetadata.get_module_variants("account_lockout", platform)
            return (module_name in variants, [v for v in variants if v != module_name])
        
        if "unix" in module_name:
            variants = PlatformMetadata.get_module_variants("unix_authentication", platform)
            return (module_name in variants, [])
        
        # Default: assume compatible
        return (True, [])
    
    @staticmethod
    def get_platform_differences(modules: List[str]) -> Dict[Platform, List[str]]:
        """
        Get differences in module availability across platforms.
        
        Args:
            modules: List of module names
            
        Returns:
            Dict[Platform, List[str]]: Platform -> incompatible modules
        """
        differences = {}
        
        for platform in Platform:
            incompatible = [
                mod for mod in modules
                if not PlatformCompatibilityChecker.get_compatible_modules(mod, platform)[0]
            ]
            if incompatible:
                differences[platform] = incompatible
        
        return differences
