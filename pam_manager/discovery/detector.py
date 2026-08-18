"""PAM module discovery detector for system scanning."""

from pathlib import Path
from typing import Dict, List, Set

from pam_manager.core import Platform
from pam_manager.discovery.parser import DiscoveredModule, DiscoveryReport, PamFileParser
from pam_manager.modules import ModuleRegistry
from pam_manager.platform.detector import PlatformDetector


class DiscoveryDetector:
    """Detector for discovering installed PAM modules on the system."""

    def __init__(self, platform: Platform = None) -> None:
        """Initialize discovery detector.

        Args:
            platform: Target platform (defaults to current system)
        """
        if platform is None:
            self.platform = PlatformDetector.detect_platform()
        else:
            self.platform = platform

        # Get PAM config paths for the platform
        pam_conf_path, pam_d_path, sys_lib_path = PlatformDetector.get_pam_config_paths(
            self.platform
        )
        self.pam_conf_path = pam_conf_path
        self.pam_d_path = pam_d_path
        self.system_lib_path = sys_lib_path

        self.registry = ModuleRegistry()

    def discover_modules(self) -> DiscoveryReport:
        """Discover all PAM modules currently installed on the system.

        Scans:
        1. /etc/pam.d directory (Linux systems)
        2. /etc/pam.conf (all systems)

        Returns:
            DiscoveryReport with discovered modules and analysis
        """
        discovered_modules: List[DiscoveredModule] = []

        # Parse /etc/pam.d directory if it exists
        if self.pam_d_path.exists():
            discovered_modules.extend(PamFileParser.parse_pam_d_files(self.pam_d_path))

        # Parse /etc/pam.conf if it exists
        if self.pam_conf_path.exists():
            discovered_modules.extend(PamFileParser.parse_pam_conf(self.pam_conf_path))

        # Analyze discovered modules
        analysis = self._analyze_modules(discovered_modules)

        return DiscoveryReport(
            platform=self.platform,
            total_modules_discovered=len(discovered_modules),
            unique_modules=len(set(m.name for m in discovered_modules)),
            modules_by_facility=analysis["by_facility"],
            modules_by_service=analysis["by_service"],
            installed_pam_files=analysis["pam_files"],
            discovered_module_paths=analysis["module_paths"],
            missing_modules=analysis["missing"],
            deprecated_modules=analysis["deprecated"],
            all_discovered=discovered_modules,
        )

    def _analyze_modules(
        self, modules: List[DiscoveredModule]
    ) -> Dict:
        """Analyze discovered modules.

        Args:
            modules: List of discovered modules

        Returns:
            Dictionary with analysis results
        """
        by_facility: Dict[str, int] = {}
        by_service: Dict[str, int] = {}
        module_paths: Set[str] = set()
        pam_files: Set[str] = set()
        missing: List[str] = []
        deprecated: List[str] = []

        for module in modules:
            # Count by facility
            by_facility[module.facility] = by_facility.get(module.facility, 0) + 1

            # Count by service
            by_service[module.service] = by_service.get(module.service, 0) + 1

            # Collect module paths
            if module.path:
                module_paths.add(module.path)

            # Collect config files
            pam_files.add(module.config_file)

            # Check if module is in database
            db_module = self.registry.get_module(module.name)
            if db_module is None:
                missing.append(module.name)
            elif db_module.deprecated:
                deprecated.append(module.name)

        return {
            "by_facility": by_facility,
            "by_service": by_service,
            "module_paths": sorted(list(module_paths)),
            "pam_files": sorted(list(pam_files)),
            "missing": list(set(missing)),  # Remove duplicates
            "deprecated": list(set(deprecated)),
        }

    def compare_with_database(self) -> Dict:
        """Compare discovered modules with module database.

        Returns:
            Dictionary with comparison results:
            - installed: List of discovered modules in database
            - missing: List of modules referenced but not in database
            - not_in_use: List of database modules not found on system
            - coverage: Percentage of database modules in use
        """
        report = self.discover_modules()
        discovered_names = set(m.name for m in report.all_discovered)
        
        # Get all module names from database
        database_names = set(self.registry.list_all_modules())

        installed = discovered_names & database_names
        missing = discovered_names - database_names
        not_in_use = database_names - discovered_names

        coverage = (
            len(installed) / len(database_names) * 100
            if database_names
            else 0
        )

        return {
            "installed": sorted(list(installed)),
            "missing": sorted(list(missing)),
            "not_in_use": sorted(list(not_in_use)),
            "coverage": coverage,
            "installed_count": len(installed),
            "database_count": len(database_names),
        }

    def get_module_by_service(self, service_name: str) -> List[DiscoveredModule]:
        """Get all modules configured for specific service.

        Args:
            service_name: PAM service name (e.g., "sshd", "login", "sudo")

        Returns:
            List of modules for that service
        """
        report = self.discover_modules()
        return [m for m in report.all_discovered if m.service == service_name]

    def get_module_by_facility(self, facility: str) -> List[DiscoveredModule]:
        """Get all modules for specific facility.

        Args:
            facility: PAM facility (auth, account, password, session)

        Returns:
            List of modules for that facility
        """
        report = self.discover_modules()
        return [m for m in report.all_discovered if m.facility == facility]

    def get_module_by_name(self, module_name: str) -> List[DiscoveredModule]:
        """Get all discovered instances of a specific module.

        Args:
            module_name: Name of module (e.g., "pam_unix")

        Returns:
            List of module instances (may appear in multiple services)
        """
        report = self.discover_modules()
        return [m for m in report.all_discovered if m.name == module_name]

    def get_security_recommendations(self) -> Dict:
        """Generate security recommendations based on discovered modules.

        Returns:
            Dictionary with recommendations
        """
        report = self.discover_modules()
        comparison = self.compare_with_database()
        recommendations = []

        # Check for deprecated modules
        if report.deprecated_modules:
            recommendations.append(
                f"WARNING: Found deprecated modules in use: {', '.join(report.deprecated_modules)}"
            )

        # Check for missing module database entries
        if report.missing_modules:
            recommendations.append(
                f"INFO: Found {len(report.missing_modules)} modules not in database"
            )

        # Check if pam_unix is configured (basic authentication)
        pam_unix_modules = self.get_module_by_name("pam_unix")
        if not pam_unix_modules:
            recommendations.append(
                "SECURITY: pam_unix not configured (needed for basic authentication)"
            )

        # Check password quality configuration
        pam_pwquality = self.get_module_by_name("pam_pwquality")
        if not pam_pwquality:
            recommendations.append(
                "SECURITY: pam_pwquality not configured (password quality enforcement recommended)"
            )

        # Check account lockout configuration
        lockout_modules = (
            self.get_module_by_name("pam_faillock")
            + self.get_module_by_name("pam_tally2")
        )
        if not lockout_modules:
            recommendations.append(
                "SECURITY: Account lockout not configured (pam_faillock or pam_tally2 recommended)"
            )

        # Database coverage
        coverage = comparison["coverage"]
        recommendations.append(f"INFO: Database coverage: {coverage:.1f}%")

        return {
            "recommendations": recommendations,
            "deprecated_in_use": report.deprecated_modules,
            "missing_from_database": report.missing_modules,
            "database_coverage": coverage,
        }


__all__ = ["DiscoveryDetector"]
