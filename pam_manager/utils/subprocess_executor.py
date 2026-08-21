"""Subprocess Utilities Module - Safe subprocess operations for PAM Manager.

Replaces os.system() calls with safer subprocess.run() operations.
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict

logger = logging.getLogger(__name__)


class SubprocessExecutor:
    """Wrapper for safe subprocess execution."""
    
    @staticmethod
    def run_command(cmd: List[str], shell: bool = False, 
                   check: bool = False, capture_output: bool = False,
                   timeout: Optional[int] = 10) -> Tuple[bool, str, str]:
        """Run command safely using subprocess.
        
        Args:
            cmd: Command as list (preferred) or string
            shell: Whether to run in shell mode (avoid if possible)
            check: Whether to raise exception on non-zero exit
            capture_output: Whether to capture stdout/stderr
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                shell=shell,
                check=check,
                capture_output=capture_output,
                timeout=timeout,
                text=True
            )
            return result.returncode == 0, result.stdout or "", result.stderr or ""
        except subprocess.TimeoutExpired:
            error = f"Command timeout after {timeout} seconds"
            logger.error(error)
            return False, "", error
        except Exception as e:
            error = f"Command execution failed: {e}"
            logger.error(error)
            return False, "", error
    
    @staticmethod
    def check_command_exists(cmd: str) -> bool:
        """Check if command exists in PATH using 'which'.
        
        Args:
            cmd: Command name to check
            
        Returns:
            True if command exists, False otherwise
        """
        success, _, _ = SubprocessExecutor.run_command(
            ["which", cmd],
            capture_output=True
        )
        return success
    
    @staticmethod
    def check_sudo_available(cmd: str) -> bool:
        """Check if command is available via sudo without password.
        
        Args:
            cmd: Command to check with sudo
            
        Returns:
            True if available, False otherwise
        """
        success, _, _ = SubprocessExecutor.run_command(
            ["sudo", "-n", cmd, "--version"],
            capture_output=True,
            timeout=5
        )
        return success
    
    @staticmethod
    def get_command_output(cmd: List[str], timeout: int = 10) -> Tuple[bool, str]:
        """Run command and return output.
        
        Args:
            cmd: Command as list
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, output)
        """
        success, stdout, stderr = SubprocessExecutor.run_command(
            cmd,
            capture_output=True,
            timeout=timeout
        )
        return success, stdout if success else stderr
    
    @staticmethod
    def run_with_sudo(cmd: str, args: List[str] = None) -> Tuple[bool, str, str]:
        """Run command with sudo.
        
        Args:
            cmd: Command to run
            args: Additional arguments
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        full_cmd = ["sudo", "-n", cmd]
        if args:
            full_cmd.extend(args)
        
        return SubprocessExecutor.run_command(full_cmd, capture_output=True)


class PackageManagerExecutor:
    """Execute package manager commands safely."""
    
    PACKAGE_MANAGERS = {
        'apt': {
            'install': ['apt-get', 'install', '-y'],
            'remove': ['apt-get', 'remove', '-y'],
            'update': ['apt-get', 'update'],
            'check': ['apt-get', '--version'],
            'search': ['apt-cache', 'search']
        },
        'yum': {
            'install': ['yum', 'install', '-y'],
            'remove': ['yum', 'remove', '-y'],
            'update': ['yum', 'update'],
            'check': ['yum', '--version'],
            'search': ['yum', 'search']
        },
        'dnf': {
            'install': ['dnf', 'install', '-y'],
            'remove': ['dnf', 'remove', '-y'],
            'update': ['dnf', 'update'],
            'check': ['dnf', '--version'],
            'search': ['dnf', 'search']
        },
        'pacman': {
            'install': ['pacman', '-S', '--noconfirm'],
            'remove': ['pacman', '-R', '--noconfirm'],
            'update': ['pacman', '-Sy'],
            'check': ['pacman', '--version'],
            'search': ['pacman', '-Ss']
        },
        'brew': {
            'install': ['brew', 'install'],
            'remove': ['brew', 'uninstall'],
            'update': ['brew', 'update'],
            'check': ['brew', '--version'],
            'search': ['brew', 'search']
        }
    }
    
    @staticmethod
    def detect_package_manager() -> Optional[str]:
        """Detect available package manager.
        
        Returns:
            Name of detected package manager, or None
        """
        for pm_name in PackageManagerExecutor.PACKAGE_MANAGERS.keys():
            cmd_list = PackageManagerExecutor.PACKAGE_MANAGERS[pm_name]['check']
            success, _, _ = SubprocessExecutor.run_command(
                cmd_list,
                capture_output=True,
                timeout=5
            )
            if success:
                logger.info(f"Detected package manager: {pm_name}")
                return pm_name
        
        return None
    
    @staticmethod
    def install_package(package: str, pm: str = None) -> Tuple[bool, str]:
        """Install package using detected or specified package manager.
        
        Args:
            package: Package name to install
            pm: Package manager to use (auto-detect if None)
            
        Returns:
            Tuple of (success, message)
        """
        if not pm:
            pm = PackageManagerExecutor.detect_package_manager()
            if not pm:
                return False, "No package manager detected"
        
        if pm not in PackageManagerExecutor.PACKAGE_MANAGERS:
            return False, f"Unknown package manager: {pm}"
        
        install_cmd = PackageManagerExecutor.PACKAGE_MANAGERS[pm]['install']
        full_cmd = install_cmd + [package]
        
        success, stdout, stderr = SubprocessExecutor.run_with_sudo(
            full_cmd[0],
            full_cmd[1:]
        )
        
        if success:
            return True, f"Package '{package}' installed successfully"
        else:
            return False, f"Failed to install '{package}': {stderr}"


__all__ = ['SubprocessExecutor', 'PackageManagerExecutor']
