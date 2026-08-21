"""Command-line argument parsing for PAM Manager."""

import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class CLIOptions:
    """CLI options container."""
    debug: bool = False
    populate_mode: bool = False
    populate_path: Optional[str] = None
    help_requested: bool = False


def print_help() -> None:
    """Print help message and exit."""
    print("""
PAM Manager - Graphical interface for PAM configuration management
Version: 13.0.0

USAGE:
    python PAMManager.py [OPTIONS]

OPTIONS:
    --help, -h              Show this help message and exit
    
    --debug                 Enable debug mode for detailed console output
                            Shows internal operations and data flow
                            Example: python PAMManager.py --debug
    
    --populate [FILE]       Populate PAM configuration from template or file
                            Automatically detects format (YAML, JSON, XML)
                            If no file specified, auto-detects templates
                            Examples:
                              python PAMManager.py --populate
                              python PAMManager.py --populate config.yaml
                              python PAMManager.py --populate config.json

EXAMPLES:
    # Run with all debug output
    python PAMManager.py --debug
    
    # Populate configuration from YAML file with debug
    python PAMManager.py --debug --populate /path/to/config.yaml
    
    # Auto-detect and populate with defaults
    python PAMManager.py --populate

FEATURES:
    - Interactive PAM configuration editor
    - Template-based configuration management
    - Multi-format support (YAML, JSON, XML)
    - Platform-specific module detection
    - Service definition and policy management
    - Advanced validation and conflict detection
    - Debug logging for troubleshooting

REQUIREMENTS:
    - Python 3.8+
    - PyQt5 (or PyQt4 for legacy systems)
    - pam_manager package

For more information, visit the project documentation.
    """)


def parse_arguments() -> CLIOptions:
    """
    Parse command-line arguments.
    
    Returns:
        CLIOptions: Parsed command-line options
    """
    options = CLIOptions()
    
    # Check for help
    if '--help' in sys.argv or '-h' in sys.argv:
        options.help_requested = True
        print_help()
        sys.exit(0)
    
    # Check for debug mode
    options.debug = '--debug' in sys.argv
    
    # Check for populate mode
    options.populate_mode = '--populate' in sys.argv
    
    if options.populate_mode:
        idx = sys.argv.index('--populate')
        sys.argv.pop(idx)  # Remove --populate flag
        
        # Check if next argument is a file path (not another flag)
        if idx < len(sys.argv) and not sys.argv[idx].startswith('--'):
            options.populate_path = sys.argv.pop(idx)
    
    return options
