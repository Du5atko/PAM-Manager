"""Factory for creating appropriate package manager instances."""

from pam_manager.core import PackageManager, Platform
from pam_manager.package_manager.apt import APTPackageManager
from pam_manager.package_manager.base import PackageManager as BasePackageManager
from pam_manager.package_manager.dnf import DNFPackageManager
from pam_manager.package_manager.pkg import PKGPackageManager
from pam_manager.package_manager.yum import YUMPackageManager


class PackageManagerFactory:
    """Factory for creating platform-specific package manager instances."""

    @staticmethod
    def create(package_manager: PackageManager) -> BasePackageManager:
        """Create a package manager instance for the given package manager type.

        Args:
            package_manager: PackageManager enum value

        Returns:
            Instance of appropriate PackageManager subclass

        Raises:
            ValueError: If package manager type is not supported
        """
        if package_manager == PackageManager.APT:
            return APTPackageManager()
        elif package_manager == PackageManager.DNF:
            return DNFPackageManager()
        elif package_manager == PackageManager.YUM:
            return YUMPackageManager()
        elif package_manager == PackageManager.PKG:
            return PKGPackageManager()
        else:
            raise ValueError(f"Unsupported package manager: {package_manager}")

    @staticmethod
    def create_for_platform(platform: Platform) -> BasePackageManager:
        """Create a package manager instance for the given platform.

        Args:
            platform: Platform enum value

        Returns:
            Instance of appropriate PackageManager subclass

        Raises:
            ValueError: If platform is not supported
        """
        from pam_manager.platform.detector import PlatformDetector

        pkg_mgr = PlatformDetector.detect_package_manager(platform)
        return PackageManagerFactory.create(pkg_mgr)


__all__ = ["PackageManagerFactory"]
