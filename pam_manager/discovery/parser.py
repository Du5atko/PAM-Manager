"""PAM module discovery for system analysis."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from pam_manager.core import Platform


@dataclass(frozen=True)
class DiscoveredModule:
    """Information about a discovered PAM module on the system."""

    name: str  # Module name (e.g., "pam_unix")
    facility: str  # PAM facility (auth, account, password, session)
    control: str  # Control flag (required, requisite, sufficient, optional)
    service: str  # PAM service (sshd, login, sudo, etc.)
    path: Optional[str]  # Full path to module .so file if found
    arguments: List[str]  # Module arguments from PAM config
    config_file: str  # Source file (/etc/pam.d/*, /etc/pam.conf)
    line_number: int  # Line number in config file
    is_installed: bool  # True if .so file exists on system


@dataclass(frozen=True)
class DiscoveryReport:
    """Summary of PAM discovery on the system."""

    platform: Platform
    total_modules_discovered: int
    unique_modules: int
    modules_by_facility: Dict[str, int]
    modules_by_service: Dict[str, int]
    installed_pam_files: List[str]
    discovered_module_paths: List[str]
    missing_modules: List[str]  # Modules referenced but not found
    deprecated_modules: List[str]  # Deprecated modules in use
    all_discovered: List[DiscoveredModule]


class PamFileParser:
    """Parser for PAM configuration files."""

    @staticmethod
    def parse_pam_conf(file_path: Path) -> List[DiscoveredModule]:
        """Parse /etc/pam.conf (single file for all services).

        Format:
            service_name  facility  control  module_path  [arguments...]

        Args:
            file_path: Path to /etc/pam.conf

        Returns:
            List of DiscoveredModule entries
        """
        modules = []

        if not file_path.exists():
            return modules

        try:
            with open(file_path, "r") as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Parse line: service facility control module [args...]
                    parts = line.split()
                    if len(parts) < 4:
                        continue

                    service = parts[0]
                    facility = parts[1]
                    control = parts[2]
                    module_path = parts[3]
                    arguments = parts[4:] if len(parts) > 4 else []

                    # Extract module name from path
                    module_name = PamFileParser._extract_module_name(module_path)

                    # Check if module .so exists
                    is_installed = PamFileParser._check_module_installed(module_path)

                    modules.append(
                        DiscoveredModule(
                            name=module_name,
                            facility=facility,
                            control=control,
                            service=service,
                            path=module_path,
                            arguments=arguments,
                            config_file=str(file_path),
                            line_number=line_no,
                            is_installed=is_installed,
                        )
                    )
        except (IOError, OSError):
            pass

        return modules

    @staticmethod
    def parse_pam_d_files(pam_d_dir: Path) -> List[DiscoveredModule]:
        """Parse all files in /etc/pam.d directory.

        Each file defines PAM configuration for one service.
        Format (per line):
            facility  control  module_path  [arguments...]

        Args:
            pam_d_dir: Path to /etc/pam.d directory

        Returns:
            List of DiscoveredModule entries
        """
        modules = []

        if not pam_d_dir.is_dir():
            return modules

        try:
            for pam_file in pam_d_dir.iterdir():
                if pam_file.is_file() and not pam_file.name.startswith("."):
                    service_name = pam_file.name

                    try:
                        with open(pam_file, "r") as f:
                            for line_no, line in enumerate(f, 1):
                                line = line.strip()

                                # Skip comments, empty lines, and includes
                                if not line or line.startswith("#"):
                                    continue
                                if line.startswith("@include"):
                                    continue

                                # Parse line: facility control module [args...]
                                parts = line.split()
                                if len(parts) < 3:
                                    continue

                                facility = parts[0]
                                control = parts[1]
                                module_path = parts[2]
                                arguments = parts[3:] if len(parts) > 3 else []

                                # Extract module name
                                module_name = PamFileParser._extract_module_name(
                                    module_path
                                )

                                # Check if module exists
                                is_installed = PamFileParser._check_module_installed(
                                    module_path
                                )

                                modules.append(
                                    DiscoveredModule(
                                        name=module_name,
                                        facility=facility,
                                        control=control,
                                        service=service_name,
                                        path=module_path,
                                        arguments=arguments,
                                        config_file=str(pam_file),
                                        line_number=line_no,
                                        is_installed=is_installed,
                                    )
                                )
                    except (IOError, OSError):
                        continue
        except (IOError, OSError):
            pass

        return modules

    @staticmethod
    def _extract_module_name(module_path: str) -> str:
        """Extract module name from path.

        Examples:
            /lib/security/pam_unix.so -> pam_unix
            pam_unix.so -> pam_unix
            /usr/lib/x86_64-linux-gnu/security/pam_unix.so -> pam_unix

        Args:
            module_path: Full path or filename of module

        Returns:
            Module name without path and .so extension
        """
        # Get filename without directory
        filename = Path(module_path).name

        # Remove .so and any version suffixes
        if filename.endswith(".so"):
            return filename[:-3]

        # Handle .so.X or .so.X.Y.Z
        base = filename.split(".so")[0] if ".so" in filename else filename

        return base

    @staticmethod
    def _check_module_installed(module_path: str) -> bool:
        """Check if PAM module .so file exists.

        Tries multiple search paths if not absolute path:
        - /lib/security/
        - /usr/lib/security/
        - /usr/lib/x86_64-linux-gnu/security/
        - /lib64/security/
        - /usr/local/lib/security/
        - /usr/lib/freebsd/

        Args:
            module_path: Path to module file

        Returns:
            True if module file exists, False otherwise
        """
        # If absolute path, check directly
        if module_path.startswith("/"):
            return Path(module_path).exists()

        # Search common PAM module directories
        search_paths = [
            Path("/lib/security") / (module_path + ".so"),
            Path("/lib/security") / module_path,
            Path("/usr/lib/security") / (module_path + ".so"),
            Path("/usr/lib/security") / module_path,
            Path("/usr/lib/x86_64-linux-gnu/security") / (module_path + ".so"),
            Path("/usr/lib/x86_64-linux-gnu/security") / module_path,
            Path("/lib64/security") / (module_path + ".so"),
            Path("/lib64/security") / module_path,
            Path("/usr/local/lib/security") / (module_path + ".so"),
            Path("/usr/local/lib/security") / module_path,
            Path("/usr/lib/freebsd") / module_path,
        ]

        for path in search_paths:
            if path.exists():
                return True

        return False


__all__ = ["DiscoveredModule", "DiscoveryReport", "PamFileParser"]
