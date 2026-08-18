"""Base package manager interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass(frozen=True)
class PackageInfo:
    """Information about a package."""

    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    installed: bool = False
    available_in_repo: bool = False


@dataclass(frozen=True)
class InstallationResult:
    """Result of package installation."""

    success: bool
    package_name: str
    version: Optional[str] = None
    error_message: Optional[str] = None
    already_installed: bool = False


class PackageManager(ABC):
    """Abstract base class for package managers."""

    @abstractmethod
    def get_installed_packages(self) -> List[str]:
        """Get list of installed packages.

        Returns:
            List of package names
        """
        pass

    @abstractmethod
    def get_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """Get information about a package.

        Args:
            package_name: Name of package

        Returns:
            PackageInfo or None if not found
        """
        pass

    @abstractmethod
    def search_package(self, query: str) -> List[str]:
        """Search for packages by name or description.

        Args:
            query: Search query

        Returns:
            List of matching package names
        """
        pass

    @abstractmethod
    def search_available(self, package_name: str) -> List[PackageInfo]:
        """Search for available packages in repositories.

        Args:
            package_name: Package name or pattern

        Returns:
            List of available packages
        """
        pass

    @abstractmethod
    def is_installed(self, package_name: str) -> bool:
        """Check if package is installed.

        Args:
            package_name: Package name

        Returns:
            True if installed, False otherwise
        """
        pass

    @abstractmethod
    def install_package(
        self, package_name: str, dry_run: bool = False
    ) -> InstallationResult:
        """Install a package.

        Args:
            package_name: Package name
            dry_run: If True, simulate without actually installing

        Returns:
            InstallationResult with status and details
        """
        pass

    @abstractmethod
    def install_packages(
        self, package_names: List[str], dry_run: bool = False
    ) -> List[InstallationResult]:
        """Install multiple packages.

        Args:
            package_names: List of package names
            dry_run: If True, simulate without actually installing

        Returns:
            List of InstallationResult for each package
        """
        pass

    @abstractmethod
    def get_package_version(self, package_name: str) -> Optional[str]:
        """Get version of installed package.

        Args:
            package_name: Package name

        Returns:
            Version string or None if not installed
        """
        pass

    @abstractmethod
    def update_package_cache(self) -> bool:
        """Update package cache/index.

        Returns:
            True if successful, False otherwise
        """
        pass


__all__ = ["PackageManager", "PackageInfo", "InstallationResult"]
