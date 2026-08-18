"""YUM package manager for RHEL 7 and older systems."""

import subprocess
from typing import List, Optional

from pam_manager.package_manager.base import (
    InstallationResult,
    PackageInfo,
    PackageManager,
)


class YUMPackageManager(PackageManager):
    """YUM package manager implementation for RHEL 7 and older."""

    def __init__(self) -> None:
        """Initialize YUM package manager."""
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
                ["rpm", "-qa"],
                capture_output=True,
                text=True,
                check=False,
            )

            packages = []
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line:
                    # Extract package name from rpm format (name-version-release.arch)
                    parts = line.split("-")
                    if len(parts) >= 2:
                        # Remove arch suffix
                        name = "-".join(parts[:-2])
                        if name:
                            packages.append(name)

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
                ["yum", "search", query],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

            packages = []
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line and not line.startswith("="):
                    parts = line.split()
                    if parts and ".x86_64" in parts[0] or ".noarch" in parts[0]:
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
                ["sudo", "yum", "install", "-y", package_name],
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
                ["rpm", "-q", package_name],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                # Format is name-version-release.arch
                parts = output.split("-")
                if len(parts) >= 3:
                    # version is second-to-last before arch
                    return "-".join(parts[-2:]).split(".")[0]

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
                ["sudo", "yum", "check-update"],
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )

            self._installed_cache = None  # Invalidate cache
            # yum check-update returns 100 if updates available, 0 if none
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
                ["yum", "info", package_name],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            return result.returncode == 0 and "Name" in result.stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False


__all__ = ["YUMPackageManager"]
