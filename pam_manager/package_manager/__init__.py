"""Package manager package - platform-specific package management."""

from pam_manager.package_manager.apt import APTPackageManager
from pam_manager.package_manager.base import (
    InstallationResult,
    PackageInfo,
    PackageManager,
)
from pam_manager.package_manager.dnf import DNFPackageManager
from pam_manager.package_manager.factory import PackageManagerFactory
from pam_manager.package_manager.pkg import PKGPackageManager
from pam_manager.package_manager.yum import YUMPackageManager

__all__ = [
    "PackageManager",
    "PackageInfo",
    "InstallationResult",
    "APTPackageManager",
    "DNFPackageManager",
    "YUMPackageManager",
    "PKGPackageManager",
    "PackageManagerFactory",
]
