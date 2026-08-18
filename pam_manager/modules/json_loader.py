"""JSON-based loader for PAM modules configuration."""

import json
from pathlib import Path
from typing import Dict, Optional, Set
import sys

from pam_manager.core import PAMFacility, PAMControlFlag, Platform
from pam_manager.modules.base import PAMModuleInfo


class ModulesJSONLoader:
    """Loader for PAM modules configuration from JSON files."""

    def __init__(self, modules_dir: Optional[Path] = None):
        """Initialize loader.
        
        Args:
            modules_dir: Path to pam.modules directory. If None, searches relative to script location.
        """
        self.modules_dir = modules_dir or self._find_modules_dir()
        self.modules_cache: Dict[str, PAMModuleInfo] = {}
        self.loaded = False
        
    def _find_modules_dir(self) -> Path:
        """Find pam.modules directory relative to project root."""
        # Try current directory
        current = Path.cwd() / "pam.modules"
        if current.exists():
            return current
        
        # Try parent directory
        parent = Path.cwd().parent / "pam.modules"
        if parent.exists():
            return parent
        
        # Try relative to this file
        script_dir = Path(__file__).parent.parent.parent
        script_modules = script_dir / "pam.modules"
        if script_modules.exists():
            return script_modules
        
        # Fall back to current directory even if doesn't exist
        return Path.cwd() / "pam.modules"
    
    def load(self) -> bool:
        """Load all modules from JSON files.
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if self.loaded and self.modules_cache:
            return True
        
        try:
            # Load list_modules.json first
            list_file = self.modules_dir / "list_modules.json"
            if not list_file.exists():
                print(f"[WARNING] Modules list file not found: {list_file}")
                return False
            
            with open(list_file, 'r') as f:
                modules_list = json.load(f)
            
            modules = modules_list.get('modules', [])
            
            # Load each module config
            for module_entry in modules:
                module_name = module_entry.get('name')
                config_file = module_entry.get('config_file')
                
                if not module_name or not config_file:
                    continue
                
                module_info = self._load_module_config(config_file)
                if module_info:
                    self.modules_cache[module_name] = module_info
            
            self.loaded = True
            # print(f"[INFO] Loaded {len(self.modules_cache)} PAM modules from JSON")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load modules from JSON: {e}")
            return False
    
    def _load_module_config(self, config_file: str) -> Optional[PAMModuleInfo]:
        """Load a single module configuration from JSON.
        
        Args:
            config_file: Filename of module config (e.g., 'pam_unix.json')
            
        Returns:
            PAMModuleInfo object or None if failed
        """
        try:
            config_path = self.modules_dir / config_file
            
            if not config_path.exists():
                print(f"[WARNING] Module config not found: {config_path}")
                return None
            
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Convert JSON data to PAMModuleInfo
            module_info = self._json_to_module_info(config_data)
            return module_info
            
        except Exception as e:
            print(f"[ERROR] Failed to load module config {config_file}: {e}")
            return None
    
    def _json_to_module_info(self, data: Dict) -> PAMModuleInfo:
        """Convert JSON data to PAMModuleInfo object.
        
        Args:
            data: JSON data dictionary
            
        Returns:
            PAMModuleInfo object
        """
        # Convert facility strings to PAMFacility enums
        facilities = set()
        for fac_str in data.get('supported_facilities', []):
            try:
                facilities.add(PAMFacility[fac_str])
            except KeyError:
                pass
        
        # Convert platform strings to Platform enums
        platforms = set()
        for plat_str in data.get('supported_platforms', []):
            try:
                platforms.add(Platform[plat_str])
            except KeyError:
                pass
        
        # Convert control flag
        control_flag_str = data.get('preferred_control_flag', 'OPTIONAL')
        try:
            control_flag = PAMControlFlag[control_flag_str]
        except KeyError:
            control_flag = PAMControlFlag.OPTIONAL
        
        # Create PAMModuleInfo object
        return PAMModuleInfo(
            name=data.get('name', ''),
            description=data.get('description', ''),
            detailed_description=data.get('detailed_description', ''),
            category=data.get('category', ''),
            supported_facilities=facilities,
            supported_platforms=platforms,
            parameters=data.get('parameters', {}),
            dependencies=set(data.get('dependencies', [])),
            conflicts=set(data.get('conflicts', [])),
            package_name_debian=data.get('package_name_debian'),
            package_name_rhel=data.get('package_name_rhel'),
            package_name_freebsd=data.get('package_name_freebsd'),
            preferred_control_flag=control_flag,
            recommended_ordering=data.get('recommended_ordering', 99),
            deprecated=data.get('deprecated', False),
            maintenance_status=data.get('maintenance_status', 'maintained'),
            security_impact=data.get('security_impact', ''),
            documentation_url=data.get('documentation_url', ''),
            notes=data.get('notes', ''),
            supported_extended_return_values=set(data.get('supported_extended_return_values', [])),
            supported_extended_actions=set(data.get('supported_extended_actions', [])),
        )
    
    def get_modules(self) -> Dict[str, PAMModuleInfo]:
        """Get all loaded modules.
        
        Returns:
            Dictionary of module_name -> PAMModuleInfo
        """
        if not self.loaded:
            self.load()
        
        return self.modules_cache.copy()
    
    def get_module(self, name: str) -> Optional[PAMModuleInfo]:
        """Get a specific module by name.
        
        Args:
            name: Module name (e.g., 'pam_unix')
            
        Returns:
            PAMModuleInfo or None if not found
        """
        if not self.loaded:
            self.load()
        
        return self.modules_cache.get(name)


# Global loader instance
_loader = None

def get_modules_loader() -> ModulesJSONLoader:
    """Get or create global modules loader instance.
    
    Returns:
        ModulesJSONLoader instance
    """
    global _loader
    if _loader is None:
        _loader = ModulesJSONLoader()
    return _loader


def load_extended_syntax() -> Optional[Dict]:
    """Load extended PAM control syntax definitions from JSON.
    
    Returns:
        Dictionary with 'return_values' and 'actions' keys, or None if failed
    """
    try:
        loader = get_modules_loader()
        extended_path = loader.modules_dir / "extended_syntax.json"
        
        if not extended_path.exists():
            print(f"[WARNING] Extended syntax file not found: {extended_path}")
            return None
        
        with open(extended_path, 'r') as f:
            data = json.load(f)
        
        print(f"[INFO] Loaded extended PAM control syntax from JSON")
        return data
        
    except Exception as e:
        print(f"[ERROR] Failed to load extended syntax: {e}")
        return None


__all__ = ["ModulesJSONLoader", "get_modules_loader", "load_extended_syntax"]
