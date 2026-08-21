"""Enhanced platform detection and capabilities."""

import logging
from typing import Dict, List, Optional
import subprocess
import json
import re

from pam_manager.platform.metadata import (
    Platform,
    PlatformMetadata,
    PlatformPackageManager,
)


logger = logging.getLogger(__name__)


class PlatformDetector:
    """Enhanced platform detection with capabilities assessment."""
    
    @staticmethod
    def detect_platform() -> Optional[Platform]:
        """
        Detect current platform.
        
        Returns:
            Platform: Detected platform or None
        """
        try:
            # Try /etc/os-release first (modern systems)
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                
                if 'ubuntu' in content:
                    return Platform.LINUX_UBUNTU
                elif 'debian' in content and 'ubuntu' not in content:
                    return Platform.LINUX_DEBIAN
                elif 'linuxmint' in content or 'mint' in content:
                    return Platform.LINUX_MINT
                elif 'fedora' in content:
                    return Platform.LINUX_FEDORA
                elif 'rhel' in content or 'red hat' in content:
                    return Platform.LINUX_REDHAT
                elif 'almalinux' in content:
                    return Platform.LINUX_ALMA
                elif 'rocky' in content:
                    return Platform.LINUX_ROCKY
                elif 'centos' in content:
                    return Platform.LINUX_CENTOS
                elif 'kali' in content:
                    return Platform.LINUX_KALI
        except FileNotFoundError:
            pass
        
        try:
            # Try /etc/lsb-release (older Ubuntu/Debian)
            with open('/etc/lsb-release', 'r') as f:
                content = f.read().upper()
                if 'UBUNTU' in content:
                    return Platform.LINUX_UBUNTU
                elif 'DEBIAN' in content:
                    return Platform.LINUX_DEBIAN
        except FileNotFoundError:
            pass
        
        try:
            # Try system info (BSD/macOS)
            result = subprocess.run(['uname', '-s'], capture_output=True, text=True, timeout=5)
            system = result.stdout.strip().lower()
            
            if 'freebsd' in system:
                return Platform.BSD_FREEBSD
            elif 'openbsd' in system:
                return Platform.BSD_OPENBSD
            elif 'netbsd' in system:
                return Platform.BSD_NETBSD
            elif 'darwin' in system:
                return Platform.MACOS
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None
    
    @staticmethod
    def get_pam_version(platform: Platform) -> Optional[str]:
        """
        Get PAM version on platform.
        
        Args:
            platform: Target platform
            
        Returns:
            str: PAM version or None
        """
        try:
            # Try to get PAM version
            result = subprocess.run(
                ['pam_tally2', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse version from output
                match = re.search(r'(\d+\.\d+\.\d+)', result.stdout)
                if match:
                    return match.group(1)
            
            # Try alternative
            result = subprocess.run(
                ['pam-config', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                match = re.search(r'(\d+\.\d+\.\d+)', result.stdout)
                if match:
                    return match.group(1)
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None
    
    @staticmethod
    def check_module_available(module_name: str, platform: Platform) -> bool:
        """
        Check if PAM module is available on platform.
        
        Args:
            module_name: Module name
            platform: Target platform
            
        Returns:
            bool: True if module is available
        """
        module_paths = PlatformMetadata.get_module_paths(platform)
        naming_pattern = PlatformMetadata.get_module_naming(platform)
        module_filename = naming_pattern.format(module=module_name)
        
        for path in module_paths:
            full_path = f"{path}/{module_filename}"
            try:
                result = subprocess.run(
                    ['test', '-f', full_path],
                    timeout=5
                )
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return False
    
    @staticmethod
    def get_available_modules(platform: Platform) -> List[str]:
        """
        Get all available PAM modules on platform.
        
        Args:
            platform: Target platform
            
        Returns:
            List[str]: Available module names
        """
        available = []
        module_paths = PlatformMetadata.get_module_paths(platform)
        
        try:
            for path in module_paths:
                result = subprocess.run(
                    ['ls', path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    for filename in result.stdout.strip().split('\n'):
                        if filename.startswith('pam_') and filename.endswith('.so'):
                            # Extract module name
                            module_name = filename[4:-3]  # Remove pam_ prefix and .so suffix
                            if module_name not in available:
                                available.append(module_name)
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning(f"Could not enumerate modules for {platform.value}")
        
        return sorted(available)


class PlatformCapabilities:
    """Platform capabilities assessment."""
    
    @staticmethod
    def assess_capabilities(platform: Platform) -> Dict[str, bool]:
        """
        Assess platform capabilities for PAM features.
        
        Args:
            platform: Target platform
            
        Returns:
            Dict[str, bool]: Feature -> supported mapping
        """
        capabilities = {
            "multi_facility": True,
            "control_flags": True,
            "modules": {
                "unix": PlatformDetector.check_module_available("unix", platform),
                "pwquality": PlatformDetector.check_module_available("pwquality", platform),
                "cracklib": PlatformDetector.check_module_available("cracklib", platform),
                "faillock": PlatformDetector.check_module_available("faillock", platform),
                "tally2": PlatformDetector.check_module_available("tally2", platform),
                "ldap": PlatformDetector.check_module_available("ldap", platform),
                "krb5": PlatformDetector.check_module_available("krb5", platform),
                "systemd": PlatformDetector.check_module_available("systemd", platform),
                "selinux": PlatformDetector.check_module_available("selinux", platform),
                "apparmor": PlatformDetector.check_module_available("apparmor", platform),
            },
        }
        
        # Add BSD-specific capabilities
        if PlatformMetadata.is_bsd(platform):
            capabilities["pam_conf"] = True
            capabilities["services_in_pam_conf"] = True
        else:
            capabilities["pam_d_directory"] = True
            capabilities["services_as_files"] = True
        
        return capabilities
    
    @staticmethod
    def get_platform_summary(platform: Platform) -> Dict[str, any]:
        """
        Get comprehensive platform summary.
        
        Args:
            platform: Target platform
            
        Returns:
            Dict[str, any]: Platform information
        """
        return {
            "platform": platform.value,
            "category": (
                "linux" if PlatformMetadata.is_linux(platform) else
                "bsd" if PlatformMetadata.is_bsd(platform) else
                "macos"
            ),
            "pam_config_path": PlatformMetadata.get_config_path(platform),
            "module_paths": PlatformMetadata.get_module_paths(platform),
            "package_manager": PlatformMetadata.get_package_manager(platform),
            "available_modules": PlatformDetector.get_available_modules(platform),
            "capabilities": PlatformCapabilities.assess_capabilities(platform),
        }


class PlatformCompatibilityMatrix:
    """Generate compatibility matrix for modules across platforms."""
    
    @staticmethod
    def generate_matrix(modules: List[str]) -> Dict[str, Dict[str, bool]]:
        """
        Generate compatibility matrix.
        
        Args:
            modules: List of module names
            
        Returns:
            Dict[str, Dict[str, bool]]: Platform -> module -> compatible
        """
        matrix = {}
        
        for platform in Platform:
            matrix[platform.value] = {}
            for module in modules:
                available = PlatformDetector.check_module_available(module, platform)
                matrix[platform.value][module] = available
        
        return matrix
    
    @staticmethod
    def get_universal_modules(all_modules: List[str]) -> List[str]:
        """
        Get modules available on all platforms.
        
        Args:
            all_modules: List of all module names
            
        Returns:
            List[str]: Modules available everywhere
        """
        universal = []
        
        for module in all_modules:
            available_on_all = True
            for platform in Platform:
                if not PlatformDetector.check_module_available(module, platform):
                    available_on_all = False
                    break
            
            if available_on_all:
                universal.append(module)
        
        return universal
    
    @staticmethod
    def get_platform_specific_modules(
        all_modules: List[str],
        platform: Platform
    ) -> List[str]:
        """
        Get modules specific to a platform.
        
        Args:
            all_modules: List of all module names
            platform: Target platform
            
        Returns:
            List[str]: Platform-specific modules
        """
        specific = []
        
        for module in all_modules:
            available_here = PlatformDetector.check_module_available(module, platform)
            available_elsewhere = False
            
            for other_platform in Platform:
                if other_platform != platform:
                    if PlatformDetector.check_module_available(module, other_platform):
                        available_elsewhere = True
                        break
            
            if available_here and not available_elsewhere:
                specific.append(module)
        
        return specific
