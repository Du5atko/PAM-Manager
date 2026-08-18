"""PAM Configuration Wizard - Interactive CLI for policy management."""

from typing import Dict, List, Optional, Tuple

from pam_manager.core import Platform
from pam_manager.discovery import DiscoveryDetector, DiscoveryReport
from pam_manager.engine import PolicyEngine, PolicyValidationResult
from pam_manager.modules import ModuleRegistry
from pam_manager.policy import PolicyModel


class WizardState:
    """Maintains wizard session state."""

    def __init__(self) -> None:
        """Initialize wizard state."""
        self.selected_modules: List[str] = []
        self.security_level: str = "standard"
        self.platform: Platform = Platform.UBUNTU
        self.validation_result: Optional[PolicyValidationResult] = None
        self.discovered_modules: Optional[DiscoveryReport] = None

    def reset(self) -> None:
        """Reset wizard state."""
        self.selected_modules = []
        self.security_level = "standard"
        self.validation_result = None
        self.discovered_modules = None


class TextWizard:
    """Interactive text-based PAM configuration wizard."""

    def __init__(self, platform: Platform = None) -> None:
        """Initialize wizard.

        Args:
            platform: Target platform (auto-detects if None)
        """
        self.state = WizardState()
        self.engine = PolicyEngine(platform)
        self.registry = ModuleRegistry()
        self.discovery = DiscoveryDetector(platform)
        self.platform = platform or self.discovery.platform
        self.state.platform = self.platform

    def run(self) -> None:
        """Run interactive wizard."""
        self._print_header()

        while True:
            action = self._show_main_menu()

            if action == "1":
                self._scan_system()
            elif action == "2":
                self._quick_policy()
            elif action == "3":
                self._custom_policy()
            elif action == "4":
                self._manage_policy()
            elif action == "5":
                self._show_database()
            elif action == "6":
                self._manage_fragments()
            elif action == "7":
                self._manage_elements()
            elif action == "8":
                self._exit()
            else:
                self._print_error("Invalid option. Please try again.")

    def _print_header(self) -> None:
        """Print wizard header."""
        print("\n" + "=" * 60)
        print("  PAM CONFIGURATION WIZARD".center(60))
        print("=" * 60)
        print(f"Platform: {self.platform.name}")
        print()

    def _show_main_menu(self) -> str:
        """Show main menu and get user choice.

        Returns:
            User's menu choice
        """
        import sys
        
        print("\nMain Menu:")
        print("  1) Scan System PAM Configuration")
        print("  2) Quick Policy Setup")
        print("  3) Custom Policy Builder")
        print("  4) Manage Current Policy")
        print("  5) Browse Module Database")
        print("  6) Manage Policy Fragments")
        print("  7) Manage Policy Elements")
        print("  8) Exit")
        print()

        # Flush output to ensure prompt is visible
        sys.stdout.flush()
        
        try:
            return input("Select option (1-8): ").strip()
        except (EOFError, KeyboardInterrupt):
            raise

    def _scan_system(self) -> None:
        """Scan and display current system PAM configuration."""
        print("\n" + "-" * 60)
        print("SCANNING SYSTEM PAM CONFIGURATION")
        print("-" * 60)

        try:
            report = self.discovery.discover_modules()
            self.state.discovered_modules = report

            print(f"\nPlatform: {report.platform.name}")
            print(f"Total Modules Discovered: {report.total_modules_discovered}")
            print(f"Unique Modules: {report.unique_modules}")

            print("\nModules by Facility:")
            for facility, count in report.modules_by_facility.items():
                facility_modules = [m.name for m in report.all_discovered if m.facility == facility]
                unique_names = list(set(facility_modules))[:5]
                print(f"  {facility}: {', '.join(unique_names)}")
                if count > 5:
                    print(f"    ... and {count - 5} more")

            print(f"\nInstalled PAM Files: {len(report.installed_pam_files)}")
            for pam_file in report.installed_pam_files[:5]:
                print(f"  - {pam_file}")
            if len(report.installed_pam_files) > 5:
                print(f"  ... and {len(report.installed_pam_files) - 5} more")

            # Show recommendations
            recommendations = self.discovery.get_security_recommendations()
            if recommendations.get("deprecated_modules"):
                print("\n⚠️ Deprecated modules in use:")
                for mod in recommendations["deprecated_modules"]:
                    print(f"  - {mod}")

        except Exception as e:
            self._print_error(f"Failed to scan system: {e}")

    def _quick_policy(self) -> None:
        """Quick policy setup with predefined templates."""
        print("\n" + "-" * 60)
        print("QUICK POLICY SETUP")
        print("-" * 60)

        print("\nSecurity Level:")
        print("  1) Basic (Minimal - pam_unix only)")
        print("  2) Standard (Recommended - password quality + lockout)")
        print("  3) Strong (Enhanced - 2FA + SELinux/AppArmor)")
        print("  4) Maximum (Strict - All security features)")
        print()

        level_choice = input("Select security level (1-4): ").strip()
        level_map = {"1": "basic", "2": "standard", "3": "strong", "4": "maximum"}

        if level_choice not in level_map:
            self._print_error("Invalid security level")
            return

        security_level = level_map[level_choice]
        suggested = self.engine.suggest_policy(security_level)

        self.state.security_level = security_level
        self.state.selected_modules = suggested

        print(f"\nSuggested modules for '{security_level}' level:")
        for i, module in enumerate(suggested, 1):
            info = self.engine.get_module_info(module)
            desc = info.get("description", "")[:50]
            print(f"  {i}) {module}: {desc}")

        confirm = input("\nApply this policy? (y/n): ").strip().lower()
        if confirm == "y":
            self._validate_and_show_policy(suggested)

    def _custom_policy(self) -> None:
        """Build custom policy with module selection."""
        print("\n" + "-" * 60)
        print("CUSTOM POLICY BUILDER")
        print("-" * 60)

        modules = []

        while True:
            print(f"\nCurrent modules: {modules if modules else 'None selected'}")
            print("\nOptions:")
            print("  1) Add module")
            print("  2) Remove module")
            print("  3) View recommendations")
            print("  4) Validate policy")
            print("  5) Back to main menu")
            print()

            choice = input("Select option (1-5): ").strip()

            if choice == "1":
                modules = self._add_module_interactive(modules)
            elif choice == "2":
                modules = self._remove_module_interactive(modules)
            elif choice == "3":
                self._show_recommendations(modules)
            elif choice == "4":
                self._validate_and_show_policy(modules)
            elif choice == "5":
                break
            else:
                self._print_error("Invalid option")

    def _add_module_interactive(self, modules: List[str]) -> List[str]:
        """Interactive module addition."""
        print("\nAvailable modules (by facility):")

        all_modules = self.registry.list_all_modules()
        for i, module_name in enumerate(all_modules, 1):
            if module_name not in modules:
                info = self.engine.get_module_info(module_name)
                if info.get("found"):
                    print(f"  {i}) {module_name}: {info.get('description', '')[:40]}")

        try:
            choice = int(input("\nEnter module number (or 0 to cancel): ").strip())
            if choice == 0:
                return modules
            if 1 <= choice <= len(all_modules):
                module = all_modules[choice - 1]
                if module not in modules:
                    modules.append(module)
                    print(f"✓ Added {module}")
                else:
                    print(f"✗ {module} already selected")
        except ValueError:
            self._print_error("Invalid input")

        return modules

    def _remove_module_interactive(self, modules: List[str]) -> List[str]:
        """Interactive module removal."""
        if not modules:
            print("No modules selected")
            return modules

        print("\nSelected modules:")
        for i, module in enumerate(modules, 1):
            print(f"  {i}) {module}")

        try:
            choice = int(input("\nEnter number to remove (or 0 to cancel): ").strip())
            if choice == 0:
                return modules
            if 1 <= choice <= len(modules):
                removed = modules.pop(choice - 1)
                print(f"✓ Removed {removed}")
        except ValueError:
            self._print_error("Invalid input")

        return modules

    def _show_recommendations(self, modules: List[str]) -> None:
        """Show recommendations for current module selection."""
        if not modules:
            print("No modules selected")
            return

        validation = self.engine.validate_policy(modules)

        print("\nRecommendations:")
        for rec in validation.recommendations:
            print(f"  • {rec}")

        if not validation.recommendations:
            print("  ✓ No recommendations - policy looks good")

        if validation.conflicts:
            print("\n⚠️ Conflicts detected:")
            for conflict in validation.conflicts:
                print(f"  • {conflict.module1} vs {conflict.module2}: {conflict.reason}")

    def _validate_and_show_policy(self, modules: List[str]) -> None:
        """Validate policy and show results."""
        if not modules:
            self._print_error("No modules selected")
            return

        print("\n" + "-" * 60)
        print("VALIDATING POLICY")
        print("-" * 60)

        validation = self.engine.validate_policy(modules)
        self.state.validation_result = validation

        print(f"\n✓ Validation: {'PASSED' if validation.valid else 'FAILED'}")
        print(f"Module List: {', '.join(validation.module_list)}")
        print(f"Required (with deps): {', '.join(validation.required_modules)}")

        if validation.missing_dependencies:
            print(f"\n⚠️ Missing Dependencies: {validation.missing_dependencies}")

        if validation.conflicts:
            print(f"\n⚠️ Conflicts ({len(validation.conflicts)}):")
            for conflict in validation.conflicts:
                print(f"  • {conflict.module1} ↔ {conflict.module2}")
                print(f"    Reason: {conflict.reason}")
                print(f"    Severity: {conflict.severity}")

        if validation.warnings:
            print(f"\n⚠️ Warnings:")
            for warning in validation.warnings:
                print(f"  • {warning}")

        if validation.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in validation.recommendations:
                print(f"  • {rec}")

        self.state.selected_modules = validation.required_modules

    def _manage_policy(self) -> None:
        """Manage current policy."""
        print("\n" + "-" * 60)
        print("POLICY MANAGEMENT")
        print("-" * 60)

        if not self.state.selected_modules:
            print("No policy loaded. Create a policy first.")
            return

        print(f"\nCurrent Policy ({len(self.state.selected_modules)} modules):")
        for module in self.state.selected_modules:
            print(f"  • {module}")

        print("\nOptions:")
        print("  1) Compare with system")
        print("  2) Export policy")
        print("  3) Clear policy")
        print("  4) Back to main menu")
        print()

        choice = input("Select option (1-4): ").strip()

        if choice == "1":
            self._show_system_comparison()
        elif choice == "2":
            self._export_policy()
        elif choice == "3":
            self.state.selected_modules = []
            print("✓ Policy cleared")
        elif choice == "4":
            pass
        else:
            self._print_error("Invalid option")

    def _show_system_comparison(self) -> None:
        """Show policy vs system comparison."""
        if not self.state.selected_modules:
            print("No policy to compare")
            return

        comparison = self.engine.compare_with_system()

        print("\nSystem Comparison:")
        print(f"Current System Modules: {len(comparison['current_system_modules'])}")
        print(f"Database Coverage: {comparison['coverage']:.1f}%")
        print(f"Known Installed: {len(comparison['installed_known'])}")

        if comparison["unknown_modules"]:
            print(f"\nUnknown Modules in System:")
            for mod in comparison["unknown_modules"][:5]:
                print(f"  • {mod}")
            if len(comparison["unknown_modules"]) > 5:
                print(f"  ... and {len(comparison['unknown_modules']) - 5} more")

    def _export_policy(self) -> None:
        """Export policy to file."""
        if not self.state.selected_modules:
            print("No policy to export")
            return

        filename = input("Enter filename (without extension): ").strip()
        if not filename:
            filename = "pam_policy"

        # Would implement actual file export here
        print(f"✓ Policy would be exported to '{filename}.yaml'")

    def _show_database(self) -> None:
        """Browse module database."""
        print("\n" + "-" * 60)
        print("MODULE DATABASE BROWSER")
        print("-" * 60)

        print("\nFacility Categories:")
        print("  1) Authentication (auth)")
        print("  2) Account (account)")
        print("  3) Password (password)")
        print("  4) Session (session)")
        print()

        choice = input("Select facility (1-4): ").strip()
        facility_map = {
            "1": "auth",
            "2": "account",
            "3": "password",
            "4": "session",
        }

        if choice not in facility_map:
            self._print_error("Invalid facility")
            return

        print("\n" + "-" * 60)
        print(f"MODULES FOR {facility_map[choice].upper()}")
        print("-" * 60)

        all_modules = self.registry.list_all_modules()
        for i, module_name in enumerate(all_modules, 1):
            info = self.engine.get_module_info(module_name)
            if info.get("found"):
                print(f"\n{i}) {module_name}")
                print(f"   Description: {info.get('description', 'N/A')}")
                print(f"   Detailed Description: {info.get('detailed_description', 'N/A')}")
                print(f"   Category: {info.get('category', 'N/A')}")
                if info.get("dependencies"):
                    print(f"   Dependencies: {', '.join(info['dependencies'])}")

    def _manage_fragments(self) -> None:
        """Manage policy fragments."""
        from pam_manager.policy.fragment_manager import (
            PolicyFragmentManager, PolicyFragmentEntry
        )
        
        manager = PolicyFragmentManager()
        
        while True:
            print("\n" + "-" * 60)
            print("POLICY FRAGMENT MANAGER")
            print("-" * 60)
            print("  1) List fragments")
            print("  2) Create fragment")
            print("  3) Delete fragment")
            print("  4) Back to main menu")
            print()
            
            choice = input("Select option (1-4): ").strip()
            
            if choice == "1":
                fragments = manager.list_fragments()
                if fragments:
                    print(f"\n{len(fragments)} policy fragments:")
                    for frag in fragments:
                        print(f"\n  {frag.id}")
                        print(f"    Module: {frag.module}")
                        print(f"    Interface: {frag.interface}")
                        print(f"    Control: {frag.control_flag}")
                        print(f"    Security Level: {frag.security_level}")
                        if frag.parameters:
                            print(f"    Parameters: {', '.join(frag.parameters.keys())}")
                else:
                    print("\nNo fragments yet.")
            
            elif choice == "2":
                name = input("Fragment name: ").strip()
                if not name:
                    self._print_error("Name cannot be empty")
                    continue
                
                if manager.get_fragment(name):
                    self._print_error("Fragment already exists")
                    continue
                
                module = input("Module name: ").strip()
                interface = input("Interface (auth/account/session/password): ").strip()
                control = input("Control flag (required/requisite/sufficient/optional): ").strip()
                security = input("Security level (low/medium/high/maximum) [medium]: ").strip() or "medium"
                
                frag = PolicyFragmentEntry(
                    id=name,
                    description=input("Description: ").strip(),
                    module=module,
                    interface=interface,
                    control_flag=control,
                    security_level=security,
                )
                
                if manager.add_fragment(frag):
                    self._print_success(f"Fragment '{name}' created")
                else:
                    self._print_error("Failed to create fragment")
            
            elif choice == "3":
                name = input("Fragment name to delete: ").strip()
                if manager.get_fragment(name):
                    confirm = input(f"Delete '{name}'? (y/n): ").strip().lower()
                    if confirm == "y":
                        manager.remove_fragment(name)
                        self._print_success(f"Fragment '{name}' deleted")
                else:
                    self._print_error("Fragment not found")
            
            elif choice == "4":
                break
            else:
                self._print_error("Invalid option")
    
    def _manage_elements(self) -> None:
        """Manage policy elements."""
        from pam_manager.policy.fragment_manager import (
            PolicyElementManager, PolicyElementEntry, PolicyElementFragmentRef
        )
        
        manager = PolicyElementManager()
        
        while True:
            print("\n" + "-" * 60)
            print("POLICY ELEMENT MANAGER")
            print("-" * 60)
            print("  1) List elements")
            print("  2) Create element")
            print("  3) Delete element")
            print("  4) Back to main menu")
            print()
            
            choice = input("Select option (1-4): ").strip()
            
            if choice == "1":
                elements = manager.list_elements()
                if elements:
                    print(f"\n{len(elements)} policy elements:")
                    for elem in elements:
                        print(f"\n  {elem.id}")
                        print(f"    Fragments: {len(elem.fragments)}")
                        for frag in elem.fragments:
                            print(f"      - {frag.fragment_ref}")
                else:
                    print("\nNo elements yet.")
            
            elif choice == "2":
                name = input("Element name: ").strip()
                if not name:
                    self._print_error("Name cannot be empty")
                    continue
                
                if manager.get_element(name):
                    self._print_error("Element already exists")
                    continue
                
                description = input("Description: ").strip()
                fragments_refs = []
                
                while True:
                    frag_ref = input("Add fragment ref (or empty to finish): ").strip()
                    if not frag_ref:
                        break
                    
                    elem_frag = PolicyElementFragmentRef(
                        fragment_ref=frag_ref,
                        interface=input("  Interface override (empty for default): ").strip() or None,
                        control_flag=input("  Control flag override (empty for default): ").strip() or None,
                    )
                    fragments_refs.append(elem_frag)
                
                if not fragments_refs:
                    self._print_error("Element must have at least one fragment")
                    continue
                
                elem = PolicyElementEntry(
                    id=name,
                    description=description,
                    fragments=fragments_refs,
                )
                
                if manager.add_element(elem):
                    self._print_success(f"Element '{name}' created with {len(fragments_refs)} fragments")
                else:
                    self._print_error("Failed to create element")
            
            elif choice == "3":
                name = input("Element name to delete: ").strip()
                if manager.get_element(name):
                    confirm = input(f"Delete '{name}'? (y/n): ").strip().lower()
                    if confirm == "y":
                        manager.remove_element(name)
                        self._print_success(f"Element '{name}' deleted")
                else:
                    self._print_error("Element not found")
            
            elif choice == "4":
                break
            else:
                self._print_error("Invalid option")
    
    def _exit(self) -> None:
        """Exit wizard."""
        print("\nThank you for using PAM Configuration Wizard!")
        exit(0)

    @staticmethod
    def _print_error(message: str) -> None:
        """Print error message."""
        print(f"\n❌ Error: {message}")

    @staticmethod
    def _print_success(message: str) -> None:
        """Print success message."""
        print(f"\n✓ {message}")


__all__ = ["TextWizard", "WizardState"]
