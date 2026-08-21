"""Module management widget for PAM - Phase 4."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """Module installation status."""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    INSTALLED_NOT_LOADED = "installed_not_loaded"
    INSTALLED_BROKEN = "installed_broken"
    CONFLICTED = "conflicted"


@dataclass
class ModuleInfo:
    """Module information."""
    name: str
    category: str  # authentication, account, session, password
    description: str
    status: ModuleStatus
    installed_version: Optional[str] = None
    available_version: Optional[str] = None
    security_level: str = "medium"  # low, medium, high, critical
    alternatives: List[str] = None
    conflicts: List[str] = None
    enabled: bool = False
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []
        if self.conflicts is None:
            self.conflicts = []


class ModuleManager:
    """Manage PAM modules."""
    
    def __init__(self):
        """Initialize module manager."""
        self.modules: Dict[str, ModuleInfo] = {}
        self.enabled_modules: List[str] = []
    
    def register_module(self, module: ModuleInfo) -> None:
        """
        Register module.
        
        Args:
            module: Module information
        """
        self.modules[module.name] = module
        logger.debug(f"Registered module: {module.name}")
    
    def get_module(self, name: str) -> Optional[ModuleInfo]:
        """
        Get module information.
        
        Args:
            name: Module name
            
        Returns:
            Optional[ModuleInfo]: Module info or None
        """
        return self.modules.get(name)
    
    def get_modules_by_category(self, category: str) -> List[ModuleInfo]:
        """
        Get modules by category.
        
        Args:
            category: Module category
            
        Returns:
            List[ModuleInfo]: Modules in category
        """
        return [m for m in self.modules.values() if m.category == category]
    
    def get_installed_modules(self) -> List[ModuleInfo]:
        """
        Get installed modules.
        
        Returns:
            List[ModuleInfo]: Installed modules
        """
        return [
            m for m in self.modules.values()
            if m.status in [ModuleStatus.INSTALLED, ModuleStatus.INSTALLED_NOT_LOADED]
        ]
    
    def get_available_modules(self) -> List[ModuleInfo]:
        """
        Get available for installation modules.
        
        Returns:
            List[ModuleInfo]: Available modules
        """
        return [
            m for m in self.modules.values()
            if m.status == ModuleStatus.NOT_INSTALLED
        ]
    
    def enable_module(self, name: str) -> Tuple[bool, str]:
        """
        Enable module in configuration.
        
        Args:
            name: Module name
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        module = self.get_module(name)
        if not module:
            return (False, f"Module not found: {name}")
        
        if module.status == ModuleStatus.NOT_INSTALLED:
            return (False, f"Module not installed: {name}")
        
        if module.status == ModuleStatus.INSTALLED_BROKEN:
            return (False, f"Module is broken: {name}")
        
        # Check for conflicts
        for conflict in module.conflicts:
            if conflict in self.enabled_modules:
                return (False, f"Module conflicts with enabled module: {conflict}")
        
        if name not in self.enabled_modules:
            self.enabled_modules.append(name)
            module.enabled = True
            logger.info(f"Enabled module: {name}")
        
        return (True, f"Module enabled: {name}")
    
    def disable_module(self, name: str) -> Tuple[bool, str]:
        """
        Disable module in configuration.
        
        Args:
            name: Module name
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        module = self.get_module(name)
        if not module:
            return (False, f"Module not found: {name}")
        
        if name in self.enabled_modules:
            self.enabled_modules.remove(name)
            module.enabled = False
            logger.info(f"Disabled module: {name}")
        
        return (True, f"Module disabled: {name}")
    
    def get_enabled_modules(self) -> List[str]:
        """
        Get enabled modules.
        
        Returns:
            List[str]: Enabled module names
        """
        return self.enabled_modules
    
    def get_module_status(self, name: str) -> Optional[ModuleStatus]:
        """
        Get module status.
        
        Args:
            name: Module name
            
        Returns:
            Optional[ModuleStatus]: Module status or None
        """
        module = self.get_module(name)
        if module:
            return module.status
        return None
    
    def check_conflicts(self, modules: List[str]) -> List[Tuple[str, str]]:
        """
        Check for conflicts in module list.
        
        Args:
            modules: List of module names
            
        Returns:
            List[Tuple[str, str]]: List of (module1, module2) conflicts
        """
        conflicts = []
        
        for i, module1 in enumerate(modules):
            m1 = self.get_module(module1)
            if not m1:
                continue
            
            for module2 in modules[i+1:]:
                if module2 in m1.conflicts:
                    conflicts.append((module1, module2))
        
        return conflicts
    
    def get_alternatives(self, name: str) -> List[str]:
        """
        Get alternative modules.
        
        Args:
            name: Module name
            
        Returns:
            List[str]: Alternative modules
        """
        module = self.get_module(name)
        if module:
            return module.alternatives
        return []
    
    def generate_module_report(self) -> str:
        """
        Generate module status report.
        
        Returns:
            str: Formatted report
        """
        report = [
            "╔════════════════════════════════════════╗",
            "║        MODULE MANAGEMENT REPORT        ║",
            "╚════════════════════════════════════════╝",
            "",
            "SUMMARY:",
        ]
        
        stats = {
            "total": len(self.modules),
            "installed": len(self.get_installed_modules()),
            "available": len(self.get_available_modules()),
            "enabled": len(self.enabled_modules),
        }
        
        report.extend([
            f"  Total Modules: {stats['total']}",
            f"  Installed: {stats['installed']}",
            f"  Available: {stats['available']}",
            f"  Enabled: {stats['enabled']}",
            "",
            "INSTALLED MODULES:",
        ])
        
        installed = self.get_installed_modules()
        if installed:
            for module in sorted(installed, key=lambda x: x.name):
                status = "✓" if module.enabled else "•"
                report.append(
                    f"  {status} {module.name} "
                    f"(v{module.installed_version or '?'}) "
                    f"[{module.category}]"
                )
        else:
            report.append("  None")
        
        report.extend(["", "AVAILABLE FOR INSTALLATION:"])
        
        available = self.get_available_modules()
        if available:
            for module in sorted(available, key=lambda x: x.name):
                report.append(f"  ○ {module.name} [v{module.available_version or '?'}]")
        else:
            report.append("  None")
        
        return "\n".join(report)
    
    def get_security_audit(self) -> Dict[str, List[str]]:
        """
        Get security audit of enabled modules.
        
        Returns:
            Dict[str, List[str]]: Security level -> modules
        """
        audit = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }
        
        for name in self.enabled_modules:
            module = self.get_module(name)
            if module:
                level = module.security_level
                if level in audit:
                    audit[level].append(name)
        
        return audit


class ModuleInstallationHelper:
    """Help with module installation."""
    
    def __init__(self, manager: ModuleManager):
        """
        Initialize helper.
        
        Args:
            manager: Module manager instance
        """
        self.manager = manager
    
    def get_installation_instructions(self, name: str, platform: str) -> Dict[str, str]:
        """
        Get installation instructions for module.
        
        Args:
            name: Module name
            platform: Platform identifier
            
        Returns:
            Dict[str, str]: Installation instructions
        """
        module = self.manager.get_module(name)
        if not module:
            return {"error": f"Module not found: {name}"}
        
        # Platform-specific package names
        package_map = {
            "ubuntu": f"libpam-{name.replace('_', '-')}",
            "debian": f"libpam-{name.replace('_', '-')}",
            "fedora": f"pam-{name}",
            "rhel": f"pam-{name}",
            "freebsd": f"pam-{name}",
            "macos": f"pam-{name}",
        }
        
        package = package_map.get(platform, name)
        
        install_commands = {
            "ubuntu": f"sudo apt-get install {package}",
            "debian": f"sudo apt-get install {package}",
            "fedora": f"sudo dnf install {package}",
            "rhel": f"sudo yum install {package}",
            "freebsd": f"sudo pkg install {package}",
            "macos": f"brew install {package}",
        }
        
        return {
            "module": name,
            "platform": platform,
            "package": package,
            "install_command": install_commands.get(platform, f"Install {package}"),
            "description": module.description,
            "security_level": module.security_level,
        }
    
    def get_verification_command(self, name: str) -> str:
        """
        Get verification command to check if module is installed.
        
        Args:
            name: Module name
            
        Returns:
            str: Verification command
        """
        return f"pam-config --query {name} || echo 'Not found'"
    
    def get_rollback_instructions(self, name: str) -> str:
        """
        Get rollback/uninstall instructions.
        
        Args:
            name: Module name
            
        Returns:
            str: Rollback instructions
        """
        return f"1. Remove {name} from PAM configuration files\n" \
               f"2. Restart PAM-dependent services\n" \
               f"3. Uninstall package with package manager\n" \
               f"4. Verify with: pam-config --query {name}"
