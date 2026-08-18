"""Policy Fragment and Element management module."""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from pathlib import Path
import yaml
import json
from datetime import datetime

from pam_manager.core import PAMFacility, PAMControlFlag


def get_pam_config_dir() -> Path:
    """Get PAM configuration directory with fallback support.
    
    Returns:
        Path: Directory for storing PAM configuration
        - ~/etc/pam.d (primary, always writable)
        - /etc/pam.d (secondary, if available)
    """
    home = Path.home()
    user_pam_dir = home / "etc" / "pam.d"
    user_pam_dir.mkdir(parents=True, exist_ok=True)
    return user_pam_dir


def get_etc_pam_d_dir() -> Optional[Path]:
    """Get system PAM directory if available.
    
    Returns:
        Path: /etc/pam.d directory, or None if not available
    """
    etc_dir = Path("/etc/pam.d")
    if etc_dir.exists() and etc_dir.is_dir():
        return etc_dir
    return None


@dataclass
class PolicyFragmentEntry:
    """Represents a single policy fragment.
    
    Note: control_flag and security_level are defined in PolicyElementFragmentRef,
    not in the fragment itself.
    """
    id: str
    description: str
    module: str
    interface: str  # auth, account, session, password
    parameters: Dict[str, str] = field(default_factory=dict)
    parameter_help: Dict[str, str] = field(default_factory=dict)  # param -> description
    platform_support: Dict[str, bool] = field(default_factory=dict)  # platform -> supported
    tags: List[str] = field(default_factory=list)
    created: str = ""
    modified: str = ""
    
    def __post_init__(self):
        """Set timestamps if not provided."""
        now = datetime.now().isoformat()
        if not self.created:
            self.created = now
        if not self.modified:
            self.modified = now
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for YAML serialization."""
        return asdict(self)


@dataclass
class PolicyElementFragmentRef:
    """Reference to a fragment within a policy element.
    
    Supports both standard control flags and extended control syntax.
    """
    fragment_ref: str
    interface: str  # auth, account, session, password (inherited from fragment but can be overridden)
    control_flag: str  # required, requisite, sufficient, optional, include, substack
    extended_control: Dict[str, str] = field(default_factory=dict)  # return_value -> action for extended syntax
    line_type: str = "module_line"  # module_line | directive_include
    include_target: str = ""  # target file for include directives
    include_format: str = ""  # 'at_include' for @include, 'include' for interface include
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PolicyElementEntry:
    """Represents a single policy element for a PAM service.
    
    Elements define which fragments are used and their configuration.
    """
    id: str  # Element name
    description: str
    service_name: Optional[str] = None  # e.g., 'login', 'sshd', 'sudo'
    config_file: Optional[str] = None  # Original config file path
    fragments: List[PolicyElementFragmentRef] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created: str = ""
    modified: str = ""
    
    def __post_init__(self):
        """Set timestamps if not provided."""
        now = datetime.now().isoformat()
        if not self.created:
            self.created = now
        if not self.modified:
            self.modified = now
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for YAML serialization."""
        data = asdict(self)
        data['fragments'] = [f.to_dict() for f in self.fragments]
        return data


class PolicyFragmentManager:
    """Manager for policy fragments - IN-MEMORY ONLY.
    
    NOTE: This manager no longer persists to policy-fragments.yaml/json.
    All persistence is handled by UnifiedConfigManager (pam-config.yaml/json).
    This class is retained for backward compatibility and in-memory operations.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize fragment manager (in-memory only).
        
        Args:
            storage_dir: Ignored - kept for backward compatibility
        """
        if storage_dir is None:
            self.storage_dir = get_pam_config_dir()
        else:
            self.storage_dir = Path(storage_dir)
        
        # In-memory storage only - no file persistence
        self.fragments: Dict[str, PolicyFragmentEntry] = {}
    
    def _load_fragments(self) -> None:
        """Deprecated - no longer loads from policy-fragments.yaml (in-memory only)."""
        pass  # No longer loads from file
    
    def save_fragments(self) -> bool:
        """Deprecated - returns True but does not persist.
        
        All persistence is now handled by UnifiedConfigManager.
        This method is kept for backward compatibility.
        """
        return True  # Always return success, but don't actually save
    
    def add_fragment(self, fragment: PolicyFragmentEntry) -> bool:
        """Add or update a fragment."""
        if not fragment.id:
            return False
        
        fragment.modified = datetime.now().isoformat()
        self.fragments[fragment.id] = fragment
        return self.save_fragments()
    
    def update_fragment(self, fragment: PolicyFragmentEntry) -> bool:
        """Update an existing fragment."""
        if not fragment.id or fragment.id not in self.fragments:
            return False
        
        fragment.modified = datetime.now().isoformat()
        self.fragments[fragment.id] = fragment
        return self.save_fragments()
    
    def remove_fragment(self, fragment_id: str) -> bool:
        """Remove a fragment."""
        if fragment_id in self.fragments:
            del self.fragments[fragment_id]
            return self.save_fragments()
        return False
    
    def get_fragment(self, fragment_id: str) -> Optional[PolicyFragmentEntry]:
        """Get a fragment by ID."""
        return self.fragments.get(fragment_id)
    
    def list_fragments(self) -> List[PolicyFragmentEntry]:
        """List all fragments."""
        return list(self.fragments.values())
    
    def list_fragments_by_interface(self, interface: str) -> List[PolicyFragmentEntry]:
        """List fragments by interface."""
        return [f for f in self.fragments.values() if f.interface == interface]
    
    def list_fragments_by_module(self, module: str) -> List[PolicyFragmentEntry]:
        """List fragments by module."""
        return [f for f in self.fragments.values() if f.module == module]


class PolicyElementManager:
    """Manager for policy elements - IN-MEMORY ONLY.
    
    NOTE: This manager no longer persists to policy-elements.yaml/json.
    All persistence is handled by UnifiedConfigManager (pam-config.yaml/json).
    This class is retained for backward compatibility and in-memory operations.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize element manager (in-memory only).
        
        Args:
            storage_dir: Ignored - kept for backward compatibility
        """
        if storage_dir is None:
            self.storage_dir = get_pam_config_dir()
        else:
            self.storage_dir = Path(storage_dir)
        
        # In-memory storage only - no file persistence
        self.elements: Dict[str, PolicyElementEntry] = {}
    
    def _load_elements(self) -> None:
        """Deprecated - no longer loads from policy-elements.yaml (in-memory only)."""
        pass  # No longer loads from file
    
    def save_elements(self) -> bool:
        """Deprecated - returns True but does not persist.
        
        All persistence is now handled by UnifiedConfigManager.
        This method is kept for backward compatibility.
        """
        return True  # Always return success, but don't actually save
    
    def add_element(self, element: PolicyElementEntry) -> bool:
        """Add or update an element."""
        if not element.id:
            return False
        
        element.modified = datetime.now().isoformat()
        self.elements[element.id] = element
        return self.save_elements()
    
    def update_element(self, element: PolicyElementEntry) -> bool:
        """Update an existing element."""
        if not element.id or element.id not in self.elements:
            return False
        
        element.modified = datetime.now().isoformat()
        self.elements[element.id] = element
        return self.save_elements()
    
    def remove_element(self, element_id: str) -> bool:
        """Remove an element."""
        if element_id in self.elements:
            del self.elements[element_id]
            return self.save_elements()
        return False
    
    def get_element(self, element_id: str) -> Optional[PolicyElementEntry]:
        """Get an element by ID."""
        return self.elements.get(element_id)
    
    def list_elements(self) -> List[PolicyElementEntry]:
        """List all elements."""
        return list(self.elements.values())
    
    def list_elements_by_service(self, service_name: str) -> List[PolicyElementEntry]:
        """List elements by service name."""
        return [e for e in self.elements.values() if e.service_name == service_name]


class ServiceDefinitionManager:
    """Manager for PAM service definitions from /etc/pam.d files."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize service definition manager.
        
        Args:
            storage_dir: Directory for storing generated files (default: ~/etc/pam.d)
        """
        if storage_dir is None:
            self.storage_dir = get_pam_config_dir()
        else:
            self.storage_dir = Path(storage_dir)
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.definitions_yaml = self.storage_dir / "service-definitions.yaml"
        self.definitions_json = self.storage_dir / "service-definitions.json"
        self.pam_config_dir = get_etc_pam_d_dir()
    
    def parse_pam_config_file(self, service_name: str) -> Optional[List[Dict]]:
        """Parse PAM configuration file for a service.
        
        Supports both standard control flags and extended syntax:
        - Standard: auth required pam_unix.so use_first_pass
        - Extended: auth [success=1 default=ignore] pam_sss.so use_first_pass
        
        Args:
            service_name: Service name (e.g., 'login', 'sshd')
            
        Returns:
            List of configuration lines as dicts, or None if file not found
        """
        if not self.pam_config_dir:
            return None
        
        config_file = self.pam_config_dir / service_name
        if not config_file.exists():
            return None
        
        lines = []
        try:
            with open(config_file, 'r') as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Parse directive include syntax separately from module lines
                    if line.startswith('@include'):
                        parts = line.split(maxsplit=1)
                        if len(parts) < 2:
                            continue

                        include_target = parts[1].strip()
                        if not include_target:
                            continue

                        config = {
                            'line_number': line_no,
                            'interface': 'auth',
                            'control_flag': 'include',
                            'extended_control': None,
                            'module': include_target,
                            'parameters': [],
                            'raw_line': line,
                            'line_type': 'directive_include',
                            'include_target': include_target,
                            'include_format': 'at_include',  # @include format
                        }
                        lines.append(config)
                        continue
                    
                    # Parse PAM configuration line
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    
                    interface = parts[0]
                    control_flag = None
                    extended_control = None
                    module_start_idx = 1
                    
                    # Check if parts[1] is extended syntax (starts with '[')
                    if parts[1].startswith('['):
                        # Find the closing bracket
                        bracket_content = []
                        bracket_end_idx = None
                        
                        for i in range(1, len(parts)):
                            bracket_content.append(parts[i])
                            if parts[i].endswith(']'):
                                bracket_end_idx = i
                                break
                        
                        if bracket_end_idx is not None:
                            # Extract extended syntax between [ and ]
                            extended_str = ' '.join(bracket_content)
                            extended_str = extended_str[1:-1]  # Remove [ and ]
                            
                            # Parse extended syntax: key=value key2=value2 ...
                            extended_control = {}
                            for kv_pair in extended_str.split():
                                if '=' in kv_pair:
                                    k, v = kv_pair.split('=', 1)
                                    extended_control[k.strip()] = v.strip()
                            
                            module_start_idx = bracket_end_idx + 1
                        else:
                            # Malformed: [ without matching ], treat as standard
                            control_flag = parts[1]
                            module_start_idx = 2
                    else:
                        # Standard control flag
                        control_flag = parts[1]
                        module_start_idx = 2
                    
                    # Module and parameters
                    if module_start_idx >= len(parts):
                        continue
                    
                    module = parts[module_start_idx]
                    module = module.replace('.so', '') if module.endswith('.so') else module
                    
                    parameters = parts[module_start_idx + 1:] if module_start_idx + 1 < len(parts) else []
                    
                    # Determine line_type based on control_flag
                    if control_flag == 'include':
                        line_type = 'directive_include'
                        include_target = module  # For include directives, module is the include target
                        include_format = 'include'  # Format without @
                    else:
                        line_type = 'module_line'
                        include_target = ''
                        include_format = ''
                    
                    config = {
                        'line_number': line_no,
                        'interface': interface,
                        'control_flag': control_flag,
                        'extended_control': extended_control,
                        'module': module,
                        'parameters': parameters,
                        'raw_line': line,
                        'line_type': line_type,
                        'include_target': include_target,
                        'include_format': include_format,
                    }
                    lines.append(config)
        except Exception as e:
            print(f"Error parsing {config_file}: {e}")
            return None
        
        return lines
    
    def generate_auto_names(self, config: Dict, line_no: int, service_name: str = "unknown") -> tuple[str, str]:
        """Generate automatic names for fragment and element.
        
        Naming scheme:
        - Fragment: "import/{service_name}/{module}/{interface}/{line_no}"
        - Element: "import/{service_name}/{interface}_{line_no}"
        
        Args:
            config: Configuration line dict
            line_no: Line number (within service)
            service_name: Name of the PAM service
            
        Returns:
            Tuple of (fragment_name, element_name)
        """
        # Extract module name (remove anything after '=' if present)
        module = config.get('module', 'unknown')
        if '=' in module:
            module = module.split('=')[0]
        
        interface = config.get('interface', 'auth')
        
        # Fragment name: include service_name to avoid collisions between services
        # import/{service_name}/{module}/{interface}/{line_no}
        fragment_name = f"import/{service_name}/{module}/{interface}/{line_no}"
        
        # Element name: import/{service_name}/{interface}_{line_no}
        element_name = f"import/{service_name}/{interface}_{line_no}"
        
        return fragment_name, element_name
    
    def import_service_definitions(self, service_name: str, config_lines: List[Dict],
                                   fragment_manager: 'PolicyFragmentManager',
                                   element_manager: 'PolicyElementManager') -> tuple[bool, List[str]]:
        """Import service definitions and update fragment/element managers.
        
        TRANSACTIONAL: Creates backup before import and rolls back on error.
        
        Args:
            service_name: Name of the PAM service
            config_lines: List of parsed configuration lines
            fragment_manager: PolicyFragmentManager instance
            element_manager: PolicyElementManager instance
            
        Returns:
            tuple: (success: bool, element_ids: List[str])
                   element_ids is the list of element IDs created/used for this service
        """
        try:
            from pam_manager.core import Platform
            
            # BACKUP: Save current state before making changes (initialize first)
            backup_state = None
            backup_state = self._create_backup_state(fragment_manager, element_manager)
            
            # Import fragments and elements for each config line
            imported_fragments = {}  # Track newly imported fragments
            imported_elements = {}    # Track newly imported elements
            element_ids = []          # Track element IDs for service
            
            for line_no, config in enumerate(config_lines, 1):
                # Generate names with service_name
                frag_name, elem_name = self.generate_auto_names(config, line_no, service_name)
                element_ids.append(elem_name)  # Add to service element list
                
                # Create fragment if not already exists
                if not fragment_manager.get_fragment(frag_name):
                    # Parse parameters - handle both key=value and boolean flags
                    # IMPORTANT: Store original parameter list to preserve order and duplicates
                    params = {}
                    param_list = config.get('parameters', [])
                    
                    for param in param_list:
                        if '=' in param:
                            k, v = param.split('=', 1)
                            params[k] = v
                        else:
                            # Boolean/flag parameter without value - store as True
                            params[param] = True
                    
                    # Store the original parameter list to preserve ordering and duplicates
                    # This allows us to reconstruct the exact original line later
                    if param_list:
                        # Store raw params as a special string that can be reconstructed
                        # Format: use a marker to indicate this is a parameter list
                        params['_pam_raw_params'] = param_list
                    
                    # Support all platforms
                    platform_support = {p.name: True for p in Platform}
                    
                    fragment = PolicyFragmentEntry(
                        id=frag_name,
                        description=f"Auto-imported from {service_name} line {line_no}",
                        module=config['module'],
                        interface=config['interface'],
                        parameters=params,
                        parameter_help={},
                        platform_support=platform_support,
                    )
                    fragment_manager.add_fragment(fragment)
                    imported_fragments[frag_name] = fragment
                
                # Create element if not already exists
                if not element_manager.get_element(elem_name):
                    from pam_manager.policy.fragment_manager import PolicyElementFragmentRef
                    
                    # Use extended_control if available, otherwise use control_flag
                    extended_control = config.get('extended_control') or None
                    control_flag = config.get('control_flag') or 'optional'
                    line_type = config.get('line_type') or 'module_line'
                    include_target = config.get('include_target') or ''
                    include_format = config.get('include_format') or ''
                    
                    frag_ref = PolicyElementFragmentRef(
                        fragment_ref=frag_name,
                        interface=config['interface'],
                        control_flag=control_flag,
                        extended_control=extended_control if extended_control else {},
                        line_type=line_type,
                        include_target=include_target,
                        include_format=include_format,
                    )
                    
                    element = PolicyElementEntry(
                        id=elem_name,
                        description=f"Auto-imported from {service_name} line {line_no}",
                        service_name=service_name,
                        config_file=None,
                        fragments=[frag_ref],
                    )
                    element_manager.add_element(element)
                    imported_elements[elem_name] = element
            
            # Deduplicate imported fragments and elements
            self._deduplicate_imports(fragment_manager, element_manager, 
                                     imported_fragments, imported_elements)
            
            # Save the definitions
            fragment_manager.save_fragments()
            element_manager.save_elements()
            
            return True, element_ids
        except Exception as e:
            print(f"Error importing service definitions: {e}")
            # ROLLBACK: Restore backup state (only if backup was created successfully)
            if backup_state is not None:
                try:
                    self._restore_backup_state(backup_state, fragment_manager, element_manager)
                    print(f"[ROLLBACK] Restored backup state due to error")
                except Exception as restore_error:
                    print(f"[ERROR] Failed to restore backup: {restore_error}")
            return False, []
    
    def _create_backup_state(self, fragment_manager: 'PolicyFragmentManager',
                             element_manager: 'PolicyElementManager') -> Dict:
        """Create backup of current fragment and element state.
        
        Works with both PolicyFragmentManager and UnifiedFragmentManagerAdapter.
        
        Returns:
            Dict containing backup state with deep copies
        """
        from copy import deepcopy
        
        # Handle adapters - they have list_fragments/list_elements methods
        if hasattr(fragment_manager, 'list_fragments'):
            fragments_list = fragment_manager.list_fragments()
            fragments_backup = {f.id: asdict(f) if hasattr(f, '__dataclass_fields__') else f 
                              for f in fragments_list}
        else:
            # Legacy manager with .fragments dict
            fragments_backup = deepcopy(dict(fragment_manager.fragments))
        
        if hasattr(element_manager, 'list_elements'):
            elements_list = element_manager.list_elements()
            elements_backup = {e.id: asdict(e) if hasattr(e, '__dataclass_fields__') else e 
                             for e in elements_list}
        else:
            # Legacy manager with .elements dict
            elements_backup = deepcopy(dict(element_manager.elements))
        
        return {
            'fragments': deepcopy(fragments_backup),
            'elements': deepcopy(elements_backup)
        }
    
    def _restore_backup_state(self, backup_state: Dict,
                              fragment_manager: 'PolicyFragmentManager',
                              element_manager: 'PolicyElementManager') -> None:
        """Restore fragment and element managers to backup state.
        
        Works with both PolicyFragmentManager and UnifiedFragmentManagerAdapter.
        
        Args:
            backup_state: Backup state dict from _create_backup_state
            fragment_manager: PolicyFragmentManager instance (or adapter)
            element_manager: PolicyElementManager instance (or adapter)
        """
        # Handle adapters by using remove/add methods instead of direct dict access
        if hasattr(fragment_manager, 'list_fragments'):
            # Adapter version - use remove/add methods
            current_frags = fragment_manager.list_fragments()
            for frag in current_frags:
                fragment_manager.remove_fragment(frag.id if hasattr(frag, 'id') else frag['id'])
            
            for frag_dict in backup_state['fragments'].values():
                fragment_manager.add_fragment(frag_dict if isinstance(frag_dict, dict) 
                                            else asdict(frag_dict))
        else:
            # Legacy manager with .fragments dict
            fragment_manager.fragments.clear()
            fragment_manager.fragments.update(backup_state['fragments'])
        
        if hasattr(element_manager, 'list_elements'):
            # Adapter version - use remove/add methods
            current_elems = element_manager.list_elements()
            for elem in current_elems:
                element_manager.remove_element(elem.id if hasattr(elem, 'id') else elem['id'])
            
            for elem_dict in backup_state['elements'].values():
                element_manager.add_element(elem_dict if isinstance(elem_dict, dict) 
                                          else asdict(elem_dict))
        else:
            # Legacy manager with .elements dict
            element_manager.elements.clear()
            element_manager.elements.update(backup_state['elements'])
    
    def _deduplicate_imports(self, fragment_manager, element_manager, 
                            imported_fragments, imported_elements):
        """Deduplicate imported fragments and elements.
        
        Renames duplicates using 'dedup-f/' and 'dedup-e/' prefixes.
        Fragments with same (module, interface, parameters) are deduplicated.
        Elements with same (fragment_ref, interface, control_flag) are deduplicated.
        
        Works with both PolicyFragmentManager and UnifiedFragmentManagerAdapter.
        """
        # Deduplicate fragments
        fragment_renames = {}  # old_name -> new_name
        frag_signatures = {}   # (module, interface, params_sig) -> list of fragment names
        
        for frag_name, fragment in imported_fragments.items():
            # Create signature from module, interface, and parameters
            # IMPORTANT: Handle _pam_raw_params (which is a list) by converting to tuple
            params_dict = dict(fragment.parameters) if fragment.parameters else {}
            raw_params = params_dict.pop('_pam_raw_params', None)
            
            # Create signature only from regular parameters, not raw_params
            params_items = params_dict.items() if params_dict else []
            # Convert raw_params list to tuple for hashability if needed
            if raw_params:
                params_items = list(params_items) + [('_pam_raw_params', tuple(raw_params))]
            
            params_sig = tuple(sorted(params_items)) if params_items else ()
            sig = (fragment.module, fragment.interface, params_sig)
            
            if sig not in frag_signatures:
                frag_signatures[sig] = []
            frag_signatures[sig].append(frag_name)
        
        # Rename duplicate fragments with dedup-f/ scheme
        for sig, frag_list in frag_signatures.items():
            if len(frag_list) > 1:
                module, interface, params_sig = sig
                for idx, old_frag_name in enumerate(frag_list, 1):
                    new_frag_name = f"dedup-f/{module}/{idx}"
                    fragment_renames[old_frag_name] = new_frag_name
                    
                    # Rename in fragment manager (works with adapters)
                    frag = fragment_manager.get_fragment(old_frag_name)
                    if frag:
                        # Create new fragment with renamed ID
                        frag.id = new_frag_name
                        # Add the renamed fragment
                        fragment_manager.add_fragment(frag)
                        # Remove the old one
                        fragment_manager.remove_fragment(old_frag_name)
        
        # Deduplicate elements
        element_renames = {}   # old_name -> new_name
        elem_signatures = {}   # (elem_sig) -> list of element names
        
        for elem_name, element in imported_elements.items():
            # Create signature from all fragments' details
            frags_sig = tuple(sorted([
                (f.fragment_ref, f.interface, f.control_flag, 
                 tuple(sorted(f.extended_control.items())) if f.extended_control else (),
                 f.line_type,
                 f.include_target)
                for f in element.fragments
            ]))
            
            if frags_sig not in elem_signatures:
                elem_signatures[frags_sig] = []
            elem_signatures[frags_sig].append(elem_name)
        
        # Rename duplicate elements with dedup-e/ scheme
        for frags_sig, elem_list in elem_signatures.items():
            if len(elem_list) > 1:
                # Use module name from first fragment reference
                first_frag_ref = frags_sig[0][0] if frags_sig else "unknown"
                # Extract module name (last component after last /)
                module_part = first_frag_ref.split('/')[-1] if '/' in first_frag_ref else first_frag_ref
                
                for idx, old_elem_name in enumerate(elem_list, 1):
                    new_elem_name = f"dedup-e/{module_part}/{idx}"
                    element_renames[old_elem_name] = new_elem_name
                    
                    # Rename in element manager (works with adapters)
                    elem = element_manager.get_element(old_elem_name)
                    if elem:
                        # Create new element with renamed ID
                        elem.id = new_elem_name
                        # Add the renamed element
                        element_manager.add_element(elem)
                        # Remove the old one
                        element_manager.remove_element(old_elem_name)
        
        # Update all references
        # Get all elements (works with adapters)
        all_elements = element_manager.list_elements() if hasattr(element_manager, 'list_elements') else []
        for element in all_elements:
            for frag_ref in element.fragments:
                if frag_ref.fragment_ref in fragment_renames:
                    frag_ref.fragment_ref = fragment_renames[frag_ref.fragment_ref]
                    # Update the element with renamed fragment references
                    element_manager.add_element(element)


# Standard PAM Control Flags
STANDARD_CONTROL_FLAGS = {
    'required': 'Module must succeed. Failure is noted but PAM continues processing.',
    'requisite': 'Module must succeed. On failure, PAM terminates immediately.',
    'sufficient': 'If successful and no prior required has failed, authentication succeeds immediately.',
    'optional': 'Result is usually ignored unless it is the only module in the facility.',
    'include': 'Causes the PAM library to load the configuration from another file.',
    'substack': 'Similar to include but with different return value handling.',
}

# Extended PAM Control Syntax - Return Values
EXTENDED_RETURN_VALUES = {
    'success': 'Success (PAM_SUCCESS)',
    'open_err': 'Module open error',
    'symbol_err': 'Missing symbol in module',
    'service_err': 'Service error',
    'system_err': 'System error',
    'buf_err': 'Memory error',
    'perm_denied': 'Permission denied',
    'auth_err': 'Authentication error',
    'cred_insufficient': 'Insufficient credentials',
    'authinfo_unavail': 'Authentication information not available',
    'user_unknown': 'Unknown user',
    'maxtries': 'Maximum tries exceeded',
    'new_authtok_reqd': 'New auth token required',
    'acct_expired': 'Account expired',
    'session_err': 'Session error',
    'cred_unavail': 'Credentials not available',
    'cred_expired': 'Credentials expired',
    'cred_err': 'Credentials error',
    'no_module_data': 'Module has no data',
    'conv_err': 'Communication error with application',
    'authtok_err': 'Password/token error',
    'authtok_recover_err': 'Cannot recover password',
    'authtok_lock_busy': 'Password is locked',
    'authtok_disable_aging': 'Cannot disable password aging',
    'try_again': 'Try again',
    'ignore': 'Module does not affect outcome',
    'abort': 'Critical error',
    'authtok_expired': 'Password expired',
    'module_unknown': 'Unknown module',
    'bad_item': 'Invalid item',
    'conv_again': 'Repeat conversation',
    'incomplete': 'Operation not complete',
    'default': 'All other return values',
}

# Extended PAM Control Syntax - Actions
EXTENDED_ACTIONS = {
    'ignore': 'Ignore the return value of the module.',
    'bad': 'Mark as failure but continue.',
    'die': 'Terminate immediately as failure.',
    'ok': 'Mark as success and continue.',
    'done': 'Terminate immediately as success (if no prior errors).',
    'reset': 'Reset state and continue from clean slate.',
}


class UnifiedFragmentManagerAdapter:
    """
    Adapter that wraps UnifiedConfigManager to provide PolicyFragmentManager interface.
    Used for backward compatibility and seamless migration.
    """
    
    def __init__(self, unified_manager: 'UnifiedConfigManager'):
        """Initialize adapter.
        
        Args:
            unified_manager: UnifiedConfigManager instance
        """
        self.unified = unified_manager
    
    def add_fragment(self, fragment) -> bool:
        """Add or update a fragment.
        
        Args:
            fragment: Either PolicyFragmentEntry or dict with fragment data
        """
        if isinstance(fragment, dict):
            # Received dict - pass directly to unified manager
            return self.unified.add_fragment(fragment)
        else:
            # Received dataclass - convert to dict
            return self.unified.add_fragment(asdict(fragment))
    
    def update_fragment(self, fragment: PolicyFragmentEntry) -> bool:
        """Update an existing fragment."""
        return self.unified.add_fragment(asdict(fragment))
    
    def remove_fragment(self, fragment_id: str) -> bool:
        """Remove a fragment."""
        return self.unified.remove_fragment(fragment_id)
    
    def get_fragment(self, fragment_id: str) -> Optional[PolicyFragmentEntry]:
        """Get a fragment by ID."""
        frag_dict = self.unified.get_fragment(fragment_id)
        if not frag_dict:
            return None
        return PolicyFragmentEntry(
            id=frag_dict['id'],
            description=frag_dict['description'],
            module=frag_dict['module'],
            interface=frag_dict['interface'],
            parameters=frag_dict.get('parameters', {}),
            parameter_help=frag_dict.get('parameter_help', {}),
            platform_support=frag_dict.get('platform_support', {}),
            tags=frag_dict.get('tags', []),
            created=frag_dict.get('created', ''),
            modified=frag_dict.get('modified', ''),
        )
    
    def list_fragments(self) -> List[PolicyFragmentEntry]:
        """List all fragments."""
        return [
            PolicyFragmentEntry(
                id=f['id'],
                description=f['description'],
                module=f['module'],
                interface=f['interface'],
                parameters=f.get('parameters', {}),
                parameter_help=f.get('parameter_help', {}),
                platform_support=f.get('platform_support', {}),
                tags=f.get('tags', []),
                created=f.get('created', ''),
                modified=f.get('modified', ''),
            )
            for f in self.unified.list_fragments()
        ]
    
    def save_fragments(self) -> bool:
        """Save all fragments to persistent storage."""
        try:
            self.unified.save()
            return True
        except:
            return False


class UnifiedElementManagerAdapter:
    """
    Adapter that wraps UnifiedConfigManager to provide PolicyElementManager interface.
    Used for backward compatibility and seamless migration.
    """
    
    def __init__(self, unified_manager: 'UnifiedConfigManager'):
        """Initialize adapter.
        
        Args:
            unified_manager: UnifiedConfigManager instance
        """
        self.unified = unified_manager
    
    def add_element(self, element) -> bool:
        """Add or update an element.
        
        Args:
            element: Either PolicyElementEntry or dict with element data
        """
        if isinstance(element, dict):
            # Received dict - pass directly to unified manager
            elem_dict = element
        else:
            # Received dataclass - convert to dict
            elem_dict = asdict(element)
        
        # Convert fragment objects to dicts if needed
        if 'fragments' in elem_dict:
            elem_dict['fragments'] = [
                asdict(f) if hasattr(f, '__dataclass_fields__') else f
                for f in elem_dict['fragments']
            ]
        return self.unified.add_element(elem_dict)
    
    def update_element(self, element: PolicyElementEntry) -> bool:
        """Update an existing element."""
        return self.add_element(element)
    
    def remove_element(self, element_id: str) -> bool:
        """Remove an element."""
        return self.unified.remove_element(element_id)
    
    def get_element(self, element_id: str) -> Optional[PolicyElementEntry]:
        """Get an element by ID."""
        elem_dict = self.unified.get_element(element_id)
        if not elem_dict:
            return None
        
        # Parse fragment references
        fragments = []
        for frag_ref in elem_dict.get('fragments', []):
            ref = PolicyElementFragmentRef(
                fragment_ref=frag_ref['fragment_ref'],
                interface=frag_ref['interface'],
                control_flag=frag_ref['control_flag'],
                extended_control=frag_ref.get('extended_control', {}),
                line_type=frag_ref.get('line_type', 'module_line'),
                include_target=frag_ref.get('include_target', ''),
            )
            fragments.append(ref)
        
        return PolicyElementEntry(
            id=elem_dict['id'],
            description=elem_dict['description'],
            service_name=elem_dict.get('service_name'),
            config_file=elem_dict.get('config_file'),
            fragments=fragments,
            tags=elem_dict.get('tags', []),
            created=elem_dict.get('created', ''),
            modified=elem_dict.get('modified', ''),
        )
    
    def list_elements(self) -> List[PolicyElementEntry]:
        """List all elements."""
        result = []
        for elem_dict in self.unified.list_elements():
            # Parse fragment references
            fragments = []
            for frag_ref in elem_dict.get('fragments', []):
                ref = PolicyElementFragmentRef(
                    fragment_ref=frag_ref['fragment_ref'],
                    interface=frag_ref['interface'],
                    control_flag=frag_ref['control_flag'],
                    extended_control=frag_ref.get('extended_control', {}),
                    line_type=frag_ref.get('line_type', 'module_line'),
                    include_target=frag_ref.get('include_target', ''),
                )
                fragments.append(ref)
            
            elem = PolicyElementEntry(
                id=elem_dict['id'],
                description=elem_dict['description'],
                service_name=elem_dict.get('service_name'),
                config_file=elem_dict.get('config_file'),
                fragments=fragments,
                tags=elem_dict.get('tags', []),
                created=elem_dict.get('created', ''),
                modified=elem_dict.get('modified', ''),
            )
            result.append(elem)
        
        return result
    
    def save_elements(self) -> bool:
        """Save all elements to persistent storage."""
        try:
            self.unified.save()
            return True
        except:
            return False


__all__ = [
    'PolicyFragmentEntry',
    'PolicyElementFragmentRef',
    'PolicyElementEntry',
    'PolicyFragmentManager',
    'PolicyElementManager',
    'ServiceDefinitionManager',
    'UnifiedFragmentManagerAdapter',
    'UnifiedElementManagerAdapter',
    'get_pam_config_dir',
    'get_etc_pam_d_dir',
    'STANDARD_CONTROL_FLAGS',
    'EXTENDED_RETURN_VALUES',
    'EXTENDED_ACTIONS',
]

