"""DNF package manager for Fedora/RedHat 8+ systems."""

import subprocess
from typing import List, Optional

from pam_manager.package_manager.base import (
    InstallationResult,
    PackageInfo,
    PackageManager,
)


class DNFPackageManager(PackageManager):
    """DNF package manager implementation for Fedora/RedHat 8+."""

    def __init__(self) -> None:
        """Initialize DNF package manager."""
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
                ["dnf", "list", "installed"],
                capture_output=True,
                text=True,
                check=False,
            )

            packages = []
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line and not line.startswith("Installed"):
                    parts = line.split()
                    if parts:
                        # Package name might have arch info, extract base name
                        pkg_name = parts[0].split(".")[0]
                        packages.append(pkg_name)

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
                ["dnf", "search", query],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

            packages = []
            for line in result.stdout.split("\n"):
                line = line.strip()
                if ".x86_64" in line or ".noarch" in line or ".aarch64" in line:
                    parts = line.split()
                    if parts:
                        pkg_name = parts[0].split(".")[0]
                        packages.append(pkg_name)

            return list(set(packages))  # Remove duplicates
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
        # Handle both exact and partial matches
        return package_name in installed_packages or any(
            pkg.startswith(package_name + "-") for pkg in installed_packages
        )

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
            return InstallationResult(
                success=True,
                package_name=package_name,
                version="(simulated)",
            )

        try:
            result = subprocess.run(
                ["sudo", "dnf", "install", "-y", package_name],
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
                ["dnf", "info", package_name],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            for line in result.stdout.split("\n"):
                if line.startswith("Version"):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        return parts[1].strip()

            return None
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None

    def update_package_cache(self) -> bool:
        """Update package cache/index.

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["sudo", "dnf", "check-update"],
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )

            self._installed_cache = None  # Invalidate cache
            # dnf check-update returns 100 if updates available, 0 if none
            return result.returncode in (0, 100)
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
                ["dnf", "info", package_name],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            return result.returncode == 0 and "Name" in result.stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False


__all__ = ["DNFPackageManager"]
