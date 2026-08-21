"""Platform-aware module metadata and configuration for PAM."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class Platform(Enum):
    """Supported platforms."""
    LINUX_UBUNTU = "UBUNTU"
    LINUX_DEBIAN = "DEBIAN"
    LINUX_MINT = "LINUX_MINT"
    LINUX_FEDORA = "FEDORA"
    LINUX_REDHAT = "REDHAT"
    LINUX_ALMA = "ALMA_LINUX"
    LINUX_ROCKY = "ROCKY_LINUX"
    LINUX_CENTOS = "CENTOS_STREAM"
    LINUX_KALI = "KALI_LINUX"
    BSD_FREEBSD = "FREEBSD"
    BSD_OPENBSD = "OPENBSD"
    BSD_NETBSD = "NETBSD"
    MACOS = "MACOS"


class PAMFacility(Enum):
    """PAM facilities."""
    AUTH = "auth"
    ACCOUNT = "account"
    SESSION = "session"
    PASSWORD = "password"


@dataclass
class PlatformParameter:
    """Platform-specific parameter configuration."""
    name: str
    type: str  # 'string', 'boolean', 'integer', 'list'
    required: bool = False
    default: Optional[str] = None
    platforms: List[Platform] = field(default_factory=list)
    description: str = ""
    security_level: str = "medium"  # 'low', 'medium', 'high', 'critical'
    notes: str = ""


@dataclass
class PlatformModuleConfig:
    """Platform-specific module configuration."""
    module_name: str
    platform: Platform
    parameters: List[PlatformParameter] = field(default_factory=list)
    config_path: Optional[str] = None  # e.g., /etc/pam.d/ for Linux
    enabled_by_default: bool = True
    service_patterns: Dict[str, str] = field(default_factory=dict)  # service -> config pattern
    notes: str = ""
    alternatives: List[str] = field(default_factory=list)  # Alternative modules on this platform
    conflicts_with: List[str] = field(default_factory=list)  # Conflicting modules


@dataclass
class PlatformPackageManager:
    """Platform-specific package manager configuration."""
    platform: Platform
    package_manager: str  # 'apt', 'yum', 'dnf', 'pacman', 'brew', 'pkg'
    package_names: Dict[str, str] = field(default_factory=dict)  # module_name -> package_name
    install_command: str = ""
    service_restart_command: str = "systemctl restart pam"


class PlatformMetadata:
    """Centralized platform metadata and configuration."""
    
    # BSD vs Linux specific configs
    PLATFORM_CATEGORIES = {
        "linux": [
            Platform.LINUX_UBUNTU,
            Platform.LINUX_DEBIAN,
            Platform.LINUX_MINT,
            Platform.LINUX_FEDORA,
            Platform.LINUX_REDHAT,
            Platform.LINUX_ALMA,
            Platform.LINUX_ROCKY,
            Platform.LINUX_CENTOS,
            Platform.LINUX_KALI,
        ],
        "bsd": [
            Platform.BSD_FREEBSD,
            Platform.BSD_OPENBSD,
            Platform.BSD_NETBSD,
        ],
        "macos": [Platform.MACOS],
    }
    
    # Default PAM configuration paths by platform
    CONFIG_PATHS = {
        Platform.LINUX_UBUNTU: "/etc/pam.d",
        Platform.LINUX_DEBIAN: "/etc/pam.d",
        Platform.LINUX_MINT: "/etc/pam.d",
        Platform.LINUX_FEDORA: "/etc/pam.d",
        Platform.LINUX_REDHAT: "/etc/pam.d",
        Platform.LINUX_ALMA: "/etc/pam.d",
        Platform.LINUX_ROCKY: "/etc/pam.d",
        Platform.LINUX_CENTOS: "/etc/pam.d",
        Platform.LINUX_KALI: "/etc/pam.d",
        Platform.BSD_FREEBSD: "/etc/pam.d",
        Platform.BSD_OPENBSD: "/etc/pam.conf",
        Platform.BSD_NETBSD: "/etc/pam.conf",
        Platform.MACOS: "/etc/pam.d",
    }
    
    # Module library paths
    MODULE_PATHS = {
        Platform.LINUX_UBUNTU: [
            "/lib/x86_64-linux-gnu/security",
            "/lib/security",
        ],
        Platform.LINUX_DEBIAN: [
            "/lib/x86_64-linux-gnu/security",
            "/lib/security",
        ],
        Platform.LINUX_FEDORA: [
            "/lib64/security",
            "/lib/security",
        ],
        Platform.LINUX_REDHAT: [
            "/lib64/security",
            "/lib/security",
        ],
        Platform.BSD_FREEBSD: [
            "/usr/lib/pam",
        ],
        Platform.BSD_OPENBSD: [
            "/usr/lib/pam",
        ],
        Platform.MACOS: [
            "/usr/lib/pam",
        ],
    }
    
    # Module naming conventions
    MODULE_NAMING = {
        Platform.LINUX_UBUNTU: "pam_{module}.so",
        Platform.LINUX_DEBIAN: "pam_{module}.so",
        Platform.LINUX_FEDORA: "pam_{module}.so",
        Platform.LINUX_REDHAT: "pam_{module}.so",
        Platform.BSD_FREEBSD: "pam_{module}.so",
        Platform.BSD_OPENBSD: "pam_{module}.so",
        Platform.MACOS: "pam_{module}.so",
    }
    
    # Platform-specific module variants
    MODULE_VARIANTS = {
        "password_quality": {
            "linux": ["pam_pwquality", "pam_cracklib"],
            "bsd": ["pam_passwdqc"],
        },
        "account_lockout": {
            "linux": ["pam_faillock", "pam_tally2"],
            "bsd": [],
        },
        "unix_authentication": {
            "linux": ["pam_unix"],
            "bsd": ["pam_unix"],
            "macos": ["pam_unix"],
        },
        "ldap": {
            "linux": ["pam_ldap"],
            "bsd": ["pam_ldap"],
        },
    }
    
    @staticmethod
    def get_config_path(platform: Platform) -> str:
        """Get PAM configuration directory for platform."""
        return PlatformMetadata.CONFIG_PATHS.get(platform, "/etc/pam.d")
    
    @staticmethod
    def get_module_paths(platform: Platform) -> List[str]:
        """Get module library paths for platform."""
        return PlatformMetadata.MODULE_PATHS.get(platform, ["/lib/security"])
    
    @staticmethod
    def get_module_naming(platform: Platform) -> str:
        """Get module naming convention for platform."""
        return PlatformMetadata.MODULE_NAMING.get(platform, "pam_{module}.so")
    
    @staticmethod
    def is_linux(platform: Platform) -> bool:
        """Check if platform is Linux."""
        return platform in PlatformMetadata.PLATFORM_CATEGORIES["linux"]
    
    @staticmethod
    def is_bsd(platform: Platform) -> bool:
        """Check if platform is BSD."""
        return platform in PlatformMetadata.PLATFORM_CATEGORIES["bsd"]
    
    @staticmethod
    def is_macos(platform: Platform) -> bool:
        """Check if platform is macOS."""
        return platform in PlatformMetadata.PLATFORM_CATEGORIES["macos"]
    
    @staticmethod
    def get_module_variants(variant_type: str, platform: Platform) -> List[str]:
        """Get available module variants for a specific type on platform."""
        if variant_type not in PlatformMetadata.MODULE_VARIANTS:
            return []
        
        variants = PlatformMetadata.MODULE_VARIANTS[variant_type]
        
        # Determine platform category
        if PlatformMetadata.is_linux(platform):
            category = "linux"
        elif PlatformMetadata.is_bsd(platform):
            category = "bsd"
        elif PlatformMetadata.is_macos(platform):
            category = "macos"
        else:
            return []
        
        return variants.get(category, [])
    
    @staticmethod
    def get_package_manager(platform: Platform) -> str:
        """Get package manager for platform."""
        package_managers = {
            Platform.LINUX_UBUNTU: "apt",
            Platform.LINUX_DEBIAN: "apt",
            Platform.LINUX_MINT: "apt",
            Platform.LINUX_FEDORA: "dnf",
            Platform.LINUX_REDHAT: "yum",
            Platform.LINUX_ALMA: "dnf",
            Platform.LINUX_ROCKY: "dnf",
            Platform.LINUX_CENTOS: "yum",
            Platform.LINUX_KALI: "apt",
            Platform.BSD_FREEBSD: "pkg",
            Platform.BSD_OPENBSD: "pkg",
            Platform.BSD_NETBSD: "pkgin",
            Platform.MACOS: "brew",
        }
        return package_managers.get(platform, "unknown")
    
    @staticmethod
    def get_service_restart_command(platform: Platform) -> str:
        """Get service restart command for platform."""
        if PlatformMetadata.is_bsd(platform):
            return "/etc/rc.d/sshd restart"
        elif PlatformMetadata.is_macos(platform):
            return "sudo launchctl stop com.openssh.sshd && sudo launchctl start com.openssh.sshd"
        else:
            return "systemctl restart sshd"


# Pre-defined platform configurations
COMMON_PLATFORM_CONFIGS: Dict[str, PlatformModuleConfig] = {
    "pam_unix_linux": PlatformModuleConfig(
        module_name="pam_unix",
        platform=Platform.LINUX_UBUNTU,
        parameters=[
            PlatformParameter(
                name="sha512",
                type="boolean",
                default="yes",
                description="Use SHA512 hashing for passwords",
                security_level="high"
            ),
            PlatformParameter(
                name="shadow",
                type="boolean",
                default="yes",
                description="Use shadow password file",
                security_level="high"
            ),
        ],
        config_path="/etc/pam.d",
        enabled_by_default=True,
    ),
    "pam_unix_bsd": PlatformModuleConfig(
        module_name="pam_unix",
        platform=Platform.BSD_FREEBSD,
        parameters=[
            PlatformParameter(
                name="try_first_pass",
                type="boolean",
                default="yes",
                description="Try first password from previous module",
                security_level="medium"
            ),
        ],
        config_path="/etc/pam.d",
        enabled_by_default=True,
        alternatives=["pam_passwdqc"],
    ),
    "pam_pwquality_linux": PlatformModuleConfig(
        module_name="pam_pwquality",
        platform=Platform.LINUX_UBUNTU,
        parameters=[
            PlatformParameter(
                name="minlen",
                type="integer",
                default="12",
                description="Minimum password length",
                security_level="high"
            ),
            PlatformParameter(
                name="dcredit",
                type="integer",
                default="-1",
                description="Digits required",
                security_level="high"
            ),
            PlatformParameter(
                name="ucredit",
                type="integer",
                default="-1",
                description="Uppercase required",
                security_level="high"
            ),
        ],
        config_path="/etc/pam.d",
        enabled_by_default=True,
        conflicts_with=["pam_cracklib"],
    ),
}
