"""Base module definitions and database structure."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from pam_manager.core import PAMFacility, PAMControlFlag, Platform


@dataclass(frozen=True)
class PAMModuleInfo:
    """Complete information about a PAM module."""

    name: str
    description: str
    detailed_description: str  # 3-5 sentence detailed description of module purpose
    category: str  # authentication, account, password, session
    supported_facilities: Set[PAMFacility]
    supported_platforms: Set[Platform]
    parameters: Dict[str, str]  # parameter_name: description
    dependencies: Set[str]  # Names of modules this depends on
    conflicts: Set[str]  # Names of modules this conflicts with
    package_name_debian: Optional[str]
    package_name_rhel: Optional[str]
    package_name_freebsd: Optional[str]
    preferred_control_flag: PAMControlFlag
    recommended_ordering: int  # Lower = earlier in stack
    deprecated: bool = False
    maintenance_status: str = "maintained"  # maintained, unmaintained, deprecated
    security_impact: str = ""  # High, Medium, Low
    documentation_url: str = ""
    notes: str = ""
    supported_extended_return_values: Set[str] = field(default_factory=lambda: {"success", "ignore", "default"})  # Extended syntax return values
    supported_extended_actions: Set[str] = field(default_factory=lambda: {"ignore", "ok", "done", "reset"})  # Extended syntax actions

    def get_package_name(self, platform: Platform) -> Optional[str]:
        """Get package name for a platform."""
        if platform in (
            Platform.DEBIAN,
            Platform.UBUNTU,
            Platform.LINUX_MINT,
            Platform.KALI_LINUX,
        ):
            return self.package_name_debian
        if platform in (
            Platform.REDHAT,
            Platform.ROCKY_LINUX,
            Platform.ALMA_LINUX,
            Platform.CENTOS_STREAM,
            Platform.FEDORA,
        ):
            return self.package_name_rhel
        if platform == Platform.FREEBSD:
            return self.package_name_freebsd
        return None

    def supports_facility(self, facility: PAMFacility) -> bool:
        """Check if module supports facility."""
        return facility in self.supported_facilities

    def supports_platform(self, platform: Platform) -> bool:
        """Check if module supports platform."""
        return platform in self.supported_platforms


__all__ = ["PAMModuleInfo"]
