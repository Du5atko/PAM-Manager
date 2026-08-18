"""Unified Configuration Manager - Handles YAML/JSON formats with automatic synchronization."""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import asdict

from .fragment_manager import (
    PolicyFragmentEntry,
    PolicyElementFragmentRef,
    PolicyElementEntry,
    PolicyFragmentManager,
    PolicyElementManager,
    ServiceDefinitionManager,
    get_pam_config_dir,
)


class UnifiedConfigManager:
    """
    Manages unified PAM configuration with YAML and JSON formats.
    
    All configuration is now stored ONLY in:
    - YAML (primary):   ~/.pam-config.yaml
    - JSON (mirror):    ~/.pam-config.json
    
    Legacy policy-fragments.yaml and policy-elements.yaml are no longer used.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize unified configuration manager.
        
        Args:
            config_dir: Directory for storing config files (default: ~/etc/pam.d)
        """
        if config_dir is None:
            self.config_dir = get_pam_config_dir()
        else:
            self.config_dir = Path(config_dir)
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths - ONLY pam-config files are used
        self.yaml_file = self.config_dir / "pam-config.yaml"
        self.json_file = self.config_dir / "pam-config.json"
        
        # Data storage
        self.data: Dict = {}
        self.fragment_manager = None
        self.element_manager = None
        self.service_manager = None
        
        # Initialize managers
        self._initialize_managers()
        
        # Load configuration
        self._load_and_sync()
    
    def _initialize_managers(self):
        """Initialize legacy managers for backward compatibility."""
        self.fragment_manager = PolicyFragmentManager(str(self.config_dir))
        self.element_manager = PolicyElementManager(str(self.config_dir))
        self.service_manager = ServiceDefinitionManager(str(self.config_dir))
    
    def _load_and_sync(self):
        """Load configuration from pam-config.yaml.
        
        This now uses ONLY pam-config.yaml/json.
        Legacy policy-fragments.yaml/policy-elements.yaml files are no longer used.
        """
        # Load YAML (primary format)
        if self.yaml_file.exists():
            self._load_yaml()
        else:
            # Create empty structure if config doesn't exist
            self._create_empty()
        
        # Synchronize JSON mirror
        self._sync_all_formats()
    
    def _create_empty(self):
        """Create empty configuration structure."""
        self.data = {
            'schema_version': '2.0',
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'metadata': {
                'name': 'PAM Configuration',
                'description': 'PAM policy configuration',
                'environment': 'production',
                'backup_enabled': True,
            },
            'fragments': [],
            'elements': [],
            'services': [],  # List of services with their elements
            'service_files': [],  # List of imported service files
            'audit_log': [],
        }
    
    def _load_yaml(self):
        """Load configuration from YAML file."""
        try:
            with open(self.yaml_file, 'r') as f:
                self.data = yaml.safe_load(f) or {}
            
            # Ensure all required keys exist
            self._ensure_structure()
        except Exception as e:
            print(f"[WARNING] Error loading YAML: {e}. Creating new config.")
            self._create_empty()
    
    def _ensure_structure(self):
        """Ensure configuration has all required keys."""
        required_keys = ['schema_version', 'metadata', 'fragments', 'elements', 'services', 'audit_log']
        for key in required_keys:
            if key not in self.data:
                if key == 'fragments':
                    self.data[key] = []
                elif key == 'elements':
                    self.data[key] = []
                elif key == 'services':
                    self.data[key] = []  # List of service objects
                elif key == 'audit_log':
                    self.data[key] = []
                elif key == 'metadata':
                    self.data[key] = {
                        'name': 'PAM Configuration',
                        'description': 'PAM policy configuration',
                    }
                elif key == 'schema_version':
                    self.data[key] = '2.0'
        
        # Update modified timestamp
        if 'modified' not in self.data:
            self.data['modified'] = datetime.now().isoformat()
    
    
    def _sync_all_formats(self):
        """Synchronize YAML and JSON formats.
        
        This ensures that both YAML (primary) and JSON (export) are always in sync.
        """
        # Always save to YAML (primary format)
        self._save_yaml()
        
        # Also save to JSON
        self._save_json()
    
    def _save_yaml(self):
        """Save configuration to YAML file."""
        try:
            self.data['modified'] = datetime.now().isoformat()
            with open(self.yaml_file, 'w') as f:
                yaml.dump(
                    self.data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
        except Exception as e:
            print(f"[ERROR] Failed to save YAML: {e}")
            raise
    
    def _save_json(self):
        """Save configuration to JSON file."""
        try:
            with open(self.json_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            print(f"[ERROR] Failed to save JSON: {e}")
            raise
    
    def _load_json(self) -> Optional[Dict]:
        """Load configuration from JSON file."""
        try:
            if self.json_file.exists():
                with open(self.json_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WARNING] Error loading JSON: {e}")
        return None
    
    # ========================================================================
    # Public API Methods
    # ========================================================================
    
    def add_fragment(self, fragment_dict: Dict) -> bool:
        """Add or update a fragment.
        
        Args:
            fragment_dict: Fragment data as dictionary
            
        Returns:
            bool: True if successful
        """
        try:
            # Create a clean copy without redundant fields
            clean_dict = dict(fragment_dict)
            # Remove redundant fields
            clean_dict.pop('platform_support', None)  # Hardcoded in code, not in config
            clean_dict.pop('parameter_help', None)    # Hardcoded in code, not in config
            
            # Find existing fragment
            existing_idx = None
            for idx, frag in enumerate(self.data['fragments']):
                if frag['id'] == clean_dict['id']:
                    existing_idx = idx
                    break
            
            # Ensure timestamps
            if 'created' not in clean_dict:
                clean_dict['created'] = datetime.now().isoformat()
            clean_dict['modified'] = datetime.now().isoformat()
            
            if existing_idx is not None:
                self.data['fragments'][existing_idx] = clean_dict
            else:
                self.data['fragments'].append(clean_dict)
            
            # Add audit log
            self._add_audit_log(
                'add_fragment',
                'success',
                f"Fragment '{clean_dict['id']}' added/updated"
            )
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to add fragment: {e}")
            return False
    
    def remove_fragment(self, fragment_id: str) -> bool:
        """Remove a fragment.
        
        Args:
            fragment_id: ID of fragment to remove
            
        Returns:
            bool: True if successful
        """
        try:
            self.data['fragments'] = [
                f for f in self.data['fragments']
                if f['id'] != fragment_id
            ]
            
            self._add_audit_log(
                'remove_fragment',
                'success',
                f"Fragment '{fragment_id}' removed"
            )
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to remove fragment: {e}")
            return False
    
    def get_fragment(self, fragment_id: str) -> Optional[Dict]:
        """Get a fragment by ID."""
        for frag in self.data['fragments']:
            if frag['id'] == fragment_id:
                return frag
        return None
    
    def list_fragments(self) -> List[Dict]:
        """List all fragments."""
        return self.data.get('fragments', [])
    
    def add_element(self, element_dict: Dict) -> bool:
        """Add or update an element."""
        try:
            # Create a clean copy without redundant fields
            clean_dict = dict(element_dict)
            # Remove redundant fields
            clean_dict.pop('platform_support', None)  # Hardcoded in code, not in config
            clean_dict.pop('service_name', None)      # Legacy field, unused
            clean_dict.pop('config_file', None)       # Legacy field, unused
            
            existing_idx = None
            for idx, elem in enumerate(self.data['elements']):
                if elem['id'] == clean_dict['id']:
                    existing_idx = idx
                    break
            
            if 'created' not in clean_dict:
                clean_dict['created'] = datetime.now().isoformat()
            clean_dict['modified'] = datetime.now().isoformat()
            
            if existing_idx is not None:
                self.data['elements'][existing_idx] = clean_dict
            else:
                self.data['elements'].append(clean_dict)
            
            self._add_audit_log(
                'add_element',
                'success',
                f"Element '{clean_dict['id']}' added/updated"
            )
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to add element: {e}")
            return False
    
    def remove_element(self, element_id: str) -> bool:
        """Remove an element."""
        try:
            self.data['elements'] = [
                e for e in self.data['elements']
                if e['id'] != element_id
            ]
            
            self._add_audit_log(
                'remove_element',
                'success',
                f"Element '{element_id}' removed"
            )
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to remove element: {e}")
            return False
    
    def get_element(self, element_id: str) -> Optional[Dict]:
        """Get an element by ID."""
        for elem in self.data['elements']:
            if elem['id'] == element_id:
                return elem
        return None
    
    def list_elements(self) -> List[Dict]:
        """List all elements."""
        return self.data.get('elements', [])
    
    def add_service(self, service_dict: Dict) -> bool:
        """Add or update a service.
        
        Args:
            service_dict: Service data as dictionary with keys: id, description, elements
            
        Returns:
            bool: True if successful
        """
        try:
            service_id = service_dict.get('id')
            if not service_id:
                print("[ERROR] Service must have 'id' field")
                return False
            
            # Find existing service
            existing_idx = None
            for idx, svc in enumerate(self.data['services']):
                if svc.get('id') == service_id:
                    existing_idx = idx
                    break
            
            # Prepare service data
            clean_dict = {
                'id': service_id,
                'description': service_dict.get('description', ''),
                'elements': service_dict.get('elements', []),
            }
            
            if existing_idx is not None:
                self.data['services'][existing_idx] = clean_dict
            else:
                self.data['services'].append(clean_dict)
            
            self._add_audit_log(
                'add_service',
                'success',
                f"Service '{service_id}' added/updated"
            )
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to add service: {e}")
            return False
    
    def remove_service(self, service_id: str) -> bool:
        """Remove a service by ID."""
        try:
            self.data['services'] = [
                s for s in self.data['services']
                if s.get('id') != service_id
            ]
            
            self._add_audit_log(
                'remove_service',
                'success',
                f"Service '{service_id}' removed"
            )
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to remove service: {e}")
            return False
    
    def get_service(self, service_id: str) -> Optional[Dict]:
        """Get a service by ID."""
        for svc in self.data['services']:
            if svc.get('id') == service_id:
                return svc
        return None
    
    def list_services(self) -> List[Dict]:
        """List all services."""
        return self.data.get('services', [])
    
    def set_service_files(self, service_files: List[str]) -> bool:
        """Set the list of imported service files."""
        try:
            self.data['service_files'] = service_files
            self._add_audit_log(
                'set_service_files',
                'success',
                f"Service files updated: {len(service_files)} files"
            )
            return True
        except Exception as e:
            print(f"[ERROR] Failed to set service files: {e}")
            return False
    
    def get_service_files(self) -> List[str]:
        """Get the list of imported service files."""
        return self.data.get('service_files', [])
    
    def add_service_file(self, service_name: str) -> bool:
        """Add a service file to the list."""
        try:
            service_files = self.get_service_files()
            if service_name not in service_files:
                service_files.append(service_name)
                self.data['service_files'] = service_files
            return True
        except Exception as e:
            print(f"[ERROR] Failed to add service file: {e}")
            return False
    
    def reload(self):
        """Reload configuration from YAML (primary format).
        
        This discards any unsaved changes and reloads from disk.
        """
        if self.yaml_file.exists():
            self._load_yaml()
        else:
            print("[WARNING] YAML config file not found. Creating new config.")
            self._create_empty()
        
        print("[INFO] Configuration reloaded from YAML")
    
    def save(self):
        """Save configuration to all formats (YAML, JSON).
        
        This ensures consistency across both formats.
        """
        try:
            self._sync_all_formats()
        except Exception as e:
            print(f"[ERROR] Failed to save configuration: {e}")
            raise
    
    def _add_audit_log(self, action: str, status: str, details: str):
        """Add entry to audit log."""
        self.data['audit_log'].append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'status': status,
            'details': details,
        })
    
    def get_metadata(self) -> Dict:
        """Get configuration metadata."""
        return self.data.get('metadata', {})
    
    def set_metadata(self, metadata: Dict):
        """Set configuration metadata."""
        self.data['metadata'] = metadata
    
    def get_audit_log(self, limit: Optional[int] = None) -> List[Dict]:
        """Get audit log entries.
        
        Args:
            limit: Maximum number of entries to return (None = all)
        """
        log = self.data.get('audit_log', [])
        if limit:
            return log[-limit:]
        return log
    
    def get_status(self) -> Dict:
        """Get configuration status."""
        return {
            'schema_version': self.data.get('schema_version', 'unknown'),
            'created': self.data.get('created', 'unknown'),
            'modified': self.data.get('modified', 'unknown'),
            'fragments_count': len(self.data.get('fragments', [])),
            'elements_count': len(self.data.get('elements', [])),
            'services_count': len(self.data.get('services', [])),
            'audit_log_entries': len(self.data.get('audit_log', [])),
            'files': {
                'yaml': str(self.yaml_file),
                'json': str(self.json_file),
            }
        }


__all__ = ['UnifiedConfigManager']
