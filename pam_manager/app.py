"""PAM Manager Application Entry Point - Orchestrates CLI, Logging, and UI."""

import sys
from typing import Optional

from pam_manager.cli.arguments import parse_arguments, CLIOptions
from pam_manager.logging import PAMLogger


class PAMManagerApp:
    """Main application controller orchestrating CLI, logging, and UI."""
    
    def __init__(self, argv: Optional[list] = None):
        """
        Initialize PAM Manager application.
        
        Args:
            argv: Command-line arguments (defaults to sys.argv)
        """
        self.argv = argv or sys.argv
        self.options: Optional[CLIOptions] = None
        self.logger = None
        self.gui = None
    
    def setup_logging(self) -> None:
        """Configure logging based on CLI options."""
        if self.options is None:
            raise RuntimeError("CLI options not parsed. Call parse_arguments() first.")
        
        log_file = None
        if self.options.debug:
            log_file = None  # Can be extended to support log file
        
        self.logger = PAMLogger.configure(
            debug_mode=self.options.debug,
            log_file=log_file
        )
        
        if self.options.debug:
            self.logger.debug("Debug mode enabled")
            if self.options.populate_mode:
                path_info = f" with file: {self.options.populate_path}" if self.options.populate_path else " (auto-detect)"
                self.logger.debug(f"Populate mode enabled{path_info}")
    
    def parse_arguments(self) -> CLIOptions:
        """
        Parse command-line arguments.
        
        Returns:
            CLIOptions: Parsed command-line options
        """
        self.options = parse_arguments()
        return self.options
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            int: Exit code
        """
        try:
            # Parse arguments
            self.parse_arguments()
            
            # Setup logging
            self.setup_logging()
            
            # Import Qt after logging is configured
            try:
                from PyQt5.QtWidgets import QApplication
            except ImportError:
                from PyQt4.QtGui import QApplication
            
            # Import main GUI
            from PAMManager import PAMManagerGUI
            
            # Create and run GUI
            qt_app = QApplication(self.argv)
            self.gui = PAMManagerGUI()
            
            # Handle populate mode
            if self.options.populate_mode:
                if self.options.populate_path:
                    if self.logger:
                        self.logger.info(f"Populating from file: {self.options.populate_path}")
                    # TODO: Call GUI populate method with path
                else:
                    if self.logger:
                        self.logger.info("Auto-detecting and populating configuration")
                    # TODO: Call GUI auto-populate method
            
            # Show GUI
            self.gui.show()
            
            # Run event loop
            return qt_app.exec_()
            
        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("Application interrupted by user")
            return 130
        except Exception as e:
            if self.logger:
                self.logger.error(f"Fatal error: {e}", exc_info=True)
            else:
                print(f"Fatal error: {e}", file=sys.stderr)
            return 1


def main() -> int:
    """Main entry point for PAM Manager."""
    app = PAMManagerApp()
    return app.run()


if __name__ == '__main__':
    sys.exit(main())
