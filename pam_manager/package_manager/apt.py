"""APT package manager for Debian/Ubuntu systems."""

import subprocess
from typing import List, Optional

from pam_manager.package_manager.base import (
    InstallationResult,
    PackageInfo,
    PackageManager,
)


class APTPackageManager(PackageManager):
    """APT package manager implementation for Debian/Ubuntu."""

    def __init__(self) -> None:
        """Initialize APT package manager."""
        self._installed_cache: Optional[List[str]] = None

    def get_installed_packages(self) -> List[str]:
        """Get list of installed packages.

        Returns:
            List of package names
        """
        if self._installed_cache is not None:
            return self._installed_cache

        try:
            result = subprocess.run(
                ["dpkg", "-l"],
                capture_output=True,
                text=True,
                check=False,
            )

            packages = []
            for line in result.stdout.split("\n"):
                if line.startswith("ii"):
                    parts = line.split()
                    if len(parts) >= 2:
                        packages.append(parts[1])

            self._installed_cache = packages
            return packages
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []

    def get_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """Get information about a package.

        Args:
            package_name: Name of package

        Returns:
            PackageInfo or None if not found
        """
        installed = self.is_installed(package_name)
        version = self.get_package_version(package_name) if installed else None

        if installed or self._package_available_in_repo(package_name):
            return PackageInfo(
                name=package_name,
                version=version,
                installed=installed,
                available_in_repo=not installed,
            )

        return None

    def search_package(self, query: str) -> List[str]:
        """Search for packages by name.

        Args:
            query: Search query

        Returns:
            List of matching package names
        """
        try:
            result = subprocess.run(
                ["apt-cache", "search", "--names-only", query],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            packages = []
            for line in result.stdout.split("\n"):
                if line.strip():
                    parts = line.split()
                    if parts:
                        packages.append(parts[0])

            return packages
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return []

    def search_available(self, package_name: str) -> List[PackageInfo]:
        """Search for available packages in repositories.

        Args:
            package_name: Package name or pattern

        Returns:
            List of available packages
        """
        matching = self.search_package(package_name)
        results = []

        for pkg_name in matching:
            info = self.get_package_info(pkg_name)
            if info:
                results.append(info)

        return results

    def is_installed(self, package_name: str) -> bool:
        """Check if package is installed.

        Args:
            package_name: Package name

        Returns:
            True if installed, False otherwise
        """
        installed_packages = self.get_installed_packages()
        return package_name in installed_packages

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
        if self.is_installed(package_name):
            return InstallationResult(
                success=True,
                package_name=package_name,
                already_installed=True,
            )

        if dry_run:
            # Simulate installation
            return InstallationResult(
                success=True,
                package_name=package_name,
                version="(simulated)",
            )

        try:
            result = subprocess.run(
                ["sudo", "apt-get", "install", "-y", package_name],
                capture_output=True,
                text=True,
                check=False,
                timeout=300,
            )

            if result.returncode == 0:
                return InstallationResult(
                    success=True,
                    package_name=package_name,
                    version=self.get_package_version(package_name),
                )
            else:
                return InstallationResult(
                    success=False,
                    package_name=package_name,
                    error_message=result.stderr or "Installation failed",
                )
        except subprocess.TimeoutExpired:
            return InstallationResult(
                success=False,
                package_name=package_name,
                error_message="Installation timed out",
            )
        except Exception as e:
            return InstallationResult(
                success=False,
                package_name=package_name,
                error_message=str(e),
            )

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
        if dry_run:
            return [
                InstallationResult(
                    success=True,
                    package_name=pkg,
                    version="(simulated)",
                )
                for pkg in package_names
            ]

        results = []
        for pkg_name in package_names:
            results.append(self.install_package(pkg_name, dry_run=False))

        return results

    def get_package_version(self, package_name: str) -> Optional[str]:
        """Get version of installed package.

        Args:
            package_name: Package name

        Returns:
            Version string or None if not installed
        """
        try:
            result = subprocess.run(
                ["dpkg", "-l", package_name],
                capture_output=True,
                text=True,
                check=False,
            )

            for line in result.stdout.split("\n"):
                if line.startswith("ii"):
                    parts = line.split()
                    if len(parts) >= 3 and parts[1] == package_name:
                        return parts[2]

            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def update_package_cache(self) -> bool:
        """Update package cache/index.

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["sudo", "apt-get", "update"],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )

            self._installed_cache = None  # Invalidate cache
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def _package_available_in_repo(self, package_name: str) -> bool:
        """Check if package is available in repository.

        Args:
            package_name: Package name

        Returns:
            True if available, False otherwise
        """
        try:
            result = subprocess.run(
                ["apt-cache", "show", package_name],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            return result.returncode == 0 and len(result.stdout) > 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False


__all__ = ["APTPackageManager"]
