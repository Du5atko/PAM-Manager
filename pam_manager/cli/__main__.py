#!/usr/bin/env python3
"""PAM Manager v2 - CLI Entry Point"""

import sys


def main():
    """Main entry point for CLI."""
    try:
        from pam_manager.cli.wizard import TextWizard
        from pam_manager.core import Platform
        
        # Auto-detect platform or use default
        wizard = TextWizard()
        wizard.run()
        
    except ImportError as e:
        print(f"Error importing PAM Manager modules: {e}", file=sys.stderr)
        sys.exit(1)
    except EOFError:
        # User pressed Ctrl+D
        print()
        sys.exit(0)
    except KeyboardInterrupt:
        # User pressed Ctrl+C
        print("\nWizard cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"Error running wizard: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
