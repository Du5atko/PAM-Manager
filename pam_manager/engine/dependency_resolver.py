"""PAM module dependency resolution."""

from typing import Dict, List, Set

from pam_manager.modules import ModuleRegistry


class DependencyResolver:
    """Resolve PAM module dependencies and generate installation order."""

    def __init__(self, registry: ModuleRegistry = None) -> None:
        """Initialize resolver with module registry.

        Args:
            registry: ModuleRegistry (defaults to new instance)
        """
        self.registry = registry or ModuleRegistry()
        self._resolved_cache: Dict[str, List[str]] = {}
        self._visiting: Set[str] = set()  # For cycle detection

    def get_dependencies(self, module_name: str) -> List[str]:
        """Get all dependencies for a module (direct only).

        Args:
            module_name: Name of module

        Returns:
            List of module names this module depends on
        """
        deps = self.registry.get_dependencies(module_name)
        return sorted(list(deps)) if deps else []

    def resolve_all_dependencies(self, module_names: List[str]) -> List[str]:
        """Resolve all dependencies for a list of modules recursively.

        Returns modules in correct installation order (dependencies first).
        Handles circular dependencies by detecting cycles.

        Args:
            module_names: List of module names to resolve

        Returns:
            List of modules in installation order
        """
        self._resolved_cache = {}
        self._visiting = set()
        resolved = []
        seen = set()

        for module_name in module_names:
            self._resolve_recursive(module_name, resolved, seen)

        return resolved

    def _resolve_recursive(
        self, module_name: str, resolved: List[str], seen: Set[str]
    ) -> None:
        """Recursively resolve dependencies.

        Args:
            module_name: Module to resolve
            resolved: List to accumulate resolved modules
            seen: Set of already processed modules
        """
        if module_name in seen:
            return

        if module_name in self._visiting:
            # Circular dependency detected - skip
            return

        self._visiting.add(module_name)

        # Get dependencies for this module
        deps = self.get_dependencies(module_name)

        # Resolve dependencies first (depth-first)
        for dep in deps:
            self._resolve_recursive(dep, resolved, seen)

        self._visiting.discard(module_name)

        # Add this module if not already processed
        if module_name not in seen:
            resolved.append(module_name)
            seen.add(module_name)

    def get_dependency_chain(self, module_name: str) -> Dict[str, List[str]]:
        """Get complete dependency chain for visualization.

        Args:
            module_name: Module name

        Returns:
            Dictionary showing module -> dependencies mapping
        """
        chain = {}
        visited = set()

        def build_chain(name: str) -> None:
            if name in visited:
                return
            visited.add(name)

            deps = self.get_dependencies(name)
            chain[name] = deps

            for dep in deps:
                build_chain(dep)

        build_chain(module_name)
        return chain

    def get_reverse_dependencies(self, module_name: str) -> List[str]:
        """Get modules that depend on this module.

        Args:
            module_name: Module name

        Returns:
            List of modules that depend on this one
        """
        all_modules = self.registry.list_all_modules()
        dependents = []

        for mod in all_modules:
            deps = self.get_dependencies(mod)
            if module_name in deps:
                dependents.append(mod)

        return dependents

    def get_installation_order(self, module_names: List[str]) -> List[str]:
        """Get optimal installation order for modules.

        Places dependencies before dependents.

        Args:
            module_names: List of module names

        Returns:
            Module names in optimal installation order
        """
        return self.resolve_all_dependencies(module_names)

    def validate_dependencies(self, module_names: List[str]) -> Dict:
        """Validate that all dependencies are satisfied.

        Args:
            module_names: List of module names

        Returns:
            Dictionary with validation results
        """
        resolved = self.resolve_all_dependencies(module_names)
        all_required = set(resolved)
        provided = set(module_names)
        missing = all_required - provided

        return {
            "valid": len(missing) == 0,
            "required_modules": sorted(list(all_required)),
            "missing_dependencies": sorted(list(missing)),
            "installation_order": resolved,
        }

    def suggest_additional_modules(self, module_names: List[str]) -> List[str]:
        """Suggest modules that might be useful with the selected ones.

        Args:
            module_names: List of selected module names

        Returns:
            List of suggested module names
        """
        suggestions = set()

        for module_name in module_names:
            # If pam_unix is selected, suggest pam_permit
            if module_name == "pam_unix":
                suggestions.add("pam_permit")

            # If auth module, suggest complementary modules
            module = self.registry.get_module(module_name)
            if module:
                # Suggest account modules if only auth selected
                if module.supported_facilities and "auth" in module.supported_facilities:
                    # Look for account modules
                    account_modules = self.registry.find_by_facility("account")
                    if account_modules:
                        suggestions.add(account_modules[0].name)

        # Remove already selected
        suggestions -= set(module_names)

        return sorted(list(suggestions))


__all__ = ["DependencyResolver"]
