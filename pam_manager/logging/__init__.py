"""Centralized logging configuration for PAM Manager."""

import logging
import sys
from typing import Optional


class PAMLogger:
    """Centralized logging configuration for PAM Manager."""
    
    _logger: Optional[logging.Logger] = None
    _debug_mode: bool = False
    
    @classmethod
    def configure(cls, debug_mode: bool = False, log_file: Optional[str] = None) -> logging.Logger:
        """
        Configure logging for PAM Manager.
        
        Args:
            debug_mode: Enable debug-level logging
            log_file: Optional file path for logging
            
        Returns:
            logging.Logger: Configured logger instance
        """
        cls._debug_mode = debug_mode
        
        # Create logger
        cls._logger = logging.getLogger('pam_manager')
        
        # Set log level
        log_level = logging.DEBUG if debug_mode else logging.INFO
        cls._logger.setLevel(log_level)
        
        # Remove existing handlers
        for handler in cls._logger.handlers[:]:
            cls._logger.removeHandler(handler)
        
        # Create formatter
        if debug_mode:
            logging_format = '[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s'
        else:
            logging_format = '[%(asctime)s] [%(levelname)s] %(message)s'
        
        formatter = logging.Formatter(
            format=logging_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        cls._logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                cls._logger.addHandler(file_handler)
            except Exception as e:
                cls._logger.warning(f"Could not create log file {log_file}: {e}")
        
        return cls._logger
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """
        Get logger instance.
        
        Args:
            name: Logger name (defaults to 'pam_manager')
            
        Returns:
            logging.Logger: Logger instance
        """
        if cls._logger is None:
            cls.configure()
        
        if name:
            return logging.getLogger(f'pam_manager.{name}')
        
        return cls._logger
    
    @classmethod
    def debug_enabled(cls) -> bool:
        """Check if debug mode is enabled."""
        return cls._debug_mode
    
    @classmethod
    def debug_print(cls, *args, **kwargs) -> None:
        """Print debug message only if DEBUG mode is enabled."""
        if cls._debug_mode and cls._logger:
            cls._logger.debug(' '.join(str(arg) for arg in args), **kwargs)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return PAMLogger.get_logger(name)
