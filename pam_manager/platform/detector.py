"""Platform detection module."""

import json
import re
import subprocess
from pathlib import Path
from typing import Optional

from pam_manager.core import Platform, PackageManager, SystemInfo


class PlatformDetector:
    """Detects operating system, distribution, and platform information."""

    def __init__(self) -> None:
        """Initialize platform detector."""
        self._system_info: Optional[SystemInfo] = None

    @staticmethod
    def detect_platform() -> Platform:
        """Detect the current platform.

        Returns:
            Platform: Detected platform type

        Raises:
            RuntimeError: If platform cannot be detected
        """
        try:
            with open("/etc/os-release", "r") as f:
                os_release = {}
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        os_release[key] = value.strip('"')

            id_like = os_release.get("ID_LIKE", "").lower()
            dist_id = os_release.get("ID", "").lower()

            # Debian-based
            if dist_id == "debian":
                return Platform.DEBIAN
            if dist_id == "ubuntu":
                return Platform.UBUNTU
            if dist_id == "linuxmint":
                return Platform.LINUX_MINT
            if dist_id == "kali":
                return Platform.KALI_LINUX

            # RedHat-based
            if dist_id == "rhel":
                return Platform.REDHAT
            if dist_id == "rocky":
                return Platform.ROCKY_LINUX
            if dist_id == "almalinux":
                return Platform.ALMA_LINUX
            if dist_id == "centos":
                return Platform.CENTOS_STREAM
            if dist_id == "fedora":
                return Platform.FEDORA

            # Check ID_LIKE for partial matches
            if "debian" in id_like:
                return Platform.DEBIAN
            if "rhel" in id_like or "fedora" in id_like:
                return Platform.REDHAT

        except (FileNotFoundError, KeyError):
            pass

        # Try uname for FreeBSD
        try:
            result = subprocess.run(
                ["uname", "-s"],
                capture_output=True,
                text=True,
                check=True,
            )
            if "FreeBSD" in result.stdout:
                return Platform.FREEBSD
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return Platform.UNKNOWN

    @staticmethod
    def detect_package_manager(platform: Platform) -> PackageManager:
        """Detect package manager for platform.

        Args:
            platform: The detected platform

        Returns:
            PackageManager: The package manager for the platform
        """
        if platform in (
            Platform.DEBIAN,
            Platform.UBUNTU,
            Platform.LINUX_MINT,
            Platform.KALI_LINUX,
        ):
            return PackageManager.APT

        if platform in (
            Platform.FEDORA,
            Platform.ROCKY_LINUX,
            Platform.ALMA_LINUX,
            Platform.CENTOS_STREAM,
        ):
            # Prefer DNF on newer versions
            if Path("/usr/bin/dnf").exists():
                return PackageManager.DNF
            return PackageManager.YUM

        if platform == Platform.REDHAT:
            # RHEL 8+ has DNF, older has YUM
            if Path("/usr/bin/dnf").exists():
                return PackageManager.DNF
            return PackageManager.YUM

        if platform == Platform.FREEBSD:
            return PackageManager.PKG

        return PackageManager.UNKNOWN

    @staticmethod
    def get_os_release_info() -> dict:
        """Read /etc/os-release file.

        Returns:
            dict: Parsed os-release data
        """
        os_release = {}
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        os_release[key] = value.strip('"')
        except FileNotFoundError:
            pass
        return os_release

    @staticmethod
    def get_distribution_version() -> str:
        """Get distribution version.

        Returns:
            str: Distribution version string
        """
        os_release = PlatformDetector.get_os_release_info()
        return os_release.get("VERSION_ID", os_release.get("VERSION", "unknown"))

    @staticmethod
    def get_distribution_name() -> str:
        """Get distribution name.

        Returns:
            str: Distribution name
        """
        os_release = PlatformDetector.get_os_release_info()
        return os_release.get("NAME", "Unknown")

    @staticmethod
    def get_kernel_version() -> str:
        """Get kernel version.

        Returns:
            str: Kernel version string
        """
        try:
            result = subprocess.run(
                ["uname", "-r"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"

    @staticmethod
    def get_architecture() -> str:
        """Get system architecture.

        Returns:
            str: Architecture string (x86_64, aarch64, etc.)
        """
        try:
            result = subprocess.run(
                ["uname", "-m"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"

    @staticmethod
    def get_pam_config_paths(platform: Platform) -> tuple[Path, Path, Path]:
        """Get PAM configuration paths for platform.

        Args:
            platform: The platform

        Returns:
            tuple: (pam_conf_path, pam_d_path, system_lib_path)
        """
        if platform == Platform.FREEBSD:
            return (
                Path("/etc/pam.conf"),
                Path("/etc/pam.d"),
                Path("/usr/lib"),
            )

        # Linux systems typically use /etc/pam.d/
        return (
            Path("/etc/pam.conf"),
            Path("/etc/pam.d"),
            Path("/lib/x86_64-linux-gnu"),  # Debian-based
        )

    def detect_system(self) -> SystemInfo:
        """Detect complete system information.

        Returns:
            SystemInfo: Complete system information

        Raises:
            RuntimeError: If platform cannot be determined
        """
        if self._system_info is not None:
            return self._system_info

        platform = self.detect_platform()
        if platform == Platform.UNKNOWN:
            raise RuntimeError("Cannot detect platform")

        package_manager = self.detect_package_manager(platform)
        dist_name = self.get_distribution_name()
        dist_version = self.get_distribution_version()
        kernel_version = self.get_kernel_version()
        architecture = self.get_architecture()

        pam_conf_path, pam_d_path, sys_lib_path = self.get_pam_config_paths(
            platform
        )

        self._system_info = SystemInfo(
            platform=platform,
            distribution_name=dist_name,
            distribution_version=dist_version,
            kernel_version=kernel_version,
            architecture=architecture,
            package_manager=package_manager,
            pam_config_path=pam_conf_path,
            pam_d_path=pam_d_path,
            system_lib_path=sys_lib_path,
        )

        return self._system_info


__all__ = ["PlatformDetector"]
