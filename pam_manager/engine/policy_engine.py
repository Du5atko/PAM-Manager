"""PAM Policy Engine - Orchestrates policy validation and module management."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from pam_manager.core import Platform
from pam_manager.discovery import DiscoveryDetector, DiscoveryReport
from pam_manager.engine.conflict_detector import ConflictDetector, ModuleConflict
from pam_manager.engine.dependency_resolver import DependencyResolver
from pam_manager.modules import ModuleRegistry
from pam_manager.policy import PolicyModel


@dataclass(frozen=True)
class PolicyValidationResult:
    """Result of policy validation."""

    valid: bool  # True if policy is valid
    module_list: List[str]  # Validated module list in order
    required_modules: List[str]  # All required modules (including dependencies)
    conflicts: List[ModuleConflict]  # Detected conflicts
    missing_dependencies: List[str]  # Unresolved dependencies
    warnings: List[str]  # Non-critical issues
    recommendations: List[str]  # Suggested improvements
    installation_order: List[str]  # Recommended installation order


class PolicyEngine:
    """PAM Policy Engine - validates and manages PAM module configurations."""

    def __init__(self, platform: Platform = None) -> None:
        """Initialize policy engine.

        Args:
            platform: Target platform (defaults to current system)
        """
        self.registry = ModuleRegistry()
        self.dependency_resolver = DependencyResolver(self.registry)
        self.conflict_detector = ConflictDetector(self.registry)
        self.discovery_detector = DiscoveryDetector(platform)
        self.platform = platform or self.discovery_detector.platform

    def validate_policy(self, module_names: List[str]) -> PolicyValidationResult:
        """Validate a policy (module list).

        Checks:
        - All modules exist in database
        - All dependencies resolved
        - No conflicts between modules
        - Covers required facilities

        Args:
            module_names: List of module names to validate

        Returns:
            PolicyValidationResult with validation details
        """
        warnings = []
        recommendations = []

        # Resolve dependencies
        resolved = self.dependency_resolver.resolve_all_dependencies(module_names)
        required = set(resolved)
        missing_deps = []

        # Check for invalid module names
        invalid_modules = []
        for mod in module_names:
            if self.registry.get_module(mod) is None:
                invalid_modules.append(mod)

        if invalid_modules:
            recommendations.append(
                f"Unknown modules: {invalid_modules} (not in database)"
            )

        # Check for missing dependencies
        for dep_name in resolved:
            if self.registry.get_module(dep_name) is None:
                missing_deps.append(dep_name)

        # Detect conflicts
        conflicts = self.conflict_detector.detect_conflicts(resolved)

        # Check facility coverage
        covered_facilities = self._get_covered_facilities(resolved)
        required_facilities = ["auth", "account", "password", "session"]
        missing_facilities = [f for f in required_facilities if f not in covered_facilities]

        if missing_facilities:
            warnings.append(f"Missing facilities: {missing_facilities}")

        # Get recommendations
        recommendations.extend(
            self._generate_recommendations(resolved, covered_facilities, conflicts)
        )

        # Determine validity
        is_valid = (
            len(invalid_modules) == 0
            and len(missing_deps) == 0
            and len(conflicts) == 0
        )

        return PolicyValidationResult(
            valid=is_valid,
            module_list=module_names,
            required_modules=resolved,
            conflicts=conflicts,
            missing_dependencies=missing_deps,
            warnings=warnings,
            recommendations=recommendations,
            installation_order=resolved,
        )

    def _get_covered_facilities(self, modules: List[str]) -> set:
        """Get facilities covered by modules.

        Args:
            modules: List of module names

        Returns:
            Set of covered facilities
        """
        covered = set()
        for module_name in modules:
            module = self.registry.get_module(module_name)
            if module and module.supported_facilities:
                covered.update(module.supported_facilities)
        return covered

    def _generate_recommendations(
        self, modules: List[str], facilities: set, conflicts: List[ModuleConflict]
    ) -> List[str]:
        """Generate recommendations for improvements.

        Args:
            modules: List of modules
            facilities: Set of covered facilities
            conflicts: List of detected conflicts

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check for security best practices
        has_auth = any(m.startswith("pam_") for m in modules)
        if "pam_unix" not in modules and has_auth:
            recommendations.append("Consider adding pam_unix for basic authentication")

        # Check for password quality
        if "password" in facilities and "pam_pwquality" not in modules:
            recommendations.append(
                "Consider pam_pwquality for password quality enforcement"
            )

        # Check for account lockout
        if "account" in facilities:
            lockout_modules = [m for m in modules if "faillock" in m or "tally" in m]
            if not lockout_modules:
                recommendations.append(
                    "Consider pam_faillock for account lockout protection"
                )

        # Conflict resolutions
        for conflict in conflicts:
            if conflict.severity == "high":
                recommendations.append(f"CRITICAL: {conflict.recommendation}")

        return recommendations

    def suggest_policy(
        self, authentication_level: str = "standard"
    ) -> List[str]:
        """Suggest a policy based on security level.

        Args:
            authentication_level: "basic", "standard", "strong", "maximum"

        Returns:
            List of suggested module names
        """
        policies = {
            "basic": ["pam_unix", "pam_permit"],
            "standard": [
                "pam_unix",
                "pam_pwquality",
                "pam_faillock",
                "pam_limits",
                "pam_systemd",
            ],
            "strong": [
                "pam_unix",
                "pam_pwquality",
                "pam_faillock",
                "pam_google_authenticator",
                "pam_limits",
                "pam_apparmor",
                "pam_systemd",
            ],
            "maximum": [
                "pam_unix",
                "pam_pwquality",
                "pam_faillock",
                "pam_google_authenticator",
                "pam_limits",
                "pam_apparmor",
                "pam_selinux",
                "pam_systemd",
            ],
        }

        suggested = policies.get(authentication_level, policies["standard"])

        # Filter for available modules
        available = [m for m in suggested if self.registry.get_module(m) is not None]

        return available

    def compare_with_system(self) -> Dict:
        """Compare policy against current system configuration.

        Returns:
            Dictionary with comparison results
        """
        discovery = self.discovery_detector.discover_modules()

        discovered_names = set(m.name for m in discovery.all_discovered)
        database_names = set(self.registry.list_all_modules())

        installed = discovered_names & database_names
        unknown = discovered_names - database_names
        not_in_use = database_names - discovered_names

        return {
            "current_system_modules": sorted(list(discovered_names)),
            "database_modules": sorted(list(database_names)),
            "installed_known": sorted(list(installed)),
            "unknown_modules": sorted(list(unknown)),
            "available_not_used": sorted(list(not_in_use))[:20],
            "coverage": len(installed) / len(database_names) * 100 if database_names else 0,
        }

    def get_module_info(self, module_name: str) -> Dict:
        """Get detailed information about a module.

        Args:
            module_name: Module name

        Returns:
            Dictionary with module information
        """
        module = self.registry.get_module(module_name)
        if not module:
            return {"found": False, "name": module_name}

        return {
            "found": True,
            "name": module.name,
            "description": module.description,
            "detailed_description": module.detailed_description,
            "category": module.category,
            "facilities": list(module.supported_facilities),
            "platforms": [p.name for p in module.supported_platforms],
            "dependencies": list(module.dependencies) if module.dependencies else [],
            "conflicts": list(module.conflicts) if module.conflicts else [],
            "package_debian": module.package_name_debian,
            "package_rhel": module.package_name_rhel,
            "package_freebsd": module.package_name_freebsd,
            "deprecated": module.deprecated,
            "security_impact": module.security_impact,
        }

    def resolve_conflicts(
        self, module_names: List[str]
    ) -> tuple:
        """Try to resolve conflicts by removing conflicting modules.

        Args:
            module_names: List of module names with potential conflicts

        Returns:
            Tuple of (resolved_list, removed_modules, recommendations)
        """
        conflicts = self.conflict_detector.detect_conflicts(module_names)

        if not conflicts:
            return (module_names, [], [])

        resolved = list(module_names)
        removed = []
        recommendations = []

        for conflict in conflicts:
            if conflict.severity == "high":
                # Try to resolve by keeping the first and removing the second
                if conflict.module2 in resolved:
                    resolved.remove(conflict.module2)
                    removed.append(conflict.module2)
                    recommendations.append(
                        f"Removed {conflict.module2} (conflicts with {conflict.module1})"
                    )

        return (resolved, removed, recommendations)


__all__ = ["PolicyEngine", "PolicyValidationResult"]
