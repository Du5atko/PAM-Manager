"""PAM module conflict detection."""

from dataclasses import dataclass
from typing import Dict, List

from pam_manager.modules import ModuleRegistry


@dataclass(frozen=True)
class ModuleConflict:
    """Information about a conflict between modules."""

    module1: str  # First conflicting module
    module2: str  # Second conflicting module
    reason: str  # Reason for conflict
    severity: str  # "high", "medium", "low"
    recommendation: str  # How to resolve


class ConflictDetector:
    """Detect conflicts between PAM modules."""

    def __init__(self, registry: ModuleRegistry = None) -> None:
        """Initialize conflict detector.

        Args:
            registry: ModuleRegistry (defaults to new instance)
        """
        self.registry = registry or ModuleRegistry()

    def detect_conflicts(self, module_names: List[str]) -> List[ModuleConflict]:
        """Detect all conflicts between modules.

        Args:
            module_names: List of module names to check

        Returns:
            List of ModuleConflict objects
        """
        conflicts = []

        # Check direct conflicts from module metadata
        for i, mod1 in enumerate(module_names):
            for mod2 in module_names[i + 1 :]:
                conflict = self._check_conflict(mod1, mod2)
                if conflict:
                    conflicts.append(conflict)

        # Check facility conflicts (multiple exclusive modules in same facility)
        conflicts.extend(self._check_facility_conflicts(module_names))

        return conflicts

    def _check_conflict(self, module1: str, module2: str) -> ModuleConflict:
        """Check if two modules conflict.

        Args:
            module1: First module name
            module2: Second module name

        Returns:
            ModuleConflict if they conflict, None otherwise
        """
        mod1_obj = self.registry.get_module(module1)
        mod2_obj = self.registry.get_module(module2)

        if not mod1_obj or not mod2_obj:
            return None

        # Check if they have declared conflicts
        mod1_conflicts = mod1_obj.conflicts or []
        mod2_conflicts = mod2_obj.conflicts or []

        if module2 in mod1_conflicts or module1 in mod2_conflicts:
            return ModuleConflict(
                module1=module1,
                module2=module2,
                reason=f"{module1} and {module2} have declared conflict",
                severity="high",
                recommendation=f"Choose either {module1} or {module2}",
            )

        # Check for alternative modules (cannot use both)
        alternatives = self._get_alternative_groups()
        for alt_group in alternatives:
            if module1 in alt_group and module2 in alt_group:
                others = [m for m in alt_group if m not in [module1, module2]]
                return ModuleConflict(
                    module1=module1,
                    module2=module2,
                    reason=f"Both {module1} and {module2} are alternatives",
                    severity="high",
                    recommendation=f"Select only one alternative module. Options: {alt_group}",
                )

        return None

    def _check_facility_conflicts(self, module_names: List[str]) -> List[ModuleConflict]:
        """Check for facility-level conflicts.

        Some module combinations create issues in same facility.

        Args:
            module_names: List of module names

        Returns:
            List of facility conflicts
        """
        conflicts = []

        # Group modules by facility
        by_facility: Dict[str, List[str]] = {}
        for module_name in module_names:
            module = self.registry.get_module(module_name)
            if module and module.supported_facilities:
                for facility in module.supported_facilities:
                    if facility not in by_facility:
                        by_facility[facility] = []
                    by_facility[facility].append(module_name)

        # Check for problematic combinations
        for facility, modules in by_facility.items():
            if len(modules) > 1:
                # Multiple auth modules - usually OK
                if facility == "auth" and len(modules) <= 3:
                    continue

                # Multiple account modules - might be OK
                if facility == "account" and len(modules) <= 2:
                    continue

                # Multiple session modules - might conflict
                if facility == "session" and len(modules) > 2:
                    conflicts.append(
                        ModuleConflict(
                            module1=modules[0],
                            module2=modules[1],
                            reason=f"Multiple session modules in {facility}: {modules}",
                            severity="medium",
                            recommendation="Review session module interaction",
                        )
                    )

        return conflicts

    def _get_alternative_groups(self) -> List[List[str]]:
        """Get groups of alternative modules.

        Returns:
            List of alternative module groups
        """
        return [
            ["pam_unix", "pam_ldap", "pam_krb5", "pam_sss"],  # Auth sources
            ["pam_faillock", "pam_tally2"],  # Account lockout
            ["pam_pwquality", "pam_cracklib"],  # Password quality
            ["pam_google_authenticator", "pam_oath", "pam_u2f"],  # 2FA
        ]

    def get_conflicting_pairs(self, module_names: List[str]) -> List[tuple]:
        """Get list of conflicting module pairs.

        Args:
            module_names: List of module names

        Returns:
            List of (module1, module2) tuples that conflict
        """
        conflicts = self.detect_conflicts(module_names)
        return [(c.module1, c.module2) for c in conflicts]

    def has_conflicts(self, module_names: List[str]) -> bool:
        """Check if module list has any conflicts.

        Args:
            module_names: List of module names

        Returns:
            True if conflicts found, False otherwise
        """
        return len(self.detect_conflicts(module_names)) > 0

    def resolve_conflict(self, conflict: ModuleConflict) -> str:
        """Get recommendation for resolving a conflict.

        Args:
            conflict: ModuleConflict object

        Returns:
            Recommendation string
        """
        return conflict.recommendation

    def find_compatible_alternative(
        self, module_name: str, other_modules: List[str]
    ) -> str:
        """Find compatible alternative to a module.

        Args:
            module_name: Module that conflicts
            other_modules: Other selected modules

        Returns:
            Alternative module name or None
        """
        alternatives = self._get_alternative_groups()

        for alt_group in alternatives:
            if module_name in alt_group:
                # Find alternative not in other_modules
                for alt in alt_group:
                    if alt not in other_modules:
                        return alt

        # If no alternative found, try similar modules
        similar = self.registry.find_alternatives(module_name)
        for sim in similar:
            if sim not in other_modules:
                return sim

        return None


__all__ = ["ModuleConflict", "ConflictDetector"]
