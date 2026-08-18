"""PAM module registry and lookup system."""

from typing import Dict, List, Optional, Set

from pam_manager.core import PAMFacility, Platform
from pam_manager.modules.base import PAMModuleInfo
from pam_manager.modules.database import PAM_MODULES


class ModuleRegistry:
    """Registry for PAM modules with filtering and dependency resolution."""

    def __init__(self) -> None:
        """Initialize module registry with JSON loader fallback."""
        # Try to load from JSON files, fall back to hardcoded database
        self._modules: Dict[str, PAMModuleInfo] = self._load_modules()
        self._resolved_dependencies: Dict[str, Set[str]] = {}
        self._resolved_conflicts: Dict[str, Set[str]] = {}
    
    def _load_modules(self) -> Dict[str, PAMModuleInfo]:
        """Load modules from JSON files with fallback to hardcoded database.
        
        Returns:
            Dictionary of module_name -> PAMModuleInfo
        """
        try:
            # Try to load from JSON files
            from pam_manager.modules.json_loader import get_modules_loader
            loader = get_modules_loader()
            if loader.load():
                modules = loader.get_modules()
                if modules:
                    # print(f"[INFO] Loaded {len(modules)} PAM modules from JSON files")
                    return modules
        except Exception as e:
            print(f"[WARNING] Failed to load modules from JSON: {e}")
        
        # Fall back to hardcoded database
        print("[INFO] Using hardcoded PAM modules database")
        return PAM_MODULES.copy()

    def get_module(self, name: str) -> Optional[PAMModuleInfo]:
        """Get module by name.

        Args:
            name: Module name (e.g., 'pam_unix')

        Returns:
            Module info or None if not found
        """
        return self._modules.get(name)

    def list_all_modules(self) -> List[str]:
        """List all available modules.

        Returns:
            List of module names
        """
        return sorted(self._modules.keys())

    def find_by_facility(self, facility: PAMFacility) -> List[str]:
        """Find modules that support a facility.

        Args:
            facility: PAM facility type

        Returns:
            List of module names
        """
        return [
            name
            for name, mod in self._modules.items()
            if mod.supports_facility(facility)
        ]

    def find_by_platform(self, platform: Platform) -> List[str]:
        """Find modules that support a platform.

        Args:
            platform: Platform type

        Returns:
            List of module names
        """
        return [
            name
            for name, mod in self._modules.items()
            if mod.supports_platform(platform)
        ]

    def find_by_facility_and_platform(
        self, facility: PAMFacility, platform: Platform
    ) -> List[str]:
        """Find modules that support both facility and platform.

        Args:
            facility: PAM facility type
            platform: Platform type

        Returns:
            List of module names
        """
        return [
            name
            for name, mod in self._modules.items()
            if mod.supports_facility(facility) and mod.supports_platform(platform)
        ]

    def find_by_category(self, category: str) -> List[str]:
        """Find modules by category.

        Args:
            category: Module category (authentication, account, password, session)

        Returns:
            List of module names
        """
        return [
            name for name, mod in self._modules.items() if mod.category == category
        ]

    def get_dependencies(self, module_name: str) -> Set[str]:
        """Get PAM module dependencies (not package dependencies).

        Args:
            module_name: Module name

        Returns:
            Set of dependent module names
        """
        mod = self.get_module(module_name)
        if not mod:
            return set()
        return mod.dependencies

    def get_conflicts(self, module_name: str) -> Set[str]:
        """Get modules that conflict with this module.

        Args:
            module_name: Module name

        Returns:
            Set of conflicting module names
        """
        mod = self.get_module(module_name)
        if not mod:
            return set()
        return mod.conflicts

    def resolve_all_dependencies(self, module_names: List[str]) -> Set[str]:
        """Resolve all dependencies for a list of modules.

        Args:
            module_names: List of module names

        Returns:
            Set of all required modules including dependencies

        Raises:
            ValueError: If module not found or circular dependency detected
        """
        resolved: Set[str] = set(module_names)
        to_process: List[str] = list(module_names)
        processed: Set[str] = set()
        max_iterations = 100
        iterations = 0

        while to_process and iterations < max_iterations:
            iterations += 1
            current = to_process.pop(0)

            if current in processed:
                continue

            mod = self.get_module(current)
            if not mod:
                raise ValueError(f"Module not found: {current}")

            processed.add(current)

            # Add dependencies
            for dep in mod.dependencies:
                if dep not in resolved:
                    resolved.add(dep)
                    if dep not in processed:
                        to_process.append(dep)

        if iterations >= max_iterations:
            raise ValueError("Circular dependency or too many iterations")

        return resolved

    def detect_conflicts(self, module_names: List[str]) -> Dict[str, Set[str]]:
        """Detect conflicts between modules.

        Args:
            module_names: List of module names to check

        Returns:
            Dictionary mapping module names to sets of conflicting modules
        """
        conflicts: Dict[str, Set[str]] = {}

        for mod_name in module_names:
            conflicts[mod_name] = set()
            mod = self.get_module(mod_name)
            if not mod:
                continue

            # Check explicit conflicts
            for conf_name in mod.conflicts:
                if conf_name in module_names:
                    conflicts[mod_name].add(conf_name)

            # Check for implicit conflicts (other modules that conflict with this)
            for other_name in module_names:
                if other_name != mod_name:
                    other_mod = self.get_module(other_name)
                    if other_mod and mod_name in other_mod.conflicts:
                        conflicts[mod_name].add(other_name)

        return conflicts

    def get_package_names(
        self, module_names: List[str], platform: Platform
    ) -> Dict[str, str]:
        """Get package names for modules on a specific platform.

        Args:
            module_names: List of module names
            platform: Platform type

        Returns:
            Dictionary mapping module names to package names
        """
        packages: Dict[str, str] = {}

        for mod_name in module_names:
            mod = self.get_module(mod_name)
            if mod:
                pkg_name = mod.get_package_name(platform)
                if pkg_name:
                    packages[mod_name] = pkg_name

        return packages

    def list_not_found(
        self, module_names: List[str], platform: Platform
    ) -> List[str]:
        """List modules without packages on a specific platform.

        Args:
            module_names: List of module names
            platform: Platform type

        Returns:
            List of module names with no package on platform
        """
        not_found = []

        for mod_name in module_names:
            mod = self.get_module(mod_name)
            if not mod or not mod.get_package_name(platform):
                not_found.append(mod_name)

        return not_found

    def get_recommended_ordering(self, module_names: List[str]) -> List[str]:
        """Get modules ordered by recommended stack ordering.

        Args:
            module_names: List of module names

        Returns:
            Ordered list of module names (early to late in stack)
        """
        modules_with_order = []

        for mod_name in module_names:
            mod = self.get_module(mod_name)
            if mod:
                modules_with_order.append((mod_name, mod.recommended_ordering))

        # Sort by ordering, then alphabetically for stable sort
        modules_with_order.sort(key=lambda x: (x[1], x[0]))
        return [name for name, _ in modules_with_order]

    def filter_deprecated(self, module_names: List[str]) -> List[str]:
        """Filter out deprecated modules.

        Args:
            module_names: List of module names

        Returns:
            List of non-deprecated module names
        """
        return [
            name
            for name in module_names
            if not self.get_module(name) or not self.get_module(name).deprecated
        ]

    def find_alternatives(
        self, module_name: str, facility: Optional[PAMFacility] = None
    ) -> List[str]:
        """Find alternative modules with similar functionality.

        Args:
            module_name: Module name
            facility: Optional facility to filter by

        Returns:
            List of alternative module names
        """
        mod = self.get_module(module_name)
        if not mod:
            return []

        # Find modules in same category with same facility support
        alternatives = []
        for name, other_mod in self._modules.items():
            if name == module_name:
                continue
            if other_mod.category == mod.category:
                if facility is None or other_mod.supports_facility(facility):
                    alternatives.append(name)

        return alternatives


__all__ = ["ModuleRegistry"]
