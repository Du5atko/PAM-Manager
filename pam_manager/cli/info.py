#!/usr/bin/env python3
"""PAM Manager v2 - Info Command"""

import sys


def main():
    """Display system PAM information."""
    try:
        from pam_manager.modules import ModuleRegistry
        from pam_manager.platform.detector import PlatformDetector
        
        print()
        print("System Information:")
        print("-" * 50)
        try:
            detected_platform = PlatformDetector.detect_platform()
            print(f"  Platform: {detected_platform.name}")
        except Exception as e:
            print(f"  Platform: Unable to detect ({e})")
        
        print()
        registry = ModuleRegistry()
        module_names = registry.list_all_modules()
        
        print("Available PAM Modules:")
        print("-" * 50)
        print(f"  Total: {len(module_names)} modules")
        
        print()
        print("  Breakdown by Category:")
        print("  " + "-" * 46)
        
        # Group by category
        by_category = {}
        for mod_name in module_names:
            mod = registry.get_module(mod_name)
            if mod:
                cat = mod.category
                by_category.setdefault(cat, []).append(mod_name)
        
        for category, modules in sorted(by_category.items()):
            cat_name = category.capitalize() if isinstance(category, str) else category.value
            print(f"    - {cat_name:20} {len(modules):2} modules")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
