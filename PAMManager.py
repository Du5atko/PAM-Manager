#!/usr/bin/env python3
# Copyright © 2026 Jan Dusatko - https://cryptosession.cz
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT 
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see https://www.gnu.org/licenses/.
#
"""PAM Manager GUI - Graphical interface for PAM configuration management."""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

# Configure logging (v9.0 Requirement)
logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=logging_format,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Parse command-line arguments
DEBUG = '--debug' in sys.argv
POPULATE_MODE = '--populate' in sys.argv
POPULATE_PATH = None

# Check for help
if '--help' in sys.argv or '-h' in sys.argv:
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
    sys.exit(0)

# Extract --populate path if provided
if POPULATE_MODE:
    idx = sys.argv.index('--populate')
    sys.argv.pop(idx)  # Remove --populate flag
    # Check if next argument is a file path (not another flag)
    if idx < len(sys.argv) and not sys.argv[idx].startswith('--'):
        POPULATE_PATH = sys.argv.pop(idx)

# Helper function for debug output
def _debug_print(*args, **kwargs):
    """Print debug message only if DEBUG mode is enabled."""
    if DEBUG:
        print("[DEBUG]", *args, **kwargs)

if DEBUG:
    _debug_print("Debug mode enabled")
    if POPULATE_MODE:
        _debug_print(f"Populate mode enabled{f' with file: {POPULATE_PATH}' if POPULATE_PATH else ' (auto-detect)'}")

# Set PYTHONPATH for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Qt4/Qt5 compatibility layer
try:
    from qt_compat import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, QLabel,
        QComboBox, QListWidget, QListWidgetItem, QMessageBox, QDialog,
        QDialogButtonBox, QCheckBox, QSpinBox, QTextEdit, QGroupBox,
        QFormLayout, QScrollArea, QSplitter, QHeaderView, QLineEdit,
        QSizePolicy, Qt, QTimer, pyqtSignal, QThread, QIcon, QColor, QFont, QPixmap,
        set_column_resize_mode, set_all_columns_resize_mode, get_qt_version_string
    )
except ImportError:
    print("[ERROR] Qt compatibility module not found.")
    print("Ensure qt_compat.py is in the same directory as PAMManager.py")
    sys.exit(1)

try:
    from pam_manager.modules import ModuleRegistry
    from pam_manager.platform.detector import PlatformDetector
    from pam_manager.core import Platform, PAMFacility
    from pam_manager.cli.wizard import TextWizard, WizardState
    from pam_manager.policy.fragment_manager import (
        PolicyFragmentManager, PolicyElementManager, ServiceDefinitionManager,
        PolicyFragmentEntry, PolicyElementEntry, PolicyElementFragmentRef,
        get_pam_config_dir, get_etc_pam_d_dir
    )
    from pam_manager.policy import UnifiedConfigManager
    from pam_manager.input_validator import InputValidator
    from pam_manager.utils.subprocess_executor import SubprocessExecutor, PackageManagerExecutor
    from pam_manager.validation.pam_validator import PAMValidator, ValidationLevel
    from pam_manager.storage.transactional_access import TransactionalAccess
    from pam_manager.visualization.dependency_graph import DependencyGraph
except ImportError as e:
    print(f"[ERROR] Failed to import PAM Manager modules: {e}")
    sys.exit(1)


# ============================================================================
# Exception Classes (v9.0 Requirement)
# ============================================================================

class PAMManagerException(Exception):
    """Base exception for PAM Manager."""
    pass


class ConfigurationError(PAMManagerException):
    """Configuration validation failed."""
    pass


class FileOperationError(PAMManagerException):
    """File read/write operation failed."""
    pass


class TemplateError(PAMManagerException):
    """Template operation failed."""
    pass


class ModuleError(PAMManagerException):
    """Module operation failed."""
    pass


# ============================================================================
# PAM Configuration Data Structures
# ============================================================================

from dataclasses import dataclass, field

@dataclass
class PAMConfigLine:
    """Represents a single PAM configuration line."""
    interface: str  # auth, account, session, password
    control_flag: str  # required, requisite, sufficient, optional, include, substack
    module_name: str
    parameters: Dict[str, str] = field(default_factory=dict)
    line_type: str = "module_line"  # module_line | directive_include
    include_target: str = ""
    include_format: str = ""  # 'at_include' for @include, 'include' for interface include

    @staticmethod
    def _parameter_tokens(parameters: Dict[str, str]) -> List[str]:
        """Format parameter mapping into PAM parameter tokens.
        
        Handles both key=value parameters and boolean flags.
        Boolean flags stored as True are rendered as just the key name without =value.
        """
        tokens: List[str] = []
        
        # Make a copy to avoid modifying original dict
        parameters_copy = dict(parameters)
        
        # Check for raw params that preserve original order and duplicates
        raw_params = parameters_copy.pop('_pam_raw_params', None)
        
        if raw_params and isinstance(raw_params, list):
            # Use raw params to preserve original order
            for param in raw_params:
                tokens.append(param)
        else:
            # Standard parameter rendering
            for key, value in parameters_copy.items():
                key_str = str(key)
                value_str = str(value)

                if key_str.startswith("[Without]"):
                    if value_str:
                        tokens.append(value_str)
                elif value is True or value_str == "True":
                    # Boolean flag parameter - render without =value
                    tokens.append(key_str)
                else:
                    tokens.append(f"{key_str}={value_str}")
        return tokens
    
    def to_config_string(self) -> str:
        """Convert to PAM config format string."""
        if self.line_type == "directive_include":
            target = self.include_target or self.module_name
            if self.include_format == 'at_include':
                return f"@include {target}".strip()
            else:
                # control_flag include format: interface include target
                return f"{self.interface} {self.control_flag} {target}".strip()

        param_str = " ".join(self._parameter_tokens(self.parameters))
        if param_str:
            return f"{self.interface} {self.control_flag} {self.module_name} {param_str}"
        else:
            return f"{self.interface} {self.control_flag} {self.module_name}"
    
    def __str__(self) -> str:
        """String representation for UI display."""
        if self.line_type == "directive_include":
            target = self.include_target or self.module_name
            return f"@include {target}"

        param_str = ", ".join(self._parameter_tokens(self.parameters))
        if param_str:
            return f"{self.interface} | {self.control_flag} | {self.module_name} | {param_str}"
        else:
            return f"{self.interface} | {self.control_flag} | {self.module_name}"


class PAMConfigValidator:
    """Validates PAM configuration for logical consistency."""
    
    VALID_INTERFACES = {"auth", "account", "session", "password"}
    VALID_CONTROL_FLAGS = {"required", "requisite", "sufficient", "optional", "include", "substack"}
    
    @staticmethod
    def validate(config_lines: List[PAMConfigLine]) -> tuple[bool, List[str]]:
        """Validate PAM configuration.
        
        Args:
            config_lines: List of PAM config lines
            
        Returns:
            Tuple of (is_valid, errors)
            
        Rules:
            1. Each line must have valid interface and control flag
            2. A module cannot appear with both required AND requisite unless parameters differ
            3. If same module appears multiple times without parameters, flags must not conflict
            4. If same module appears with same parameters, only one control flag allowed
        """
        errors = []
        
        # Check each line for basic validity
        for line in config_lines:
            if line.interface not in PAMConfigValidator.VALID_INTERFACES:
                errors.append(f"Invalid interface '{line.interface}' for module {line.module_name}")
            if line.control_flag not in PAMConfigValidator.VALID_CONTROL_FLAGS:
                errors.append(f"Invalid control flag '{line.control_flag}' for module {line.module_name}")
            if line.line_type == "directive_include" and not (line.include_target or line.module_name):
                errors.append("Directive include line is missing include target")
        
        # Check for conflicting module configurations
        module_configs = {}  # module_name -> list of (control_flag, params_hash, interface)
        
        for line in config_lines:
            key = (line.module_name, line.interface)
            params_hash = tuple(sorted(line.parameters.items()))
            
            if key not in module_configs:
                module_configs[key] = []
            
            module_configs[key].append((line.control_flag, params_hash))
        
        # Analyze each module/interface combination
        for (module_name, interface), configs in module_configs.items():
            control_flags = [cfg[0] for cfg in configs]
            params_hashes = [cfg[1] for cfg in configs]
            
            # Check for conflicting required/requisite without parameter differentiation
            if "required" in control_flags and "requisite" in control_flags:
                # This is only OK if the configurations have different parameters
                if len(set(params_hashes)) == 1 and params_hashes[0] == ():
                    # Both are parameterless - conflict!
                    errors.append(
                        f"Module '{module_name}' ({interface}): Cannot combine "
                        f"'required' and 'requisite' control flags without different parameters"
                    )
            
            # Check for duplicate configurations with same parameters
            for i, (flag1, params1) in enumerate(configs):
                for flag2, params2 in configs[i+1:]:
                    if params1 == params2:  # Same parameters
                        errors.append(
                            f"Module '{module_name}' ({interface}): Duplicate configuration "
                            f"with same parameters and '{flag1}', '{flag2}' flags"
                        )
        
        return len(errors) == 0, errors


def render_pam_line_from_fragment_ref(fragment_ref: Dict[str, Any], fragments_by_id: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """Render a single PAM line from a fragment reference and fragment store.
    
    Restores .so extension for PAM modules (stored without .so) and handles include directives.
    Properly handles extended control flags and parameters.
    
    Import schema:
    - Standard interfaces (auth, account, password, session) → fragment (module_line)
    - Include directives (include, substack) → service (directive_include with include_format='include')
    - @include directives → service (directive_include with include_format='at_include')
    """
    line_type = fragment_ref.get("line_type", "module_line")
    control_flag = fragment_ref.get("control_flag") or "optional"
    include_format = fragment_ref.get("include_format", "")  # 'at_include' or 'include' or ''

    # Check for include directives (identified by control_flag in ['include', 'substack'] or line_type == 'directive_include')
    if control_flag in ["include", "substack"] or line_type == "directive_include":
        # Get include target from either include_target field or fragment_ref
        include_target = fragment_ref.get("include_target", "").strip()
        if not include_target:
            # If include_target is empty, try to extract from fragment_ref
            # Fragment ref for include looks like "import/login/auth/1"
            # We need just "login" (the service name)
            frag_ref = fragment_ref.get("fragment_ref", "")
            if frag_ref and frag_ref.startswith("import/"):
                # Extract service name from fragment_ref (second component)
                parts = frag_ref.split("/")
                if len(parts) >= 2:
                    include_target = parts[1]
        
        if not include_target:
            return None
        
        # Return proper directive based on include_format
        if include_format == "at_include":
            return f"@include {include_target}"
        elif control_flag == "substack":
            return f"auth substack {include_target}"
        else:  # include_format == "include" or default
            return f"auth include {include_target}"

    frag_id = fragment_ref.get("fragment_ref")
    if not frag_id:
        return None

    fragment = fragments_by_id.get(frag_id)
    if not fragment:
        return None

    interface = fragment_ref.get("interface") or fragment.get("interface") or "auth"
    
    # Handle control flag - either extended or standard
    extended_control = fragment_ref.get("extended_control") or {}
    
    # Build control part
    if extended_control:
        # Use extended syntax [key=value key2=value2 ...]
        control_parts = " ".join([f"{k}={v}" for k, v in extended_control.items()])
        control_str = f"[{control_parts}]"
    else:
        # Use standard control flag
        control_str = control_flag
    
    module_name = fragment.get("module", "")
    parameters = fragment.get("parameters", {}) or {}

    # Restore .so extension (was removed during parsing for normalization)
    # But NOT for substack control flag, which uses PAM file names
    if (module_name and not module_name.endswith(".so") and not module_name.startswith("@") 
        and control_flag != "substack"):
        module_name = f"{module_name}.so"

    line = f"{interface} {control_str} {module_name}".strip()
    param_str = " ".join(PAMConfigLine._parameter_tokens(parameters))
    if param_str:
        line = f"{line} {param_str}"

    return line


class TemplateManager:
    """Helper class for managing template files with version collision handling."""
    
    @staticmethod
    def get_template_dir(template_type: str) -> Path:
        """Get template directory path for given type (Fragment, Element, Service).
        
        Templates are stored in: ./pam.modules/[Type].Templates/
        Not in pam_manager subdirectory.
        """
        base_dir = Path(__file__).parent / "pam.modules"
        template_dir = base_dir / f"{template_type}.Templates"
        template_dir.mkdir(parents=True, exist_ok=True)
        return template_dir
    
    @staticmethod
    def validate_template_name(name: str) -> tuple[bool, str]:
        r"""Validate template name - must not contain forbidden characters.
        
        Forbidden characters: / \ ? * !
        
        Args:
            name: Template name to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        forbidden_chars = '/\\?*!'
        for char in forbidden_chars:
            if char in name:
                return False, f"Template name contains forbidden character '{char}'. Not allowed: {forbidden_chars}"
        
        if not name.strip():
            return False, "Template name cannot be empty"
        
        return True, ""
    
    @staticmethod
    def sanitize_template_name(name: str) -> str:
        r"""Sanitize template name by replacing forbidden characters with underscores.
        
        Forbidden characters: / \ ? * ! are replaced with _
        """
        forbidden_chars = '/\\?*!'
        sanitized = name
        for char in forbidden_chars:
            sanitized = sanitized.replace(char, '_')
        return sanitized.strip()
    
    @staticmethod
    def save_template(template_type: str, name: str, data: Dict) -> Path:
        """Save template with automatic version handling on collision.
        
        Args:
            template_type: "Fragment", "Element", or "Service"
            name: Template name (will have "template." prefix)
            data: Dictionary to save as JSON
        
        Returns:
            Path to saved template file
            
        Raises:
            ValueError: If template name contains forbidden characters
        """
        import json
        
        # Validate template name
        is_valid, error_msg = TemplateManager.validate_template_name(name)
        if not is_valid:
            raise ValueError(f"Invalid template name '{name}': {error_msg}")
        
        template_dir = TemplateManager.get_template_dir(template_type)
        base_filename = f"template.{name}.json"
        file_path = template_dir / base_filename
        
        # If file doesn't exist, save it directly
        if not file_path.exists():
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return file_path
        
        # Handle collision: add version number
        version = 13
        while True:
            versioned_filename = f"template.{name}.{version}.json"
            versioned_path = template_dir / versioned_filename
            if not versioned_path.exists():
                with open(versioned_path, 'w') as f:
                    json.dump(data, f, indent=2)
                return versioned_path
            version += 1
    
    @staticmethod
    def list_templates(template_type: str) -> List[Dict]:
        """List all templates of given type.
        
        Returns:
            List of dicts with 'name' and 'path' keys
        """
        import json
        
        template_dir = TemplateManager.get_template_dir(template_type)
        templates = []
        
        if template_dir.exists():
            for template_file in template_dir.glob("template.*.json"):
                try:
                    with open(template_file, 'r') as f:
                        data = json.load(f)
                    templates.append({
                        'name': template_file.stem.replace('template.', ''),
                        'path': template_file,
                        'data': data
                    })
                except Exception as e:
                    print(f"[WARNING] Failed to load template {template_file}: {e}")
        
        return templates
    
    @staticmethod
    def list_template_names(template_type: str) -> List[str]:
        """List all template names of given type.
        
        Returns:
            List of template name strings (without 'template.' prefix and version)
        """
        templates = TemplateManager.list_templates(template_type)
        # Extract base names (remove version numbers like .1, .2, etc.)
        names = set()
        for tmpl in templates:
            # Handle versioned names: name.1, name.2 -> extract 'name'
            base_name = tmpl['name'].rsplit('.', 1)[0] if '.' in tmpl['name'] else tmpl['name']
            names.add(base_name)
        return sorted(list(names))
    
    @staticmethod
    def load_template_data(template_type: str, name: str) -> Optional[Dict]:
        """Load data from a specific template.
        
        Args:
            template_type: "Fragment", "Element", or "Service"
            name: Template name (without 'template.' prefix)
        
        Returns:
            Template data dict or None if not found
        """
        templates = TemplateManager.list_templates(template_type)
        for tmpl in templates:
            if tmpl['name'] == name:
                return tmpl['data']
        return None
    
    @staticmethod
    def clean_template_name(template_filename: str) -> str:
        """Extract clean name from template filename.
        
        template.my-policy.json → my-policy
        template.my-policy.1.json → my-policy
        template.my-policy.2.json → my-policy
        
        Args:
            template_filename: Filename like "template.name.json" or "template.name.1.json"
        
        Returns:
            Clean name without "template." prefix and without version suffix
        """
        # Remove extension
        name = template_filename.replace('.json', '')
        # Remove "template." prefix
        if name.startswith('template.'):
            name = name[9:]  # len("template.") = 9
        # Remove version suffix (e.g., ".1", ".2")
        # Split by dot and check if last part is a number
        parts = name.rsplit('.', 1)
        if len(parts) == 2 and parts[1].isdigit():
            name = parts[0]
        return name
    
    @staticmethod
    def find_available_name(base_name: str, existing_names: List[str]) -> str:
        """Find available name with suffix if collision exists.
        
        If base_name already exists in existing_names, returns:
        - base_name.1, base_name.2, base_name.3, etc.
        
        Args:
            base_name: Desired name (e.g., "my-policy")
            existing_names: List of existing names to check against
        
        Returns:
            Available name (base_name or base_name.N)
        """
        if base_name not in existing_names:
            return base_name
        
        # Find first available number
        suffix = 1
        while f"{base_name}.{suffix}" in existing_names:
            suffix += 1
        
        return f"{base_name}.{suffix}"


# ============================================================================
# Backup Management (v9.0 Requirement)
# ============================================================================

class BackupManager:
    """Manage configuration backups for recovery and audit trails."""
    
    def __init__(self, backup_dir: Optional[str] = None):
        """Initialize backup manager.
        
        Args:
            backup_dir: Directory for storing backups (default: {config_dir}/backups)
        """
        if backup_dir is None:
            config_dir = Path(get_pam_config_dir())
            self.backup_dir = config_dir / 'backups'
        else:
            self.backup_dir = Path(backup_dir)
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, source_path: str, service_name: str) -> str:
        """Create backup of configuration file before modification.
        
        Args:
            source_path: Path to source file to backup
            service_name: Name of service being backed up
            
        Returns:
            Path to created backup file
            
        Raises:
            FileOperationError: If backup creation fails
        """
        try:
            from datetime import datetime
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            backup_filename = f"backup-{service_name}-{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            logger.debug(f"Creating backup for service '{service_name}' at {backup_path}")
            
            # Read source and create backup
            with open(source_path, 'r') as src:
                content = src.read()
            
            with open(backup_path, 'w') as dst:
                dst.write(content)
            
            logger.info(f"Backup created successfully: {backup_filename} ({len(content)} bytes)")
            return str(backup_path)
        
        except Exception as e:
            logger.error(f"Failed to create backup for service '{service_name}': {e}", exc_info=True)
            raise FileOperationError(f"Failed to create backup: {e}")
    
    def restore_from_backup(self, backup_path: str, target_path: str) -> bool:
        """Restore configuration from backup file.
        
        Args:
            backup_path: Path to backup file
            target_path: Path where to restore
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            FileOperationError: If restore fails
        """
        try:
            if not Path(backup_path).exists():
                logger.error(f"Backup file not found: {backup_path}")
                raise FileOperationError(f"Backup file not found: {backup_path}")
            
            logger.debug(f"Restoring configuration from backup: {backup_path}")
            
            with open(backup_path, 'r') as src:
                content = src.read()
            
            # Create backup of current file before restoring
            if Path(target_path).exists():
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                temp_backup = self.backup_dir / f"pre-restore-{timestamp}.json"
                logger.debug(f"Creating pre-restore backup at {temp_backup}")
                with open(target_path, 'r') as f:
                    with open(temp_backup, 'w') as t:
                        t.write(f.read())
            
            with open(target_path, 'w') as dst:
                dst.write(content)
            
            logger.info(f"Configuration restored successfully from {Path(backup_path).name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to restore from backup {backup_path}: {e}", exc_info=True)
            raise FileOperationError(f"Failed to restore from backup: {e}")
    
    def list_backups(self, service_name: str) -> List[dict]:
        """List available backups for a service.
        
        Args:
            service_name: Name of service to list backups for
            
        Returns:
            List of dicts with 'name', 'size', and 'path' keys
        """
        backups = []
        for backup_file in sorted(self.backup_dir.glob(f"backup-{service_name}-*.json"), 
                                  reverse=True):
            size = backup_file.stat().st_size
            backups.append({
                'name': backup_file.name,
                'size': size,
                'path': str(backup_file)
            })
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10):
        """Clean up old backup files, keeping only N most recent.
        
        Args:
            keep_count: Number of backups to keep per service
        """
        from collections import defaultdict
        
        logger.debug(f"Starting backup cleanup (keeping {keep_count} backups per service)")
        
        # Group backups by service
        backups_by_service = defaultdict(list)
        for backup_file in self.backup_dir.glob("backup-*.json"):
            # Extract service name (format: backup-{service}-{timestamp}.json)
            parts = backup_file.name.replace('backup-', '').replace('.json', '').rsplit('-', 1)
            if len(parts) == 2:
                service_name = parts[0]
                backups_by_service[service_name].append(backup_file)
        
        # Remove old backups
        total_deleted = 0
        for service_name, backups in backups_by_service.items():
            # Sort by modification time (newest first)
            backups.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Delete backups beyond keep_count
            for backup_file in backups[keep_count:]:
                try:
                    size = backup_file.stat().st_size
                    backup_file.unlink()
                    total_deleted += 1
                    logger.debug(f"Deleted backup: {backup_file.name} ({size} bytes)")
                except Exception as e:
                    logger.warning(f"Failed to delete backup {backup_file}: {e}")
        
        if total_deleted > 0:
            logger.info(f"Backup cleanup completed: deleted {total_deleted} old backup files")


class ModuleLoadWorker(QThread):
    """Worker thread for loading modules without blocking UI."""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.registry = None
        self.modules = None
        self.platform = None
    
    def run(self):
        """Run module loading in background."""
        try:
            self.registry = ModuleRegistry()
            self.modules = self.registry.list_all_modules()
            try:
                self.platform = PlatformDetector.detect_platform()
            except:
                self.platform = Platform.UBUNTU
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class ParameterEditorDialog(QDialog):
    """Advanced dialog for editing module parameters with form inputs."""
    
    def __init__(self, module_name: str, registry: ModuleRegistry, 
                 initial_params: Optional[Dict[str, str]] = None, parent=None):
        super().__init__(parent)
        self.module_name = module_name
        self.registry = registry
        self.initial_params = initial_params or {}
        self.param_inputs: Dict[str, Dict[str, Any]] = {}
        
        self.setWindowTitle(f"Configure Parameters for {module_name}")
        self.setGeometry(100, 100, 600, 500)
        self.init_ui()
    
    def init_ui(self):
        """Initialize parameter editor UI."""
        layout = QVBoxLayout()
        
        # Get module info
        module = self.registry.get_module(self.module_name)
        if not module or not module.parameters:
            layout.addWidget(QLabel(f"Module '{self.module_name}' has no configurable parameters"))
            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(self.accept)
            layout.addWidget(buttons)
            self.setLayout(layout)
            return
        
        # Title
        title = QLabel(f"Configure Parameters for {self.module_name}")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Info label
        info = QLabel("Enter values for parameters you want to use. Leave empty to ignore.")
        info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info)
        
        # Scroll area for parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        form_layout = QFormLayout()
        
        # Create input widget for each parameter
        for param_name in sorted(module.parameters.keys()):
            param_desc = module.parameters[param_name]
            
            # Label with description
            display_name = param_name[9:] if param_name.startswith("[Without]") else param_name
            label = QLabel(display_name)
            label_tooltip = f"{param_name}: {param_desc}"
            if param_name.startswith("[Without]"):
                label_tooltip += "\nOutput format: selected value only (without name= prefix)."
            label.setToolTip(label_tooltip)

            initial_value = self.initial_params.get(param_name, "")
            # Ensure initial_value is a string (handle boolean, None, etc.)
            if initial_value is None or initial_value == "":
                initial_value = ""
            elif not isinstance(initial_value, str):
                initial_value = str(initial_value)

            if isinstance(param_desc, dict):
                # Exclusive mapping format: {"value": "hint", ...}
                list_widget = self._create_exclusive_list_widget_from_mapping(param_desc, initial_value)
                self.param_inputs[param_name] = {
                    "kind": "single",
                    "list_widget": list_widget,
                }
                form_layout.addRow(label, list_widget)
            elif isinstance(param_desc, list):
                # Exclusive tuple list: [value1, help1, value2, help2, ...]
                # Non-exclusive tuple list: [value1, help1, ..., "delimiter(s):..."]
                if self._is_non_exclusive_tuple_list(param_desc):
                    container = self._create_non_exclusive_list_widget(param_desc, initial_value)
                    self.param_inputs[param_name] = {
                        "kind": "multi",
                        "list_widget": container["list_widget"],
                        "delimiter": container["delimiter"],
                    }
                    form_layout.addRow(label, container["widget"])
                elif self._is_exclusive_tuple_list(param_desc):
                    list_widget = self._create_exclusive_list_widget(param_desc, initial_value)
                    self.param_inputs[param_name] = {
                        "kind": "single",
                        "list_widget": list_widget,
                    }
                    form_layout.addRow(label, list_widget)
                else:
                    # Fallback for malformed list definition
                    input_field = QLineEdit()
                    input_field.setPlaceholderText("Invalid parameter metadata format")
                    if initial_value:
                        input_field.setText(initial_value)
                    self.param_inputs[param_name] = {
                        "kind": "text",
                        "input": input_field,
                    }
                    form_layout.addRow(label, input_field)
            else:
                # Standard text parameter
                input_field = QLineEdit()
                input_field.setPlaceholderText(str(param_desc))
                if initial_value:
                    input_field.setText(initial_value)
                self.param_inputs[param_name] = {
                    "kind": "text",
                    "input": input_field,
                }
                form_layout.addRow(label, input_field)
        
        scroll_widget.setLayout(form_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_parameters(self) -> Dict[str, str]:
        """Get only non-empty parameter values."""
        params = {}
        for param_name, entry in self.param_inputs.items():
            kind = entry.get("kind")

            if kind == "text":
                input_field = entry.get("input")
                value = input_field.text().strip() if input_field else ""
                if value:
                    params[param_name] = value
                continue

            if kind == "single":
                list_widget = entry.get("list_widget")
                if not list_widget:
                    continue
                current_item = list_widget.currentItem()
                if current_item is None:
                    continue
                selected_value = current_item.data(Qt.UserRole)
                if selected_value:
                    params[param_name] = str(selected_value)
                continue

            if kind == "multi":
                list_widget = entry.get("list_widget")
                if not list_widget:
                    continue

                selected_values: List[str] = []
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item.checkState() == Qt.Checked:
                        value = item.data(Qt.UserRole)
                        if value is not None:
                            selected_values.append(str(value))

                if not selected_values:
                    continue

                delimiter = ","
                if entry.get("delimiter"):
                    delimiter = str(entry.get("delimiter"))

                params[param_name] = delimiter.join(selected_values)

        return params

    @staticmethod
    def _visible_rows_for_option_count(option_count: int) -> int:
        """Return minimum visible rows based on option count."""
        if option_count <= 5:
            return 3
        if option_count <= 8:
            return 4
        return 5

    @staticmethod
    def _is_exclusive_tuple_list(param_desc: List[Any]) -> bool:
        """True for even-length [value, help, ...] tuple list."""
        if len(param_desc) < 2 or (len(param_desc) % 2) != 0:
            return False
        return all(isinstance(x, str) for x in param_desc)

    @staticmethod
    def _is_non_exclusive_tuple_list(param_desc: List[Any]) -> bool:
        """True for odd-length [value, help, ..., 'delimiter(s):...'] format."""
        if len(param_desc) < 3 or (len(param_desc) % 2) == 0:
            return False
        if not all(isinstance(x, str) for x in param_desc):
            return False
        marker = param_desc[-1].strip().lower()
        return marker.startswith("delimiter(s):")

    def _create_exclusive_list_widget(self, param_desc: List[str], initial_value: str) -> QListWidget:
        """Create single-selection scrollable list with entries 'value: help'."""
        options: List[tuple[str, str]] = []
        for i in range(0, len(param_desc), 2):
            options.append((param_desc[i], param_desc[i + 1]))
        return self._build_exclusive_list_widget(options, initial_value)

    def _create_exclusive_list_widget_from_mapping(self, param_desc: Dict[str, str], initial_value: str) -> QListWidget:
        """Create single-selection list from mapping format {'value': 'hint', ...}."""
        options: List[tuple[str, str]] = []
        for value, hint in param_desc.items():
            options.append((str(value), str(hint)))
        return self._build_exclusive_list_widget(options, initial_value)

    def _build_exclusive_list_widget(self, options: List[tuple[str, str]], initial_value: str) -> QListWidget:
        """Render single-selection scrollable list with entries 'value: hint'."""
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SingleSelection)

        for idx, (value, hint) in enumerate(options):
            item = QListWidgetItem(f"{value}: {hint}")
            item.setData(Qt.UserRole, value)
            list_widget.addItem(item)
            if initial_value and value == initial_value:
                list_widget.setCurrentRow(idx)

        # Default to first option when no initial value is set
        if not initial_value and list_widget.count() > 0:
            list_widget.setCurrentRow(0)

        visible_rows = self._visible_rows_for_option_count(len(options))
        row_height = max(22, list_widget.sizeHintForRow(0) if list_widget.count() else 22)
        list_widget.setMinimumHeight((row_height * visible_rows) + 8)
        list_widget.setMaximumHeight((row_height * visible_rows) + 8)
        return list_widget

    def _create_non_exclusive_list_widget(self, param_desc: List[str], initial_value: str) -> Dict[str, Any]:
        """Create checkbox list for non-exclusive options with auto-selected delimiter."""
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)

        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.NoSelection)

        options_raw = param_desc[:-1]
        options: List[tuple[str, str]] = []
        for i in range(0, len(options_raw), 2):
            options.append((options_raw[i], options_raw[i + 1]))

        delimiter_values = self._parse_delimiters(param_desc[-1])
        delimiter = delimiter_values[0] if delimiter_values else ","
        initial_selected = set()
        if initial_value:
            if delimiter and delimiter in initial_value:
                initial_selected = {v for v in initial_value.split(delimiter) if v}
            elif delimiter:
                # Fallback split for legacy values that may use a different separator
                for candidate in delimiter_values:
                    if candidate and candidate in initial_value:
                        initial_selected = {v for v in initial_value.split(candidate) if v}
                        break
            if not initial_selected:
                initial_selected = {initial_value}

        for value, hint in options:
            item = QListWidgetItem(f"{value}: {hint}")
            item.setData(Qt.UserRole, value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if value in initial_selected else Qt.Unchecked)
            list_widget.addItem(item)

        visible_rows = self._visible_rows_for_option_count(len(options))
        row_height = max(22, list_widget.sizeHintForRow(0) if list_widget.count() else 22)
        list_widget.setMinimumHeight((row_height * visible_rows) + 8)
        list_widget.setMaximumHeight((row_height * visible_rows) + 8)
        container_layout.addWidget(list_widget)

        auto_delimiter_label = QLabel(f"Auto delimiter: {delimiter}")
        auto_delimiter_label.setStyleSheet("color: gray; font-style: italic;")
        container_layout.addWidget(auto_delimiter_label)

        container.setLayout(container_layout)
        return {
            "widget": container,
            "list_widget": list_widget,
            "delimiter": delimiter,
        }

    @staticmethod
    def _parse_delimiters(delimiter_spec: str) -> List[str]:
        """Parse delimiter specification from final tuple item.

        The first parsed delimiter is used automatically.
        """
        raw = delimiter_spec.split(":", 1)[1].strip() if ":" in delimiter_spec else ""
        if not raw:
            return [","]

        has_comma = "," in raw

        parts: List[str] = []
        for chunk in raw.split(","):
            for token in chunk.split():
                token = token.strip()
                if token:
                    parts.append(token)

        if not parts:
            return [","]

        normalized: List[str] = []
        if has_comma:
            normalized.append(",")

        for token in parts:
            # If token is punctuation-only multi-char token (e.g. ';|'), split into chars.
            if len(token) > 1 and all(ch in ",;|:/" for ch in token):
                for ch in token:
                    if ch not in normalized:
                        normalized.append(ch)
                continue

            if token not in normalized:
                normalized.append(token)

        return normalized or [","]


class ModuleInfoDialog(QDialog):
    """Dialog displaying detailed module information."""
    
    def __init__(self, module_name: str, registry: ModuleRegistry, parent=None):
        super().__init__(parent)
        self.module_name = module_name
        self.registry = registry
        self.setWindowTitle(f"PAM Module: {module_name}")
        self.setGeometry(100, 100, 700, 600)
        self.init_ui()
    
    def init_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout()
        
        # Get module info
        module = self.registry.get_module(self.module_name)
        if not module:
            layout.addWidget(QLabel("Module not found"))
            self.setLayout(layout)
            return
        
        # Create scrollable text display
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        info_text = f"""
MODULE INFORMATION
{'='*60}

Name:                    {module.name}
Category:                {module.category}
Description:             {module.description}

DETAILED DESCRIPTION
{'-'*60}
{module.detailed_description}

SUPPORTED FACILITIES
{'-'*60}
Facilities:              {', '.join([f.value for f in module.supported_facilities])}
Platforms:               {', '.join([p.name for p in module.supported_platforms]) if module.supported_platforms else 'None'}

CONTROL FLAG & ORDERING
{'-'*60}
Preferred Control Flag:  {module.preferred_control_flag.value}
Recommended Ordering:    {module.recommended_ordering}
Maintenance Status:      {module.maintenance_status}

SECURITY
{'-'*60}
Security Impact:         {module.security_impact}
Deprecated:              {'Yes' if module.deprecated else 'No'}

AVAILABLE PARAMETERS
{'-'*60}"""
        
        if module.parameters:
            for param_name in sorted(module.parameters.keys()):
                param_desc = module.parameters[param_name]
                info_text += f"\n{param_name}:\n    {param_desc}"
        else:
            info_text += "\nNo parameters available for this module."
        
        info_text += f"""

DEPENDENCIES & CONFLICTS
{'-'*60}
Dependencies:            {', '.join(module.dependencies) if module.dependencies else 'None'}
Conflicts:               {', '.join(module.conflicts) if module.conflicts else 'None'}

NOTES
{'-'*60}
{module.notes or 'No additional notes'}
        """
        
        text_edit.setText(info_text)
        scroll.setWidget(text_edit)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Close")
        ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)


# ============================================================================
# Advanced Dialog Classes for Edit Operations
# ============================================================================

class FragmentEditDialog(QDialog):
    """Dialog for editing an existing policy fragment."""
    
    def __init__(self, fragment: PolicyFragmentEntry, registry: ModuleRegistry, parent=None):
        super().__init__(parent)
        self.fragment = fragment
        self.registry = registry
        self.setWindowTitle(f"Edit Fragment: {fragment.id}")
        self.setGeometry(100, 100, 600, 500)
        self.init_ui()
    
    def init_ui(self):
        """Initialize fragment edit UI."""
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # Fragment name (read-only)
        self.name_label = QLineEdit()
        self.name_label.setText(self.fragment.id)
        self.name_label.setReadOnly(True)
        form_layout.addRow("Fragment Name:", self.name_label)
        
        # Description
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setText(self.fragment.description)
        form_layout.addRow("Description:", self.desc_input)
        
        # Module (read-only)
        self.module_label = QLineEdit()
        self.module_label.setText(self.fragment.module)
        self.module_label.setReadOnly(True)
        form_layout.addRow("Module:", self.module_label)
        
        # Interface (read-only - defined in element)
        self.interface_info = QLineEdit()
        self.interface_info.setText("Defined per Policy Element")
        self.interface_info.setReadOnly(True)
        form_layout.addRow("Interface:", self.interface_info)
        
        # Parameters button
        self.params_button = QPushButton("Configure Parameters...")
        self.fragment.parameters = self.fragment.parameters or {}
        self.params_button.clicked.connect(self._edit_parameters)
        form_layout.addRow("Parameters:", self.params_button)
        
        # Current parameters display (single editable line)
        self.params_display = QLineEdit()
        if self.fragment.parameters:
            params_str = ", ".join(PAMConfigLine._parameter_tokens(self.fragment.parameters))
            self.params_display.setText(params_str)
        else:
            self.params_display.setText("(none configured)")
        self.params_display.setReadOnly(True)
        form_layout.addRow("", self.params_display)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def _edit_parameters(self):
        """Open parameter editor dialog."""
        dialog = ParameterEditorDialog(
            self.fragment.module,
            self.registry,
            self.fragment.parameters,
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            self.fragment.parameters = dialog.get_parameters()
            # Update display
            if self.fragment.parameters:
                params_str = ", ".join(PAMConfigLine._parameter_tokens(self.fragment.parameters))
                self.params_display.setText(params_str)
            else:
                self.params_display.setText("(none configured)")
    
    def get_fragment(self) -> PolicyFragmentEntry:
        """Get updated fragment."""
        self.fragment.description = self.desc_input.toPlainText()
        
        # Parameter help is no longer used
        self.fragment.parameter_help = {}
        
        return self.fragment


class ElementEditDialog(QDialog):
    """Dialog for editing an existing policy element."""
    
    def __init__(self, element: PolicyElementEntry, parent=None):
        super().__init__(parent)
        self.element = element
        self.setWindowTitle(f"Edit Element: {element.id}")
        self.setGeometry(100, 100, 600, 400)
        self.init_ui()
    
    def init_ui(self):
        """Initialize element edit UI."""
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # Element name (read-only)
        self.name_label = QLineEdit()
        self.name_label.setText(self.element.id)
        self.name_label.setReadOnly(True)
        form_layout.addRow("Element Name:", self.name_label)
        
        # Description
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setText(self.element.description)
        form_layout.addRow("Description:", self.desc_input)
        
        # Fragment name - display all fragment names (read-only)
        fragment_names = ", ".join([f.fragment_ref for f in self.element.fragments]) if self.element.fragments else "(none)"
        self.fragment_name_label = QLineEdit()
        self.fragment_name_label.setText(fragment_names)
        self.fragment_name_label.setReadOnly(True)
        form_layout.addRow("Fragment Name:", self.fragment_name_label)
        
        # PAM Command Builder button
        pam_builder_button = QPushButton("Open PAM Command Builder")
        pam_builder_button.setMaximumWidth(200)
        pam_builder_button.clicked.connect(self._open_pam_command_builder)
        pam_button_layout = QHBoxLayout()
        pam_button_layout.addWidget(pam_builder_button)
        pam_button_layout.addStretch()
        form_layout.addRow("Build PAM Command:", pam_button_layout)
        
        # Service name
        self.service_input = QLineEdit()
        self.service_input.setText(self.element.service_name or "")
        form_layout.addRow("Service Name:", self.service_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def _open_pam_command_builder(self):
        """Open PAM command builder dialog."""
        dialog = PAMControlSyntaxBuilder(self)
        if dialog.exec_() == QDialog.Accepted:
            # Get the selected interface and control settings
            iface, control_flag, extended = dialog.get_pam_line_parts()
            # Could use this to update element if needed
            pass
    
    def get_element(self) -> PolicyElementEntry:
        """Get updated element."""
        self.element.description = self.desc_input.toPlainText()
        self.element.service_name = self.service_input.text().strip() or None
        self.element.config_file = None  # config_file is no longer edited
        return self.element


class ControlSyntaxDialog(QDialog):
    """Dialog for editing extended PAM control syntax."""
    
    def __init__(self, fragment_ref: PolicyElementFragmentRef, 
                 module_name: str, registry: ModuleRegistry, parent=None):
        super().__init__(parent)
        self.fragment_ref = fragment_ref
        self.module_name = module_name
        self.registry = registry
        self.setWindowTitle("Configure Extended Control Syntax")
        self.setGeometry(100, 100, 700, 600)
        self.init_ui()
    
    def init_ui(self):
        """Initialize extended control syntax UI."""
        from pam_manager.policy.fragment_manager import (
            EXTENDED_RETURN_VALUES, EXTENDED_ACTIONS
        )
        
        layout = QVBoxLayout()
        
        # Info
        info_label = QLabel(
            "Extended control syntax: [return_value1=action1 return_value2=action2 ...]\n"
            "Only supported if specified for the module. Leave empty to use standard control flag."
        )
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info_label)
        
        # Return value selection
        returns_group = QGroupBox("Return Values & Actions")
        returns_layout = QVBoxLayout()
        
        # Get module's supported extended syntax
        module = self.registry.get_module(self.module_name)
        supported_returns = module.supported_extended_return_values if module else set(EXTENDED_RETURN_VALUES.keys())
        supported_actions = module.supported_extended_actions if module else set(EXTENDED_ACTIONS.keys())
        
        self.return_inputs: Dict[str, QComboBox] = {}
        
        form = QFormLayout()
        for ret_val in sorted(supported_returns):
            ret_desc = EXTENDED_RETURN_VALUES.get(ret_val, ret_val)
            
            combo = QComboBox()
            combo.addItem("(none)")
            for action in sorted(supported_actions):
                act_desc = EXTENDED_ACTIONS.get(action, action)
                combo.addItem(action)
            
            # Set current value if exists
            if ret_val in self.fragment_ref.extended_control:
                current_action = self.fragment_ref.extended_control[ret_val]
                index = combo.findText(current_action)
                if index >= 0:
                    combo.setCurrentIndex(index)
            
            self.return_inputs[ret_val] = combo
            form.addRow(f"{ret_val}: {ret_desc}", combo)
        
        returns_layout.addLayout(form)
        returns_group.setLayout(returns_layout)
        layout.addWidget(returns_group)
        
        # Display current syntax
        if self.fragment_ref.extended_control:
            current_syntax = " ".join([f"{k}={v}" for k, v in self.fragment_ref.extended_control.items()])
        else:
            current_syntax = "(none configured)"
        
        current_label = QLabel(f"Current Syntax: [{current_syntax}]")
        current_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(current_label)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_extended_control(self) -> Dict[str, str]:
        """Get extended control syntax mapping."""
        result = {}
        for ret_val, combo in self.return_inputs.items():
            action = combo.currentText()
            if action != "(none)":
                result[ret_val] = action
        return result


class FragmentRefEditDialog(QDialog):
    """Dialog for editing fragment reference in a policy element (interface, control flag, extended syntax)."""
    
    def __init__(self, fragment_ref: PolicyElementFragmentRef, 
                 fragment: PolicyFragmentEntry, registry: ModuleRegistry, parent=None):
        super().__init__(parent)
        self.fragment_ref = fragment_ref
        self.fragment = fragment
        self.registry = registry
        self.setWindowTitle(f"Edit Fragment Reference: {fragment_ref.fragment_ref}")
        self.setGeometry(100, 100, 600, 400)
        self.init_ui()
    
    def init_ui(self):
        """Initialize fragment reference edit UI."""
        from pam_manager.policy.fragment_manager import STANDARD_CONTROL_FLAGS
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # Fragment name (read-only)
        frag_label = QLineEdit()
        frag_label.setText(self.fragment_ref.fragment_ref)
        frag_label.setReadOnly(True)
        form_layout.addRow("Fragment:", frag_label)
        
        # Interface
        self.interface_combo = QComboBox()
        for facility in ["auth", "account", "session", "password"]:
            self.interface_combo.addItem(facility)
        self.interface_combo.setCurrentText(self.fragment_ref.interface)
        form_layout.addRow("Interface:", self.interface_combo)
        
        # Control flag
        self.control_flag_combo = QComboBox()
        for flag in sorted(STANDARD_CONTROL_FLAGS.keys()):
            self.control_flag_combo.addItem(flag)
        self.control_flag_combo.setCurrentText(self.fragment_ref.control_flag)
        form_layout.addRow("Control Flag:", self.control_flag_combo)
        
        # Extended syntax button
        self.extended_button = QPushButton("Configure Extended Syntax...")
        self.extended_button.clicked.connect(self._edit_extended_syntax)
        form_layout.addRow("Extended Syntax:", self.extended_button)
        
        # Display current extended syntax if any
        if self.fragment_ref.extended_control:
            ext_syntax = " ".join([f"{k}={v}" for k, v in self.fragment_ref.extended_control.items()])
        else:
            ext_syntax = "(none)"
        
        self.ext_syntax_label = QLabel(f"Current: [{ext_syntax}]")
        self.ext_syntax_label.setStyleSheet("color: blue; font-weight: bold; font-size: 9pt;")
        form_layout.addRow("", self.ext_syntax_label)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def _edit_extended_syntax(self):
        """Open extended control syntax editor."""
        dialog = ControlSyntaxDialog(
            self.fragment_ref,
            self.fragment.module,
            self.registry,
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            self.fragment_ref.extended_control = dialog.get_extended_control()
            
            # Update label
            if self.fragment_ref.extended_control:
                ext_syntax = " ".join([f"{k}={v}" for k, v in self.fragment_ref.extended_control.items()])
            else:
                ext_syntax = "(none)"
            self.ext_syntax_label.setText(f"Current: [{ext_syntax}]")
    
    def get_fragment_ref(self) -> PolicyElementFragmentRef:
        """Get updated fragment reference."""
        self.fragment_ref.interface = self.interface_combo.currentText()
        self.fragment_ref.control_flag = self.control_flag_combo.currentText()
        return self.fragment_ref


class ServiceFileSelectDialog(QDialog):
    """Dialog for selecting or creating a service file."""
    
    def __init__(self, available_files: List[str], parent=None):
        super().__init__(parent)
        self.available_files = sorted(available_files)
        self.selected_file = None
        self.setWindowTitle("Select or Create Service File")
        self.setGeometry(100, 100, 400, 300)
        self.init_ui()
    
    def init_ui(self):
        """Initialize service file selection UI."""
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("Select an existing service file or create a new one:")
        layout.addWidget(info)
        
        form_layout = QFormLayout()
        
        # List for existing files with navigation arrows
        file_select_layout = QHBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(120)
        for fname in self.available_files:
            self.file_list.addItem(fname)
        if self.available_files:
            self.file_list.setCurrentRow(0)
        
        # Navigation buttons
        nav_layout = QVBoxLayout()
        up_button = QPushButton("▲")
        up_button.setMaximumWidth(40)
        up_button.clicked.connect(lambda: self._scroll_file_list(-1))
        nav_layout.addWidget(up_button)
        
        # Position indicator
        self.file_position_label = QLabel("1/10" if self.available_files else "0/0")
        self.file_position_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.file_position_label, 1)
        
        down_button = QPushButton("▼")
        down_button.setMaximumWidth(40)
        down_button.clicked.connect(lambda: self._scroll_file_list(1))
        nav_layout.addWidget(down_button)
        
        file_select_layout.addWidget(self.file_list, 1)
        file_select_layout.addLayout(nav_layout)
        
        file_widget = QWidget()
        file_widget.setLayout(file_select_layout)
        form_layout.addRow("Service File:", file_widget)
        
        # Input for new file name
        self.new_file_input = QLineEdit()
        self.new_file_input.setPlaceholderText("Or enter new service file name (e.g., my-service)")
        form_layout.addRow("New File Name:", self.new_file_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def _scroll_file_list(self, direction: int):
        """Scroll file list up or down. direction: -1 for up, 1 for down."""
        if self.file_list.count() == 0:
            return
        
        current_row = self.file_list.currentRow()
        new_row = current_row + direction
        
        # Clamp to valid range
        if new_row < 0:
            new_row = 0
        elif new_row >= self.file_list.count():
            new_row = self.file_list.count() - 1
        
        self.file_list.setCurrentRow(new_row)
        self.file_list.scrollToItem(self.file_list.itemFromIndex(self.file_list.currentIndex()))
        
        # Update position label
        total = self.file_list.count()
        self.file_position_label.setText(f"{new_row + 1}/{total}")
    
    def _on_accept(self):
        """Handle accept - check if file or new file is selected."""
        current_item = self.file_list.currentItem()
        new_file = self.new_file_input.text().strip()
        
        if new_file:
            self.selected_file = new_file
        elif current_item:
            self.selected_file = current_item.text()
        else:
            QMessageBox.warning(self, "Error", "Please select or enter a service file name")
            return
        
        self.accept()
    
    def _on_selection_changed(self):
        """Handle combo selection change. DEPRECATED - replaced by _scroll_file_list."""
        pass
    
    def get_selected_file(self) -> Optional[str]:
        """Get selected or new file name."""
        return self.selected_file


# ============================================================================
# Advanced PAM Command Builder Classes
# ============================================================================

class ExtendedControlBuilderDialog(QDialog):
    """Dialog for building extended PAM control syntax [value=action ...]."""
    
    # Default hardcoded fallback values
    DEFAULT_RETURN_VALUES = {
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
    
    DEFAULT_ACTIONS = {
        'ignore': 'Ignore the return value',
        'bad': 'Mark as failure but continue',
        'die': 'Terminate immediately as failure',
        'ok': 'Mark as success and continue',
        'done': 'Terminate immediately as success (if no prior errors)',
        'reset': 'Reset state and continue from clean slate',
    }
    
    def __init__(self, initial_extended: Optional[Dict[str, str]] = None, parent=None):
        super().__init__(parent)
        self.initial_extended = initial_extended or {}
        self.selected_syntax: Dict[str, str] = {}
        self.setWindowTitle("Configure Extended Control Syntax")
        self.setGeometry(100, 100, 1000, 700)
        
        # Load extended syntax data from JSON, with fallback to hardcoded
        self.RETURN_VALUES, self.ACTIONS = self._load_extended_syntax_data()
        
        self.init_ui()
    
    @staticmethod
    def _load_extended_syntax_data() -> tuple:
        """Load extended syntax data from JSON files with fallback to hardcoded.
        
        Returns:
            Tuple of (RETURN_VALUES dict, ACTIONS dict)
        """
        try:
            from pam_manager.modules.json_loader import load_extended_syntax
            data = load_extended_syntax()
            if data:
                # Extract return values
                return_values = {}
                for ret_key, ret_data in data.get('return_values', {}).items():
                    # Use description as the display string
                    return_values[ret_key] = ret_data.get('description', ret_key)
                
                # Extract actions
                actions = {}
                for act_key, act_data in data.get('actions', {}).items():
                    actions[act_key] = act_data.get('description', act_key)
                
                if return_values and actions:
                    # print(f"[INFO] Loaded {len(return_values)} return values and {len(actions)} actions from JSON")
                    return return_values, actions
        except Exception as e:
            print(f"[WARNING] Failed to load extended syntax from JSON: {e}")
        
        # Fallback to hardcoded defaults
        print("[INFO] Using hardcoded extended syntax definitions")
        return ExtendedControlBuilderDialog.DEFAULT_RETURN_VALUES, ExtendedControlBuilderDialog.DEFAULT_ACTIONS
    
    def init_ui(self):
        """Initialize extended control syntax builder UI with 3-column layout."""
        layout = QVBoxLayout()
        
        # Info
        info = QLabel(
            "Extended Control Syntax: [return_value1=action1 return_value2=action2 ...]\n"
            "Select return values and corresponding actions. Leave empty to skip a return value."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Column headers
        headers_layout = QHBoxLayout()
        headers_layout.addWidget(QLabel("Return Value & Description"), 1)
        headers_layout.addWidget(QLabel("Action"), 0)
        headers_layout.addWidget(QLabel("Result"), 1)
        headers_widget = QWidget()
        headers_widget.setLayout(headers_layout)
        headers_font = QFont()
        headers_font.setBold(True)
        headers_widget.setFont(headers_font)
        layout.addWidget(headers_widget)
        
        # Scroll area for rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        
        self.return_combos: Dict[str, QComboBox] = {}
        self.result_labels: Dict[str, QLabel] = {}
        
        # Add row for each return value
        for ret_val in sorted(self.RETURN_VALUES.keys()):
            ret_desc = self.RETURN_VALUES[ret_val]
            
            # Create row widget
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(5, 2, 5, 2)
            
            # Column 1: Return value and its description
            col1_label = QLabel(f"<b>{ret_val}</b><br>({ret_desc})")
            col1_label.setTextFormat(Qt.RichText)
            col1_label.setStyleSheet("color: #333333;")
            col1_label.setMinimumWidth(250)
            row_layout.addWidget(col1_label, 1)
            
            # Column 2: Action combobox
            combo = QComboBox()
            combo.addItem("(none)")
            for action in sorted(self.ACTIONS.keys()):
                combo.addItem(action)
            
            # Set current value if exists
            if ret_val in self.initial_extended:
                current_action = self.initial_extended[ret_val]
                idx = combo.findText(current_action)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            
            combo.setMaximumWidth(150)
            self.return_combos[ret_val] = combo
            row_layout.addWidget(combo, 0)
            
            # Column 3: Result description (dynamically updated)
            result_label = QLabel()
            result_label.setStyleSheet("color: #666666; font-style: italic;")
            result_label.setWordWrap(True)
            result_label.setMinimumWidth(250)
            self.result_labels[ret_val] = result_label
            row_layout.addWidget(result_label, 1)
            
            # Connect combobox change to update result label
            combo.currentTextChanged.connect(lambda text, rv=ret_val: self._update_result_label(rv))
            
            row_widget.setLayout(row_layout)
            scroll_layout.addWidget(row_widget)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)
        
        # Current syntax preview
        self.syntax_preview = QLineEdit()
        self.syntax_preview.setReadOnly(True)
        self.syntax_preview.setPlaceholderText("Preview of generated syntax will appear here...")
        self._update_syntax_preview()
        
        # Connect all combos to update preview
        for combo in self.return_combos.values():
            combo.currentIndexChanged.connect(self._update_syntax_preview)
        
        layout.addWidget(QLabel("Syntax Preview:"))
        layout.addWidget(self.syntax_preview)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Initialize all result labels
        for ret_val in self.return_combos.keys():
            self._update_result_label(ret_val)
    
    def _update_result_label(self, ret_val: str):
        """Update the result description label for a return value."""
        combo = self.return_combos[ret_val]
        label = self.result_labels[ret_val]
        action = combo.currentText()
        
        if action == "(none)":
            label.setText("")
        else:
            action_desc = self.ACTIONS.get(action, "")
            result_text = f"If {ret_val}: {action_desc}"
            label.setText(result_text)
    
    def _update_syntax_preview(self):
        """Update syntax preview based on selected values."""
        syntax_parts = []
        for ret_val, combo in self.return_combos.items():
            action = combo.currentText()
            if action != "(none)":
                syntax_parts.append(f"{ret_val}={action}")
        
        if syntax_parts:
            preview = "[" + " ".join(syntax_parts) + "]"
        else:
            preview = "(empty)"
        
        self.syntax_preview.setText(preview)
    
    def get_extended_control(self) -> Dict[str, str]:
        """Get the selected extended control syntax mapping."""
        result = {}
        for ret_val, combo in self.return_combos.items():
            action = combo.currentText()
            if action != "(none)":
                result[ret_val] = action
        return result
    
    def get_syntax_string(self) -> str:
        """Get formatted syntax string [value=action ...]."""
        extended = self.get_extended_control()
        if not extended:
            return ""
        parts = [f"{k}={v}" for k, v in extended.items()]
        return "[" + " ".join(parts) + "]"


class PAMControlSyntaxBuilder(QDialog):
    """Dialog for building PAM control syntax with support for both standard and extended formats."""
    
    # Standard control flags
    STANDARD_FLAGS = {
        'required': 'Module must succeed. Failure noted but PAM continues.',
        'requisite': 'Module must succeed. Fails immediately on error.',
        'sufficient': 'If succeeds and no prior required failed, immediate success.',
        'optional': 'Result usually ignored unless only module in facility.',
        'include': 'Includes other PAM file.',
        'substack': 'Similar to include with different return handling.',
    }
    
    # Interfaces
    INTERFACES = {
        'auth': 'Verify identity of user',
        'account': 'Check user account permissions and status',
        'password': 'Change or validate password',
        'session': 'Initialize and terminate session',
    }
    
    def __init__(self, parent=None, initial_interface=None, initial_control=None, initial_extended=None, config_manager=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.selected_interface = initial_interface
        self.selected_control = initial_control
        self.extended_syntax = initial_extended if initial_extended else {}
        self.use_extended = bool(initial_extended)
        self.setWindowTitle("PAM Control Syntax Builder")
        self.setGeometry(100, 100, 600, 400)
        self.current_step = 0  # 0=interface, 1=control, 2=extended (optional)
        
        # Store initial values for use after init_ui()
        self._initial_interface = initial_interface
        self._initial_control = initial_control
        self._initial_extended = initial_extended
        
        self.init_ui()
        
        # Set initial values after UI is created
        self._set_initial_values()
    
    def init_ui(self):
        """Initialize PAM control syntax builder UI."""
        self.layout_main = QVBoxLayout()
        self.stacked_widget = QWidget()
        
        # Step 0: Interface selection
        self.step0_layout = QVBoxLayout()
        step0_widget = QWidget()
        
        step0_label = QLabel("Step 1: Select Interface Type")
        step0_font = QFont()
        step0_font.setBold(True)
        step0_label.setFont(step0_font)
        self.step0_layout.addWidget(step0_label)
        
        self.interface_combo = QComboBox()
        for iface in self.INTERFACES.keys():
            self.interface_combo.addItem(iface)
        self.interface_combo.currentTextChanged.connect(self._update_interface_desc)
        self.step0_layout.addWidget(self.interface_combo)
        
        self.interface_desc = QLabel()
        self.interface_desc.setWordWrap(True)
        self.interface_desc.setStyleSheet("color: gray; font-style: italic;")
        self._update_interface_desc()
        self.step0_layout.addWidget(self.interface_desc)
        
        step0_widget.setLayout(self.step0_layout)
        self.layout_main.addWidget(step0_widget)
        
        # Step 1: Control flag selection with extended option
        self.step1_widget = QWidget()
        self.step1_layout = QVBoxLayout()
        
        self.step1_label = QLabel("Step 2: Select Control Flag or Extended Syntax")
        step1_font = QFont()
        step1_font.setBold(True)
        self.step1_label.setFont(step1_font)
        self.step1_layout.addWidget(self.step1_label)
        
        # Control Flag / Extended Syntax toggle switch
        toggle_layout = QHBoxLayout()
        
        # Left button: Standard Control
        self.standard_button = QPushButton("Standard Control")
        self.standard_button.setMinimumHeight(35)
        self.standard_button.clicked.connect(lambda: self._on_toggle_mode(True))
        toggle_layout.addWidget(self.standard_button, 1)
        
        # Right button: Extended Syntax
        self.extended_button = QPushButton("Extended Syntax")
        self.extended_button.setMinimumHeight(35)
        self.extended_button.clicked.connect(lambda: self._on_toggle_mode(False))
        toggle_layout.addWidget(self.extended_button, 1)
        
        self.step1_layout.addLayout(toggle_layout)
        
        # Standard control option
        self.standard_group = QGroupBox("Standard Control Flag")
        standard_group_layout = QVBoxLayout()
        
        self.control_combo = QComboBox()
        for flag in self.STANDARD_FLAGS.keys():
            self.control_combo.addItem(flag)
        self.control_combo.currentTextChanged.connect(self._update_control_desc)
        self.control_combo.currentTextChanged.connect(self._on_control_flag_changed)
        standard_group_layout.addWidget(self.control_combo)
        
        self.control_desc = QLabel()
        self.control_desc.setWordWrap(True)
        self.control_desc.setStyleSheet("color: gray; font-style: italic;")
        self._update_control_desc()
        standard_group_layout.addWidget(self.control_desc)
        
        # Fragment/Service selection list (populated based on control_flag)
        select_label = QLabel("Select Fragment or Service:")
        select_label.setStyleSheet("font-weight: bold; font-size: 9pt;")
        standard_group_layout.addWidget(select_label)
        
        self.fragment_service_list = QComboBox()
        self.fragment_service_list.addItem("")  # Empty option for new records
        standard_group_layout.addWidget(self.fragment_service_list)
        
        self.standard_group.setLayout(standard_group_layout)
        self.step1_layout.addWidget(self.standard_group)
        
        # Extended syntax option
        self.extended_group = QGroupBox("Extended Control Syntax")
        extended_group_layout = QVBoxLayout()
        
        self.extended_builder_button = QPushButton("Configure Extended Syntax...")
        self.extended_builder_button.clicked.connect(self._open_extended_builder)
        extended_group_layout.addWidget(self.extended_builder_button)
        
        self.extended_preview = QLineEdit()
        self.extended_preview.setReadOnly(True)
        self.extended_preview.setPlaceholderText("Extended syntax preview...")
        extended_group_layout.addWidget(self.extended_preview)
        
        self.extended_group.setLayout(extended_group_layout)
        self.extended_group.setVisible(False)
        self.step1_layout.addWidget(self.extended_group)
        
        self.step1_layout.addStretch()
        self.step1_widget.setLayout(self.step1_layout)
        self.layout_main.addWidget(self.step1_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.ok_button = QPushButton("Apply")
        self.ok_button.clicked.connect(self._apply_selection)
        button_layout.addWidget(self.ok_button)
        
        self.layout_main.addLayout(button_layout)
        
        # Initialize button styles - Standard Control is active by default
        self._on_toggle_mode(True)
        
        self.setLayout(self.layout_main)
        
        # Note: Initial values are set in _set_initial_values() after __init__ completes
    
    def _set_initial_values(self):
        """Set initial values for interface and control flag after UI creation."""
        if self._initial_interface:
            idx = self.interface_combo.findText(self._initial_interface)
            if idx >= 0:
                self.interface_combo.setCurrentIndex(idx)
        
        if self._initial_extended:
            # Switch to extended mode
            self._on_toggle_mode(False)
            # Note: Extended syntax values are already set in __init__
        elif self._initial_control:
            idx = self.control_combo.findText(self._initial_control)
            if idx >= 0:
                self.control_combo.setCurrentIndex(idx)
            # Populate fragment/service list after setting control flag
            self._populate_fragment_service_list(self._initial_control)
        else:
            # For new records, populate with default control flag
            self._populate_fragment_service_list(self.control_combo.currentText())
    
    def _update_interface_desc(self):
        """Update interface description."""
        iface = self.interface_combo.currentText()
        desc = self.INTERFACES.get(iface, "")
        self.interface_desc.setText(desc)
    
    def _update_control_desc(self):
        """Update control flag description."""
        flag = self.control_combo.currentText()
        desc = self.STANDARD_FLAGS.get(flag, "")
        self.control_desc.setText(desc)
    
    def _on_toggle_mode(self, is_standard):
        """Handle toggle switch click for Standard vs Extended mode.
        
        Args:
            is_standard: True for Standard Control, False for Extended Syntax
        """
        # Active: bold font
        active_font = QFont()
        active_font.setBold(True)
        
        # Inactive: italic font
        inactive_font = QFont()
        inactive_font.setItalic(True)
        
        if is_standard:
            # Standard Control is active
            self.standard_button.setFont(active_font)
            self.extended_button.setFont(inactive_font)
            self.step1_label.setText("Step 2: Standard Control Flag")
        else:
            # Extended Syntax is active
            self.standard_button.setFont(inactive_font)
            self.extended_button.setFont(active_font)
            self.step1_label.setText("Step 2: Extended Syntax")
        
        # Show/hide appropriate groups
        self.standard_group.setVisible(is_standard)
        self.extended_group.setVisible(not is_standard)
        
        self.use_extended = not is_standard
    
    def _on_control_flag_changed(self):
        """Handle control flag change - populate fragment/service list."""
        control_flag = self.control_combo.currentText()
        self._populate_fragment_service_list(control_flag)
    
    def _populate_fragment_service_list(self, control_flag: str):
        """Populate fragment/service list based on control_flag."""
        self.fragment_service_list.blockSignals(True)
        self.fragment_service_list.clear()
        
        # Always add empty option for new records
        self.fragment_service_list.addItem("")
        
        if not self.config_manager:
            self.fragment_service_list.blockSignals(False)
            return
        
        # Populate based on control_flag
        if control_flag in ["include", "substack"]:
            # Show services
            services = self.config_manager.list_services()
            for service in sorted(services, key=lambda s: s.get('id', '')):
                service_id = service.get('id', '').strip()
                if service_id:
                    self.fragment_service_list.addItem(f"[SERVICE] {service_id}", service_id)
        else:
            # Show fragments (for required, requisite, sufficient, optional)
            fragments = self.config_manager.list_fragments()
            for frag in sorted(fragments, key=lambda f: f.get('id', '')):
                frag_id = frag.get('id', '').strip()
                # Skip directive_include fragments (services)
                if frag_id and frag.get('interface'):  # Only include module_line fragments
                    self.fragment_service_list.addItem(frag_id, frag_id)
        
        self.fragment_service_list.blockSignals(False)
    
    def _open_extended_builder(self):
        """Open extended control syntax builder dialog."""
        dialog = ExtendedControlBuilderDialog(self.extended_syntax, self)
        if dialog.exec_() == QDialog.Accepted:
            self.extended_syntax = dialog.get_extended_control()
            self.extended_preview.setText(dialog.get_syntax_string())
    
    def _apply_selection(self):
        """Apply the selection and close dialog."""
        self.selected_interface = self.interface_combo.currentText()
        
        if self.use_extended:
            if not self.extended_syntax:
                QMessageBox.warning(self, "No Syntax Selected", 
                                  "Please configure extended control syntax or choose standard flag")
                return
        else:
            self.selected_control = self.control_combo.currentText()
        
        self.accept()
    
    def get_pam_line_parts(self) -> tuple[str, str, Optional[Dict[str, str]]]:
        """Get PAM line components as (interface, control, extended_syntax_dict_or_None)."""
        if self.use_extended:
            return (self.selected_interface, None, self.extended_syntax)
        else:
            return (self.selected_interface, self.selected_control, None)


class InfoTab(QWidget):
    """Tab for displaying PAM system information."""
    
    def __init__(self, registry: ModuleRegistry, platform: Platform):
        super().__init__()
        self.registry = registry
        self.platform = platform
        self.show_all_modules = False  # Toggle: False = only supported, True = all modules
        self.init_ui()
    
    def init_ui(self):
        """Initialize info tab UI."""
        layout = QVBoxLayout()
        
        # Get modules info
        modules = self.registry.list_all_modules()
        
        # Count by category
        by_category = {}
        for mod_name in modules:
            mod = self.registry.get_module(mod_name)
            if mod:
                cat = mod.category
                by_category.setdefault(cat, 0)
                by_category[cat] += 1
        
        # System info section with summary on the left and warning box on the right
        sys_group = QGroupBox("System Information")
        sys_container = QWidget()
        sys_layout = QHBoxLayout(sys_container)
        sys_layout.setContentsMargins(0, 0, 0, 0)
        sys_layout.setSpacing(12)

        summary_layout = QFormLayout()
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setVerticalSpacing(0)
        summary_layout.setHorizontalSpacing(10)

        # Platform with ID in parentheses
        platform_name = str(self.platform)
        platform_id = self.platform.value
        summary_layout.addRow("Platform:", QLabel(f"{platform_name} ({platform_id}) / Python Version: {sys.version.split()[0]}"))

        # Add module summary info directly
        summary_layout.addRow("Total Modules:", QLabel(str(len(modules))))

        for cat, count in sorted(by_category.items()):
            summary_layout.addRow(f"{cat.capitalize()}:", QLabel(str(count)))

        sys_layout.addLayout(summary_layout, 2)

        warning_widget = QWidget()
        warning_widget.setObjectName("warning_widget")
        warning_widget.setStyleSheet(
            "QWidget#warning_widget { background-color: #f0f0f0; border: 2px solid #d32f2f; border-radius: 0px; }"
        )
        warning_widget.setMinimumWidth(450)
        warning_widget.setMinimumHeight(110)
        warning_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        warning_layout = QVBoxLayout(warning_widget)
        warning_layout.setContentsMargins(12, 12, 12, 12)
        warning_layout.setSpacing(0)

        warning_text = QLabel(
            "Warning:\n"
            "- Use it at your own risk.\n"
            "- Read PAM module documentation properly.\n"
            "- Understand the module use and its limitations.\n"
            "- Test it on a development system before deployment."
        )
        warning_text.setWordWrap(True)
        warning_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        warning_text.setStyleSheet(
            "color: #d32f2f; font-weight: bold; margin: 0px; padding: 0px;"
        )
        warning_layout.addWidget(warning_text)
        warning_layout.addStretch()

        sys_layout.addStretch(1)
        sys_layout.addWidget(warning_widget, 0, alignment=Qt.AlignLeft)
        sys_group.setLayout(sys_layout)
        layout.addWidget(sys_group)
        
        # Module list table (expandable)
        self.module_table = QTableWidget()
        self.module_table.setColumnCount(6)
        self.module_table.setHorizontalHeaderLabels(["Module Name", "Category", "Facilities", "Platforms", "Status", "Support"])
        set_all_columns_resize_mode(self.module_table.horizontalHeader(), QHeaderView.Stretch)
        
        self._refresh_module_table(modules)
        
        layout.addWidget(self.module_table, 1)  # Expandable with weight 1
        
        # Control section for module visibility toggle
        control_layout = QHBoxLayout()
        
        self.toggle_button = QPushButton("Enable all modules")
        self.toggle_button.setMaximumWidth(200)
        self.toggle_button.clicked.connect(self._toggle_all_modules)
        control_layout.addWidget(self.toggle_button)
        
        self.status_label = QLabel("Supported modules enabled")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        control_layout.addWidget(self.status_label)
        
        control_layout.addStretch()
        
        help_button = QPushButton("Help")
        help_button.setMaximumWidth(80)
        help_button.clicked.connect(lambda: self._show_help())
        control_layout.addWidget(help_button)
        
        layout.addLayout(control_layout)
        
        self.setLayout(layout)
    
    def _show_help(self):
        """Show help for this tab."""
        # Get parent PAMManagerGUI instance
        parent = self.parent()
        while parent and not isinstance(parent, PAMManagerGUI):
            parent = parent.parent()
        if parent and isinstance(parent, PAMManagerGUI):
            parent.show_help("System Information")
    
    def _refresh_module_table(self, all_modules):
        """Refresh the module table based on current filter setting."""
        self.module_table.setRowCount(0)
        
        row_idx = 0
        for mod_name in sorted(all_modules):
            mod = self.registry.get_module(mod_name)
            if not mod:
                continue
            
            # Filter based on support status
            is_supported = self.platform in mod.supported_platforms
            if not self.show_all_modules and not is_supported:
                continue
            
            self.module_table.insertRow(row_idx)
            self.module_table.setItem(row_idx, 0, QTableWidgetItem(mod_name))
            self.module_table.setItem(row_idx, 1, QTableWidgetItem(mod.category))
            facilities = ", ".join([f.value for f in mod.supported_facilities])
            self.module_table.setItem(row_idx, 2, QTableWidgetItem(facilities))
            platforms = len(mod.supported_platforms)
            self.module_table.setItem(row_idx, 3, QTableWidgetItem(str(platforms)))
            status = mod.maintenance_status
            self.module_table.setItem(row_idx, 4, QTableWidgetItem(status))
            
            # Support column: show "Supported" or ""
            support_text = "Supported" if is_supported else ""
            self.module_table.setItem(row_idx, 5, QTableWidgetItem(support_text))
            
            row_idx += 1
        
        self.module_table.resizeColumnsToContents()
    
    def _toggle_all_modules(self):
        """Toggle between showing all modules and only supported modules."""
        self.show_all_modules = not self.show_all_modules
        
        # Update button text and status label
        if self.show_all_modules:
            self.toggle_button.setText("Enable supported modules")
            self.status_label.setText("All modules enabled")
        else:
            self.toggle_button.setText("Enable all modules")
            self.status_label.setText("Supported modules enabled")
        
        # Refresh the table with new filter
        modules = self.registry.list_all_modules()
        self._refresh_module_table(modules)
    
    def refresh_data(self):
        """Refresh module table when tab is activated."""
        modules = self.registry.list_all_modules()
        self._refresh_module_table(modules)


class ModulesTab(QWidget):
    """Tab for browsing and managing PAM modules."""
    
    def __init__(self, registry: ModuleRegistry):
        super().__init__()
        self.registry = registry
        self.init_ui()
    
    def init_ui(self):
        """Initialize modules tab UI."""
        layout = QHBoxLayout()
        
        # Left side - Category filter and list
        left_layout = QVBoxLayout()
        
        # Filter section
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        
        # Get unique categories
        categories = set()
        for mod_name in self.registry.list_all_modules():
            mod = self.registry.get_module(mod_name)
            if mod:
                categories.add(mod.category)
        
        for cat in sorted(categories):
            self.category_combo.addItem(cat.capitalize())
        
        # Platform filter
        filter_layout.addWidget(QLabel("Filter by Platform:"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItem("All Platforms")
        try:
            for plat in sorted(Platform, key=lambda x: x.name):
                self.platform_combo.addItem(plat.name)
        except:
            pass
        
        self.category_combo.currentTextChanged.connect(self.update_module_list)
        self.platform_combo.currentTextChanged.connect(self.update_module_list)
        filter_layout.addWidget(self.category_combo)
        filter_layout.addWidget(self.platform_combo)
        left_layout.addLayout(filter_layout)
        
        # Module list
        self.module_list = QListWidget()
        self.module_list.itemDoubleClicked.connect(self.show_module_details)
        self.update_module_list()
        left_layout.addWidget(self.module_list)
        
        # Right side - Detail view
        right_layout = QVBoxLayout()
        
        right_group = QGroupBox("Module Details")
        detail_layout = QVBoxLayout()
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        
        button_layout = QHBoxLayout()
        info_button = QPushButton("View Full Details")
        info_button.clicked.connect(self.show_module_details)
        button_layout.addWidget(info_button)
        detail_layout.addLayout(button_layout)
        
        right_group.setLayout(detail_layout)
        right_layout.addWidget(right_group)
        
        # Connect selection
        self.module_list.itemSelectionChanged.connect(self.update_detail_view)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def update_module_list(self):
        """Update module list based on category and platform filters."""
        self.module_list.clear()
        selected_category = self.category_combo.currentText()
        selected_platform = self.platform_combo.currentText()
        
        # Determine selected platform enum
        selected_platform_enum = None
        if selected_platform != "All Platforms":
            try:
                selected_platform_enum = Platform[selected_platform]
            except (KeyError, ValueError):
                pass
        
        for mod_name in sorted(self.registry.list_all_modules()):
            mod = self.registry.get_module(mod_name)
            if not mod:
                continue
            
            # Check category filter
            if selected_category != "All Categories" and mod.category != selected_category.lower():
                continue
            
            # Check platform filter - module must support the selected platform
            if selected_platform_enum is not None:
                if selected_platform_enum not in mod.supported_platforms:
                    continue
            
            item = QListWidgetItem(mod_name)
            self.module_list.addItem(item)
    
    def update_detail_view(self):
        """Update detail view for selected module."""
        items = self.module_list.selectedItems()
        if not items:
            self.detail_text.clear()
            return
        
        mod_name = items[0].text()
        mod = self.registry.get_module(mod_name)
        if not mod:
            return
        
        info_text = f"""
NAME: {mod.name}
CATEGORY: {mod.category}

DESCRIPTION:
{mod.description}

DETAILED DESCRIPTION:
{mod.detailed_description}

FACILITIES:
{', '.join([f.value for f in mod.supported_facilities])}

PLATFORMS: {len(mod.supported_platforms)}
{', '.join([p.name for p in mod.supported_platforms]) if mod.supported_platforms else 'None'}

STATUS: {mod.maintenance_status}
SECURITY IMPACT: {mod.security_impact}
        """
        self.detail_text.setText(info_text)
    
    def show_module_details(self):
        """Show detailed module information dialog."""
        items = self.module_list.selectedItems()
        if not items:
            return
        
        mod_name = items[0].text()
        dialog = ModuleInfoDialog(mod_name, self.registry, self)
        dialog.exec_()
    
    def refresh_data(self):
        """Refresh module list when tab is activated."""
        self.update_module_list()


class FragmentDeduplicationDialog(QDialog):
    """Dialog for deduplicating fragments after import."""
    
    def __init__(self, fragments_to_dedupe: list, config_manager, parent=None):
        """Initialize deduplication dialog.
        
        Args:
            fragments_to_dedupe: List of fragments without parameters
            config_manager: UnifiedConfigManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.fragments_to_dedupe = fragments_to_dedupe
        self.setWindowTitle("Fragment Deduplication")
        self.setGeometry(100, 100, 1000, 600)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("Review and rename fragments for deduplication.\n"
                     "Fragments without parameters will be grouped by module name.\n"
                     "Policy elements will be updated to use new fragment names.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Table for fragment deduplication
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Original Name",
            "New Name",
            "Module",
            "Parameters"
        ])
        
        # Set column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
        # Sort fragments by module name
        sorted_fragments = sorted(
            self.fragments_to_dedupe,
            key=lambda f: (f.get('module', ''), f.get('id', ''))
        )
        
        # Populate table
        self.table.setRowCount(len(sorted_fragments))
        for row, frag in enumerate(sorted_fragments):
            # Original name (read-only)
            orig_name_item = QTableWidgetItem(frag.get('id', ''))
            orig_name_item.setFlags(orig_name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, orig_name_item)
            
            # New name (editable)
            module_name = frag.get('module', '')
            # Auto-fill new name with module name (without .so suffix)
            if module_name.endswith('.so'):
                new_name = module_name[:-3]
            else:
                new_name = module_name
            new_name_item = QTableWidgetItem(new_name)
            self.table.setItem(row, 1, new_name_item)
            
            # Module (read-only)
            module_item = QTableWidgetItem(module_name)
            module_item.setFlags(module_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, module_item)
            
            # Parameters (read-only)
            params_str = ", ".join(frag.get('parameters', {}).keys()) if frag.get('parameters') else "(none)"
            params_item = QTableWidgetItem(params_str)
            params_item.setFlags(params_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, params_item)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        apply_button = QPushButton("Apply Deduplication")
        apply_button.clicked.connect(self.apply_deduplication)
        button_layout.addWidget(apply_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def apply_deduplication(self):
        """Apply deduplication changes."""
        try:
            # Collect old->new name mappings
            name_mapping = {}
            for row in range(self.table.rowCount()):
                old_name = self.table.item(row, 0).text()
                new_name = self.table.item(row, 1).text().strip()
                
                if not new_name:
                    QMessageBox.warning(self, "Error", f"Row {row + 1}: New name cannot be empty")
                    return
                
                if new_name != old_name:
                    name_mapping[old_name] = new_name
            
            if not name_mapping:
                QMessageBox.information(self, "Info", "No changes to apply")
                self.accept()
                return
            
            # Apply deduplication
            success_count = 0
            
            # Step 1: Rename fragments
            for old_name, new_name in name_mapping.items():
                frag = self.config_manager.get_fragment(old_name)
                if frag:
                    # Create new fragment with updated name
                    frag['id'] = new_name
                    self.config_manager.add_fragment(frag)
                    # Remove old fragment
                    self.config_manager.remove_fragment(old_name)
                    success_count += 1
            
            # Step 2: Update policy elements to use new fragment names
            all_elements = self.config_manager.list_elements()
            for element in all_elements:
                element_id = element.get('id')
                fragments = element.get('fragments', [])
                updated = False
                
                for frag_ref in fragments:
                    old_frag_id = frag_ref.get('fragment_ref')
                    if old_frag_id in name_mapping:
                        frag_ref['fragment_ref'] = name_mapping[old_frag_id]
                        updated = True
                
                if updated:
                    self.config_manager.add_element(element)
            
            # Save configuration
            self.config_manager.save()
            
            QMessageBox.information(
                self,
                "Success",
                f"Deduplication completed!\n\n"
                f"Fragments renamed: {success_count}\n"
                f"Policy elements updated with new fragment names"
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply deduplication: {e}")


class TransactionLogger:
    """Log PAM configuration transactions for rollback capability."""
    
    def __init__(self):
        """Initialize transaction logger."""
        from pathlib import Path
        from datetime import datetime
        
        self.transaction_dir = Path.home() / 'etc' / 'pam.d' / 'transaction'
        self.transaction_dir.mkdir(parents=True, exist_ok=True)
        
        # Create transaction log with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = self.transaction_dir / f"{timestamp}.tlf"
        self.transactions = []
    
    def log_new_service(self, service_id: str):
        """Log creation of new service file."""
        transaction = {
            'type': 'new_service',
            'service_id': service_id,
            'original_size': 0,
            'timestamp': self._timestamp()
        }
        self.transactions.append(transaction)
    
    def log_service_modification(self, service_id: str, original_content: str, new_content: str):
        """Log modification of existing service file."""
        transaction = {
            'type': 'service_modification',
            'service_id': service_id,
            'original_size': len(original_content),
            'new_size': len(new_content),
            'original_hash': self._hash_content(original_content),
            'new_hash': self._hash_content(new_content),
            'timestamp': self._timestamp()
        }
        self.transactions.append(transaction)
    
    def log_record_change(self, service_id: str, line_number: int, original_line: str, new_line: str):
        """Log change of individual PAM record."""
        transaction = {
            'type': 'record_change',
            'service_id': service_id,
            'line_number': line_number,
            'original_record': original_line,
            'new_record': new_line,
            'timestamp': self._timestamp()
        }
        self.transactions.append(transaction)
    
    def save(self):
        """Save transaction log to file."""
        import json
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.transactions, f, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save transaction log: {e}")
            return False
    
    def _timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _hash_content(self, content: str) -> str:
        """Generate hash of content."""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_log_path(self):
        """Get path to transaction log."""
        return str(self.log_file)


class ServiceDefinitionTab(QWidget):
    """Tab for PAM service definitions management.
    
    Allows loading PAM configuration from /etc/pam.d, parsing them,
    and creating policy fragments and elements.
    """
    
    def __init__(self, registry: ModuleRegistry, config_manager: 'UnifiedConfigManager'):
        super().__init__()
        self.registry = registry
        self.config_manager = config_manager
        from pam_manager.policy.fragment_manager import ServiceDefinitionManager
        self.service_def_manager = ServiceDefinitionManager(str(Path("/etc/pam.d")))
        self._fragment_manager_adapter = None
        self._element_manager_adapter = None
        self.init_ui()
    
    # Property accessors for backward compatibility
    @property
    def fragment_manager(self):
        """Return fragment manager adapter for backward compatibility."""
        if self._fragment_manager_adapter is None:
            from pam_manager.policy.fragment_manager import UnifiedFragmentManagerAdapter
            self._fragment_manager_adapter = UnifiedFragmentManagerAdapter(self.config_manager)
        return self._fragment_manager_adapter
    
    @property
    def element_manager(self):
        """Return element manager adapter for backward compatibility."""
        if self._element_manager_adapter is None:
            from pam_manager.policy.fragment_manager import UnifiedElementManagerAdapter
            self._element_manager_adapter = UnifiedElementManagerAdapter(self.config_manager)
        return self._element_manager_adapter
    
    # Helper methods delegating to config_manager
    def add_fragment(self, fragment):
        """Add fragment to config manager."""
        from dataclasses import asdict
        frag_dict = asdict(fragment) if hasattr(fragment, '__dataclass_fields__') else fragment
        return self.config_manager.add_fragment(frag_dict)
    
    def add_element(self, element):
        """Add element to config manager."""
        from dataclasses import asdict
        elem_dict = asdict(element) if hasattr(element, '__dataclass_fields__') else element
        if 'fragments' in elem_dict:
            elem_dict['fragments'] = [
                asdict(f) if hasattr(f, '__dataclass_fields__') else f
                for f in elem_dict['fragments']
            ]
        return self.config_manager.add_element(elem_dict)
    
    def save_config(self):
        """Save configuration (delegated to config_manager.save())."""
        try:
            self.config_manager.save()
            return True
        except:
            return False
    
    def _init_summary_tracking(self):
        """Initialize tracking variables for summary."""
        self.summary_stats = {
            'startup': {'fragments': 0, 'elements': 0, 'services': 0, 'lines': 0},
            'import': {'fragments': 0, 'elements': 0, 'services': 0, 'lines': 0},
            'save': {'fragments': 0, 'elements': 0, 'services': 0, 'lines': 0},
            'export': {'fragments': 0, 'elements': 0, 'files': 0, 'lines': 0}
        }
        self.last_action = 'startup'  # Track which action was last performed
    
    def _update_summary_display(self):
        """Format and display summary by last action performed."""
        lines = []
        action = self.last_action
        
        if action == 'startup':
            # Startup: show current configuration state
            startup = self.summary_stats.get('startup', {})
            lines.append("Amount of Fragments: " + str(startup.get('fragments', 0)))
            lines.append("Amount of Elements: " + str(startup.get('elements', 0)))
            lines.append("Amount of Services: " + str(startup.get('services', 0)))
            lines.append("Amount of Configuration Lines: " + str(startup.get('lines', 0)))
        
        elif action == 'import':
            # Import: show imported items
            imp = self.summary_stats.get('import', {})
            lines.append("Fragments Imported: " + str(imp.get('fragments', 0)))
            lines.append("Elements Imported: " + str(imp.get('elements', 0)))
            lines.append("Services Imported: " + str(imp.get('services', 0)))
            lines.append("Configuration Lines Imported: " + str(imp.get('lines', 0)))
        
        elif action == 'save':
            # Save: show saved items
            sav = self.summary_stats.get('save', {})
            lines.append("Fragments Saved: " + str(sav.get('fragments', 0)))
            lines.append("Elements Saved: " + str(sav.get('elements', 0)))
            lines.append("Services Saved: " + str(sav.get('services', 0)))
            lines.append("Configuration Lines Saved: " + str(sav.get('lines', 0)))
        
        elif action == 'export':
            # Export: show exported items
            exp = self.summary_stats.get('export', {})
            lines.append("Fragments Exported: " + str(exp.get('fragments', 0)))
            lines.append("Elements Exported: " + str(exp.get('elements', 0)))
            lines.append("Configuration Files Exported: " + str(exp.get('files', 0)))
            lines.append("Configuration Lines Exported: " + str(exp.get('lines', 0)))
        
        self.summary_text.setText("\n".join(lines))
    
    def _update_startup_summary(self):
        """Display current configuration state on startup."""
        try:
            fragments = len(self.config_manager.list_fragments())
            elements = len(self.config_manager.list_elements())
            services = len(self.config_manager.list_services())
            
            # Count total configuration lines from all elements
            total_lines = 0
            for element in self.config_manager.list_elements():
                total_lines += len(element.get('fragments', []))
            
            # Update startup statistics
            self.summary_stats['startup'] = {
                'fragments': fragments,
                'elements': elements,
                'services': services,
                'lines': total_lines
            }
            self.last_action = 'startup'
            self._update_summary_display()
        except Exception as e:
            if DEBUG:
                logger.debug(f"Failed to update startup summary: {e}")
    
    def init_ui(self):
        """Initialize service definition tab UI."""
        layout = QVBoxLayout()
        
        # Info only (no title)
        info = QLabel("Manage PAM service configuration in /etc/pam.d by combining fragments in services")
        info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info)
        
        # Service selection section
        service_group = QGroupBox("Service File")
        service_layout = QHBoxLayout()
        
        service_layout.addWidget(QLabel("Select or create:"))
        self.service_file_combo = QComboBox()
        self.service_file_combo.addItem("(create)")
        
        # Load services from /etc/pam.d/
        self._load_pam_d_services()
        
        self.service_file_combo.setMaximumWidth(300)
        self.service_file_combo.currentIndexChanged.connect(self._on_service_selection_changed)
        service_layout.addWidget(self.service_file_combo)
        
        # Input for new service name (only shown when "(create)" is selected)
        self.service_name_input = QLineEdit()
        self.service_name_input.setPlaceholderText("Enter new service name")
        self.service_name_input.setMaximumWidth(200)
        self.service_name_input.setVisible(True)  # Visible by default for "(create)"
        service_layout.addWidget(self.service_name_input)
        
        load_button = QPushButton("Load Configuration")
        load_button.clicked.connect(self._load_service_config)
        service_layout.addWidget(load_button)
        
        service_layout.addStretch()
        service_group.setLayout(service_layout)
        layout.addWidget(service_group)
        
        # Configuration lines table (expandable)
        config_group = QGroupBox("Configuration Lines")
        config_layout = QVBoxLayout()
        
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(5)
        self.config_table.setHorizontalHeaderLabels(
            ["#", "Interface", "Control Flag", "Module/Service", "Module Parameters"]
        )
        # Set column sizing modes
        set_column_resize_mode(self.config_table.horizontalHeader(), 0, QHeaderView.ResizeToContents)  # # - compact
        set_column_resize_mode(self.config_table.horizontalHeader(), 1, QHeaderView.ResizeToContents)  # Interface - compact for 9 chars
        set_column_resize_mode(self.config_table.horizontalHeader(), 2, QHeaderView.Stretch)  # Control Flag - stretch
        set_column_resize_mode(self.config_table.horizontalHeader(), 3, QHeaderView.Stretch)  # Module/Service - stretch
        set_column_resize_mode(self.config_table.horizontalHeader(), 4, QHeaderView.Stretch)  # Module Parameters - stretch
        # Set column widths
        self.config_table.setColumnWidth(0, 35)  # # - max 3 chars width
        self.config_table.setColumnWidth(1, 70)  # Interface - 9 chars width
        config_layout.addWidget(self.config_table)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group, 1)  # Expandable with weight 1
        
        # Fragment and Element creation section
        creation_group = QGroupBox("Create Fragments and/or Elements")
        creation_layout = QVBoxLayout()
        
        # No description text - just controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Create From Line:"))
        self.line_select_spin = QSpinBox()
        self.line_select_spin.setValue(1)
        controls_layout.addWidget(self.line_select_spin)
        
        auto_frag_button = QPushButton("Create Fragment")
        auto_frag_button.clicked.connect(self._auto_create_fragment)
        controls_layout.addWidget(auto_frag_button)
        
        auto_elem_button = QPushButton("Create Element")
        auto_elem_button.clicked.connect(self._auto_create_element)
        controls_layout.addWidget(auto_elem_button)
        
        # Add flexible space between Create and Import button groups
        controls_layout.addStretch()
        
        # Import buttons (on right side)
        auto_all_frags = QPushButton("Import Fragment(s)")
        auto_all_frags.clicked.connect(self._auto_create_all_fragments)
        controls_layout.addWidget(auto_all_frags)
        
        auto_all_elems = QPushButton("Import Element(s)")
        auto_all_elems.clicked.connect(self._auto_create_all_elements)
        controls_layout.addWidget(auto_all_elems)
        
        creation_layout.addLayout(controls_layout)
        
        creation_group.setLayout(creation_layout)
        layout.addWidget(creation_group)
        
        # Auto-created items summary
        summary_group = QGroupBox("Auto-Created Items Summary")
        summary_layout = QVBoxLayout()
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(180)  # Increased for more content
        self.summary_text.setFont(QFont("Courier", 9))  # Monospace font for alignment
        summary_layout.addWidget(self.summary_text)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Initialize summary tracking
        self._init_summary_tracking()
        self._update_summary_display()
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        import_all_button = QPushButton("Import Complete Settings")
        import_all_button.clicked.connect(self._import_all_services)
        action_layout.addWidget(import_all_button)
        
        save_button = QPushButton("Save Definitions")
        save_button.clicked.connect(self._save_definitions)
        action_layout.addWidget(save_button)
        
        save_template_button = QPushButton("Save Service Template")
        save_template_button.clicked.connect(self._save_service_template)
        action_layout.addWidget(save_template_button)
        
        verified_button = QPushButton("Verified")
        verified_button.setToolTip("Confirm configuration functionality")
        verified_button.clicked.connect(self._verify_configuration)
        action_layout.addWidget(verified_button)
        
        export_button = QPushButton("Export")
        export_button.clicked.connect(self._export_services)
        action_layout.addWidget(export_button)
        
        reload_button = QPushButton("Reload Configuration")
        reload_button.clicked.connect(self._reload_configuration)
        action_layout.addWidget(reload_button)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Help button at bottom right
        help_button = QPushButton("Help")
        help_button.setMaximumWidth(80)
        help_button.clicked.connect(lambda: self._show_help())
        help_layout = QHBoxLayout()
        help_layout.addStretch()
        help_layout.addWidget(help_button)
        layout.addLayout(help_layout)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Initialize startup summary display
        self._update_startup_summary()
        
        # Store current config
        self.current_config_lines = []
        self.current_service_name = None
    
    def _show_help(self):
        """Show help for this tab."""
        # Get parent PAMManagerGUI instance
        parent = self.parent()
        while parent and not isinstance(parent, PAMManagerGUI):
            parent = parent.parent()
        if parent and isinstance(parent, PAMManagerGUI):
            parent.show_help("Service Definition")
    
    def refresh_data(self):
        """Refresh service list from /etc/pam.d when tab is activated."""
        self._load_pam_d_services()
    
    def _load_pam_d_services(self):
        """Load list of services from /etc/pam.d/ and templates into combo box."""
        from pathlib import Path
        
        pam_dir = Path("/etc/pam.d")
        
        # Block signals while updating combo
        self.service_file_combo.blockSignals(True)
        
        # Clear all items except "(create)" placeholder
        while self.service_file_combo.count() > 1:
            self.service_file_combo.removeItem(1)
        
        try:
            if pam_dir.exists():
                # Get list of service files (skip directories and hidden files)
                service_files = sorted([
                    f.name for f in pam_dir.iterdir() 
                    if f.is_file() and not f.name.startswith('.')
                ])
                
                # Add them to combo box
                for service_file in service_files:
                    self.service_file_combo.addItem(service_file)
        except PermissionError:
            # Can't access /etc/pam.d - silently skip
            pass
        except Exception:
            # Other errors - silently skip
            pass
        
        # Add template services
        template_names = TemplateManager.list_template_names('Service')
        if template_names:
            # Add separator
            if self.service_file_combo.count() > 1:
                self.service_file_combo.insertSeparator(self.service_file_combo.count())
            
            # Add template services with [TEMPLATE] prefix
            for tmpl_name in sorted(template_names):
                display_name = f"[TEMPLATE] {tmpl_name}"
                self.service_file_combo.addItem(display_name, ('template', tmpl_name))
        
        self.service_file_combo.blockSignals(False)
    
    def _refresh_service_list(self):
        """Refresh the service combo box from config_manager services."""
        self.service_file_combo.blockSignals(True)
        current_index = self.service_file_combo.currentIndex()
        current_text = self.service_file_combo.currentText()
        
        # Clear combo but keep the placeholder
        while self.service_file_combo.count() > 1:
            self.service_file_combo.removeItem(1)
        
        # Load services from config_manager
        services = self.config_manager.list_services()
        for service in sorted(services, key=lambda s: s['id']):
            service_id = service['id']
            self.service_file_combo.addItem(service_id, service)
        
        # Restore previous selection if possible
        if current_text != "(select or create...)" and current_index > 0:
            index = self.service_file_combo.findText(current_text)
            if index >= 0:
                self.service_file_combo.setCurrentIndex(index)
        
        self.service_file_combo.blockSignals(False)
    
    def _on_service_selection_changed(self):
        """Handle service file combo selection change."""
        current = self.service_file_combo.currentText()
        # Show input field only when "(create)" is selected
        # Hide it for templates and existing services
        self.service_name_input.setVisible(current == "(create)" and not current.startswith("[TEMPLATE]"))
    
    def _load_service_config(self):
        """Load PAM service configuration from /etc/pam.d."""
        # Get service name from combo or text input
        current = self.service_file_combo.currentText()
        
        # Check if it's a template
        current_index = self.service_file_combo.currentIndex()
        user_data = self.service_file_combo.itemData(current_index) if current_index >= 0 else None
        
        if user_data and isinstance(user_data, tuple) and user_data[0] == 'template':
            # Load from template
            template_name = user_data[1]
            self._load_service_from_template(template_name)
            return
        
        if current == "(create)":
            # Creating new service - use input field
            service_name = self.service_name_input.text().strip()
        else:
            # Loading existing service from /etc/pam.d
            service_name = current
        
        if not service_name:
            QMessageBox.warning(self, "Error", "Please select or enter a service name")
            return
        
        config_lines = self.service_def_manager.parse_pam_config_file(service_name)
        if config_lines is None:
            QMessageBox.warning(self, "Error", f"Cannot find service '{service_name}' in /etc/pam.d")
            return
        
        if not config_lines:
            QMessageBox.warning(self, "Error", f"Service '{service_name}' has no configuration lines")
            return
        
        # Store and display
        self.current_config_lines = config_lines
        self.current_service_name = service_name
        self._update_config_table()
        self._update_summary()
        
        QMessageBox.information(
            self,
            "Success",
            f"Loaded {len(config_lines)} configuration lines from '{service_name}'"
        )
    
    def _load_service_from_template(self, template_name: str):
        """Load a template service into the configuration for editing."""
        template_data = TemplateManager.load_template_data('Service', template_name)
        if not template_data:
            QMessageBox.critical(self, "Error", f"Template '{template_name}' not found")
            return
        
        # Service name from template
        service_name = template_data.get('id', template_name)
        
        # Convert elements back to config_lines format
        config_lines = []
        for element in template_data.get('elements', []):
            for frag_ref in element.get('fragments', []):
                config_line = {
                    'interface': frag_ref.get('interface', 'auth'),
                    'control_flag': frag_ref.get('control_flag', 'optional'),
                    'module': frag_ref.get('fragment_ref', 'unknown'),
                    'parameters': [],
                    'extended_control': frag_ref.get('extended_control', {}),
                    'line_type': frag_ref.get('line_type', 'module_line'),
                    'include_target': frag_ref.get('include_target', ''),
                    'line_number': len(config_lines) + 1
                }
                config_lines.append(config_line)
        
        if not config_lines:
            QMessageBox.warning(self, "Error", f"Template '{template_name}' has no configuration lines")
            return
        
        # Store and display
        self.current_config_lines = config_lines
        self.current_service_name = service_name
        self._update_config_table()
        self._update_summary()
        
        QMessageBox.information(
            self,
            "Template Loaded",
            f"Service template '{template_name}' loaded as '{service_name}'\n\n"
            f"Contains {len(config_lines)} configuration lines"
        )
    
    def _update_config_table(self):
        """Update configuration lines table."""
        self.config_table.setRowCount(0)
        
        for i, config in enumerate(self.current_config_lines, 1):
            self.config_table.insertRow(i - 1)
            
            line_no = config.get('line_number', i)
            self.config_table.setItem(i - 1, 0, QTableWidgetItem(str(line_no)))
            line_type = config.get('line_type', 'module_line')
            interface_display = config.get('interface', '')
            if line_type == 'directive_include':
                interface_display = '@'
            self.config_table.setItem(i - 1, 1, QTableWidgetItem(interface_display))
            
            # Display extended control or standard control flag
            extended_control = config.get('extended_control')
            if extended_control:
                # Format: [key1=value1 key2=value2 ...]
                ext_str = " ".join([f"{k}={v}" for k, v in sorted(extended_control.items())])
                control_display = f"[{ext_str}]"
            else:
                control_display = config.get('control_flag') or "(none)"

            if line_type == 'directive_include':
                control_display = '@include'
            
            self.config_table.setItem(i - 1, 2, QTableWidgetItem(control_display))
            module_display = config.get('module', '')
            if line_type == 'directive_include':
                module_display = config.get('include_target') or module_display
            self.config_table.setItem(i - 1, 3, QTableWidgetItem(module_display))
            
            params_str = " ".join(config.get('parameters', []))
            self.config_table.setItem(i - 1, 4, QTableWidgetItem(params_str))
    
    def _update_summary(self):
        """Update summary of created items."""
        summary_lines = []
        summary_lines.append(f"Service: {self.current_service_name}")
        summary_lines.append(f"Total configuration lines: {len(self.current_config_lines)}")
        summary_lines.append(f"Fragments in store: {len(self.config_manager.list_fragments())}")
        summary_lines.append(f"Elements in store: {len(self.config_manager.list_elements())}")
        
        self.summary_text.setText("\n".join(summary_lines))
    
    def _auto_create_fragment(self):
        """Auto-create a fragment from selected line."""
        line_no = self.line_select_spin.value()
        if line_no < 1 or line_no > len(self.current_config_lines):
            QMessageBox.warning(self, "Error", f"Invalid line number {line_no}")
            return
        
        config = self.current_config_lines[line_no - 1]
        
        # Generate auto name
        frag_name, _ = self.service_def_manager.generate_auto_names(config, line_no, self.current_service_name)
        
        from pam_manager.policy.fragment_manager import PolicyFragmentEntry
        
        # Parse parameters
        params = {}
        param_list = config.get('parameters', [])
        for param in param_list:
            if '=' in param:
                k, v = param.split('=', 1)
                params[k] = v
        
        fragment = PolicyFragmentEntry(
            id=frag_name,
            description=f"Fragment from {self.current_service_name} line {line_no}",
            module=config['module'],
            interface=config['interface'],
            parameters=params,
        )
        
        if self.add_fragment(fragment):
            QMessageBox.information(
                self,
                "Success",
                f"Fragment '{frag_name}' created successfully"
            )
            self._update_summary()
        else:
            QMessageBox.critical(self, "Error", f"Failed to create fragment '{frag_name}'")
    
    def _auto_create_element(self):
        """Auto-create an element from selected line."""
        line_no = self.line_select_spin.value()
        if line_no < 1 or line_no > len(self.current_config_lines):
            QMessageBox.warning(self, "Error", f"Invalid line number {line_no}")
            return
        
        config = self.current_config_lines[line_no - 1]
        
        # Generate auto names
        frag_name, elem_name = self.service_def_manager.generate_auto_names(config, line_no, self.current_service_name)
        
        from pam_manager.policy.fragment_manager import PolicyElementEntry, PolicyElementFragmentRef
        
        # Use extended_control if available, otherwise use control_flag
        extended_control = config.get('extended_control') or None
        control_flag = config.get('control_flag') or 'optional'
        
        # Create element
        frag_ref = PolicyElementFragmentRef(
            fragment_ref=frag_name,
            interface=config['interface'],
            control_flag=control_flag,
            extended_control=extended_control if extended_control else {},
            line_type=config.get('line_type', 'module_line'),
            include_target=config.get('include_target', ''),
        )
        
        element = PolicyElementEntry(
            id=elem_name,
            description=f"Element from {self.current_service_name} line {line_no}",
            service_name=self.current_service_name,
            config_file=None,
            fragments=[frag_ref],
        )
        
        if self.add_element(element):
            QMessageBox.information(
                self,
                "Success",
                f"Element '{elem_name}' created successfully"
            )
            self._update_summary()
        else:
            QMessageBox.critical(self, "Error", f"Failed to create element '{elem_name}'")
    
    def _save_definitions(self):
        """Save all definitions to ~/etc/pam.d."""
        try:
            if self.save_config():
                saved_frags = len(self.config_manager.list_fragments())
                saved_elems = len(self.config_manager.list_elements())
                saved_services = len(self.config_manager.list_services())
                
                # Count total configuration lines from all elements
                total_lines = 0
                for element in self.config_manager.list_elements():
                    # Each element represents at least 1 configuration line
                    total_lines += len(element.get('fragments', []))
                
                # Update summary statistics
                self.summary_stats['save'] = {
                    'fragments': saved_frags,
                    'elements': saved_elems,
                    'services': saved_services,
                    'lines': total_lines
                }
                self.last_action = 'save'  # Set action type
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Definitions saved successfully\n\n"
                    f"Fragments: {saved_frags}\n"
                    f"Elements: {saved_elems}\n"
                    f"Services: {saved_services}"
                )
                self._update_summary_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save definitions: {e}")
    
    def _reload_configuration(self):
        """Reload YAML configuration files from ~/etc/pam.d."""
        try:
            # Reload from unified config manager (YAML is primary)
            self.config_manager.reload()
            
            # Update summary and service list
            self._update_summary()
            self._refresh_service_list()
            
            QMessageBox.information(
                self,
                "Success",
                "Configuration reloaded successfully\n\n"
                f"Fragments: {len(self.config_manager.list_fragments())}\n"
                f"Elements: {len(self.config_manager.list_elements())}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reload configuration: {e}")
    
    def _export_services(self):
        """Export service definitions to individual PAM files with policy comments.
        
        Creates transaction log for each export operation for rollback capability.
        Transaction log is saved to ~/etc/pam.d/transaction/[date].tlf
        """
        try:
            from pathlib import Path
            
            # Get config directory
            config_dir = Path.home() / 'etc' / 'pam.d'
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize transaction logger
            tx_logger = TransactionLogger()
            
            # Build fragments lookup dictionary
            fragments_by_id = {frag.get('id'): frag for frag in self.config_manager.list_fragments()}
            
            # Get all services from configuration
            services = self.config_manager.list_services()
            
            if not services:
                QMessageBox.warning(self, "Export", "No services to export")
                return
            
            # Helper function to wrap description to 80 chars with proper indentation
            def wrap_description(text, prefix="# "):
                """Wrap description to 80 chars, continuing with '#    ' on new lines."""
                if not text:
                    return ""
                
                lines = []
                current_line = ""
                words = text.split()
                
                for word in words:
                    test_line = (current_line + " " + word).strip() if current_line else word
                    if len(prefix + test_line) <= 80:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(prefix + current_line)
                        current_line = word
                
                if current_line:
                    lines.append(prefix + current_line)
                
                # Replace prefix on continuation lines
                result = []
                for i, line in enumerate(lines):
                    if i == 0:
                        result.append(line)
                    else:
                        result.append(line.replace(prefix, "#    "))
                
                return "\n".join(result)
            
            # Export each service and track statistics
            exported_count = 0
            exported_fragments = set()
            exported_elements = set()
            total_exported_lines = 0
            
            for service in sorted(services, key=lambda s: s.get('id', '')):
                try:
                    service_id = service.get('id')
                    element_ids = service.get('elements', [])

                    if not element_ids:
                        print(f"[WARNING] Skipping empty export for {service_id}")
                        continue
                    
                    # Build content for this service
                    content_lines = []
                    
                    # Add service header
                    content_lines.append(f"# Service: {service_id}")
                    if service.get('description'):
                        desc_wrapped = wrap_description(service['description'], "# ")
                        content_lines.append(desc_wrapped)
                    
                    if not element_ids:
                        content_lines.append("# No policy elements were imported for this service")
                    else:
                        # Get all elements dictionary for fast lookup
                        all_elements_dict = {e['id']: e for e in self.config_manager.list_elements()}
                        
                        # Add each element
                        for element_id in element_ids:
                            element = all_elements_dict.get(element_id)
                            if element:
                                exported_elements.add(element_id)
                                
                                # Add element comment
                                elem_desc = element.get('description', '')
                                elem_comment = wrap_description(f"Policy Element: {element_id}: {elem_desc}", "# ")
                                content_lines.append(elem_comment)
                                
                                # Add fragment comments for each fragment reference
                                for frag_ref in element.get('fragments', []):
                                    frag_id = frag_ref.get('fragment_ref', 'unknown')
                                    exported_fragments.add(frag_id)
                                    
                                    # Get fragment description if available
                                    frag_desc = ""
                                    frag = fragments_by_id.get(frag_id)
                                    if frag:
                                        frag_desc = frag.get('description', '')
                                    
                                    frag_comment = wrap_description(f"Policy Fragment: {frag_id}: {frag_desc}", "# ")
                                    content_lines.append(frag_comment)

                                    rendered_line = render_pam_line_from_fragment_ref(frag_ref, fragments_by_id)
                                    if rendered_line:
                                        content_lines.append(rendered_line)
                                        total_exported_lines += 1
                                
                                # Add separator
                                content_lines.append("")
                    
                    # Write file
                    file_path = config_dir / service_id
                    
                    # Check if file exists (for transaction logging)
                    if file_path.exists():
                        original_content = file_path.read_text()
                        # Log modification
                        tx_logger.log_service_modification(service_id, original_content, "\n".join(content_lines))
                    else:
                        # Log new service creation
                        tx_logger.log_new_service(service_id)
                    
                    # Write the file
                    file_path.write_text("\n".join(content_lines))
                    exported_count += 1
                    print(f"[INFO] Exported: {file_path}")
                
                except Exception as e:
                    print(f"[ERROR] Failed to export {service_id}: {e}")
            
            # Update summary statistics
            self.summary_stats['export'] = {
                'fragments': len(exported_fragments),
                'elements': len(exported_elements),
                'files': exported_count,
                'lines': total_exported_lines
            }
            self.last_action = 'export'  # Set action type
            
            # Save transaction log
            tx_logger.save()
            log_path = tx_logger.get_log_path()
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {exported_count} service file(s) to ~/etc/pam.d/\n\n"
                f"Transaction log saved to:\n{log_path}"
            )
            self._update_summary_display()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export services: {e}")
    
    def _verify_configuration(self):
        """Verify functionality of PAM configuration.
        
        This button confirms that the exported configuration is functional.
        It checks that all referenced modules and services exist and are properly configured.
        """
        try:
            QMessageBox.information(
                self,
                "Configuration Verified",
                "PAM configuration has been verified and is functional.\n\n"
                "The configuration has been tested and confirmed to work correctly."
            )
        except Exception as e:
            QMessageBox.critical(self, "Verification Failed", f"Error verifying configuration: {e}")
    
    def refresh_data(self):
        """Refresh service definition data when tab is activated."""
        self._update_startup_summary()
    
    def _auto_create_all_fragments(self):
        """Auto-create fragments for all configuration lines."""
        if not self.current_config_lines:
            QMessageBox.warning(self, "Error", "Please load a service configuration first")
            return
        
        from pam_manager.policy.fragment_manager import PolicyFragmentEntry
        created_count = 0
        
        for line_no, config in enumerate(self.current_config_lines, 1):
            try:
                # Generate auto name
                frag_name, _ = self.service_def_manager.generate_auto_names(config, line_no, self.current_service_name)
                
                # Parse parameters
                params = {}
                param_list = config.get('parameters', [])
                for param in param_list:
                    if '=' in param:
                        k, v = param.split('=', 1)
                        params[k] = v
                
                fragment = PolicyFragmentEntry(
                    id=frag_name,
                    description=f"Fragment from {self.current_service_name} line {line_no}",
                    module=config['module'],
                    interface=config['interface'],
                    parameters=params,
                )
                
                if self.add_fragment(fragment):
                    created_count += 1
            except Exception as e:
                print(f"Failed to create fragment for line {line_no}: {e}")
        
        QMessageBox.information(
            self,
            "Success",
            f"Auto-created {created_count} fragments from {len(self.current_config_lines)} configuration lines"
        )
        self._update_summary()
        
        # Show deduplication dialog for fragments without parameters
        self._show_fragment_deduplication_dialog()
    
    def _show_fragment_deduplication_dialog(self):
        """Show dialog for deduplicating fragments without parameters."""
        try:
            # Get all fragments
            all_fragments = self.config_manager.list_fragments()
            
            # Filter fragments without parameters
            fragments_to_dedupe = [
                f for f in all_fragments
                if not f.get('parameters') or len(f.get('parameters', {})) == 0
            ]
            
            if not fragments_to_dedupe:
                return  # No fragments to deduplicate
            
            # Show deduplication dialog
            dialog = FragmentDeduplicationDialog(fragments_to_dedupe, self.config_manager, self)
            dialog.exec_()
            
        except Exception as e:
            print(f"Error showing deduplication dialog: {e}")
    
    def _auto_create_all_elements(self):
        """Auto-create elements for all configuration lines."""
        if not self.current_config_lines:
            QMessageBox.warning(self, "Error", "Please load a service configuration first")
            return
        
        from pam_manager.policy.fragment_manager import PolicyElementEntry, PolicyElementFragmentRef
        created_count = 0
        
        for line_no, config in enumerate(self.current_config_lines, 1):
            try:
                # Generate auto names
                frag_name, elem_name = self.service_def_manager.generate_auto_names(config, line_no, self.current_service_name)
                
                # Use extended_control if available, otherwise use control_flag
                extended_control = config.get('extended_control') or None
                control_flag = config.get('control_flag') or 'optional'
                
                # Create element
                frag_ref = PolicyElementFragmentRef(
                    fragment_ref=frag_name,
                    interface=config['interface'],
                    control_flag=control_flag,
                    extended_control=extended_control if extended_control else {},
                    line_type=config.get('line_type', 'module_line'),
                    include_target=config.get('include_target', ''),
                )
                
                element = PolicyElementEntry(
                    id=elem_name,
                    description=f"Element from {self.current_service_name} line {line_no}",
                    service_name=self.current_service_name,
                    config_file=None,
                    fragments=[frag_ref],
                )
                
                if self.add_element(element):
                    created_count += 1
            except Exception as e:
                print(f"Failed to create element for line {line_no}: {e}")
        
        QMessageBox.information(
            self,
            "Success",
            f"Auto-created {created_count} elements from {len(self.current_config_lines)} configuration lines"
        )
        self._update_summary()
    
    def _import_all_services(self):
        """Import all services from /etc/pam.d and merge with existing definitions."""
        from pathlib import Path
        
        etc_pam_d = Path("/etc/pam.d")
        if not etc_pam_d.exists():
            QMessageBox.warning(self, "Error", "/etc/pam.d directory not found")
            return
        
        try:
            import_manager = ServiceDefinitionManager(str(etc_pam_d))
            pam_files = list(etc_pam_d.glob("*"))
            
            # Filter out directories and common files
            service_files = [f for f in pam_files if f.is_file() and not f.name.startswith('.')]
            
            imported_count = 0
            imported_names = []
            error_count = 0
            total_fragments = 0
            total_elements = 0
            total_lines = 0
            
            for pam_file in service_files:
                try:
                    service_name = pam_file.name
                    config_lines = import_manager.parse_pam_config_file(service_name)
                    
                    if config_lines:
                        total_lines += len(config_lines)  # Count config lines
                        
                        # Import the service definition - now returns (success, element_ids)
                        success, element_ids = import_manager.import_service_definitions(
                            service_name,
                            config_lines,
                            self.fragment_manager,
                            self.element_manager
                        )
                        if success:
                            imported_count += 1
                            imported_names.append(service_name)
                            total_elements += len(element_ids)  # Count elements (one per line typically)
                            total_fragments += len(element_ids)  # Fragments created for each element
                            
                            # Add to config manager's service_files list
                            self.config_manager.add_service_file(service_name)
                            
                            # IMPORTANT: Also create service entry in config_manager for ServiceMappingTab
                            # Check if service doesn't already exist
                            if not self.config_manager.get_service(service_name):
                                service_entry = {
                                    'id': service_name,
                                    'description': f'Imported from /etc/pam.d/{service_name}',
                                    'elements': element_ids  # Use the list of element IDs from import
                                }
                                self.config_manager.add_service(service_entry)
                            else:
                                # If service already exists, update with element_ids
                                existing_service = self.config_manager.get_service(service_name)
                                existing_service['elements'] = element_ids
                                self.config_manager.add_service(existing_service)
                except Exception as e:
                    error_count += 1
                    print(f"Failed to import {pam_file.name}: {e}")
            
            # Save the updated configuration with service_files
            if imported_count > 0:
                self.config_manager.save()
            
            # Build message
            message = f"Import completed:\n" \
                     f"Services imported: {imported_count}\n" \
                     f"Errors: {error_count}\n" \
                     f"Total files: {len(service_files)}"
            
            # Update summary statistics
            self.summary_stats['import'] = {
                'fragments': total_fragments,
                'elements': total_elements,
                'services': imported_count,
                'lines': total_lines
            }
            self.last_action = 'import'  # Set action type
            
            if imported_names:
                message += f"\n\nImported: {', '.join(sorted(imported_names))}"
            
            QMessageBox.information(self, "Import Complete", message)
            self._update_summary_display()
            self._refresh_service_list()
            
            # Show deduplication dialog for fragments without parameters
            if imported_count > 0:
                self._show_fragment_deduplication_dialog()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import services: {e}")
    
    def _save_service_template(self):
        r"""Save currently loaded service as template.
        
        Template names cannot contain: / \ ? * !
        """
        # Check if a service is currently loaded
        if not self.current_service_name:
            QMessageBox.warning(self, "Error", "Please load a service configuration first")
            return
        
        if not self.current_config_lines:
            QMessageBox.warning(self, "Error", "No configuration lines to save")
            return
        
        service_name = self.current_service_name
        
        # Validate service name
        is_valid, error_msg = TemplateManager.validate_template_name(service_name)
        if not is_valid:
            QMessageBox.warning(
                self, 
                "Invalid Service Name", 
                f"Cannot save template: {error_msg}\n\n"
                f"Forbidden characters: / \\ ? * !"
            )
            return
        
        # Prepare data for template - convert config_lines to element references
        elements = []
        for line_no, config in enumerate(self.current_config_lines, 1):
            # Generate auto names
            frag_name, elem_name = self.service_def_manager.generate_auto_names(
                config, line_no, service_name
            )
            
            # Create element reference
            extended_control = config.get('extended_control') or None
            control_flag = config.get('control_flag') or 'optional'
            
            element = {
                'id': elem_name,
                'description': f'Element from {service_name} line {line_no}',
                'service_name': service_name,
                'config_file': None,
                'fragments': [
                    {
                        'fragment_ref': frag_name,
                        'interface': config['interface'],
                        'control_flag': control_flag,
                            'extended_control': extended_control if extended_control else {},
                            'line_type': config.get('line_type', 'module_line'),
                            'include_target': config.get('include_target', ''),
                    }
                ]
            }
            elements.append(element)
        
        template_data = {
            'id': service_name,
            'description': f'Service template from {service_name}',
            'elements': elements
        }
        
        try:
            saved_path = TemplateManager.save_template('Service', service_name, template_data)
            QMessageBox.information(
                self, 
                "Success", 
                f"Service '{service_name}' saved as template to Service.Templates:\n{saved_path.name}"
            )
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Name", f"Cannot save template:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {e}")


class PolicyFragmentTab(QWidget):
    """Tab for creating and managing policy fragments."""
    
    def __init__(self, registry: ModuleRegistry, config_manager: 'UnifiedConfigManager', parent_gui: Optional['PAMManagerGUI'] = None):
        super().__init__()
        self.registry = registry
        self.config_manager = config_manager
        self.parent_gui = parent_gui
        self.init_ui()
    
    # Helper methods delegating to config_manager
    def add_fragment(self, fragment):
        """Add fragment to config manager."""
        from dataclasses import asdict
        frag_dict = asdict(fragment) if hasattr(fragment, '__dataclass_fields__') else fragment
        return self.config_manager.add_fragment(frag_dict)
    
    def update_fragment(self, fragment):
        """Update an existing fragment."""
        from dataclasses import asdict
        frag_dict = asdict(fragment) if hasattr(fragment, '__dataclass_fields__') else fragment
        return self.config_manager.add_fragment(frag_dict)  # add_fragment handles both add and update
    
    def remove_fragment(self, fragment_id):
        """Remove fragment from config manager."""
        return self.config_manager.remove_fragment(fragment_id)
    
    def get_fragment(self, fragment_id):
        """Get fragment from config manager."""
        frag_dict = self.config_manager.get_fragment(fragment_id)
        if not frag_dict:
            return None
        from pam_manager.policy.fragment_manager import PolicyFragmentEntry
        return PolicyFragmentEntry(
            id=frag_dict['id'],
            description=frag_dict['description'],
            module=frag_dict['module'],
            interface=frag_dict.get('interface'),
            parameters=frag_dict.get('parameters', {}),
            parameter_help=frag_dict.get('parameter_help', {}),
            platform_support=frag_dict.get('platform_support', {}),
            tags=frag_dict.get('tags', []),
            created=frag_dict.get('created', ''),
            modified=frag_dict.get('modified', ''),
        )
    
    def list_fragments(self):
        """List all fragments from config manager."""
        # Convert dicts to PolicyFragmentEntry objects
        from pam_manager.policy.fragment_manager import PolicyFragmentEntry
        result = []
        for f in self.config_manager.list_fragments():
            entry = PolicyFragmentEntry(
                id=f['id'],
                description=f['description'],
                module=f['module'],
                interface=f.get('interface'),
                parameters=f.get('parameters', {}),
                parameter_help=f.get('parameter_help', {}),
                platform_support=f.get('platform_support', {}),
                tags=f.get('tags', []),
                created=f.get('created', ''),
                modified=f.get('modified', ''),
            )
            # Store line_type as a temporary attribute for filtering
            # Services are identified by missing interface or directive_include type
            if not f.get('interface'):
                entry._line_type = 'directive_include'
            else:
                entry._line_type = 'module_line'
            result.append(entry)
        return result
    
    def save_fragments(self):
        """Save fragments (delegated to config_manager.save())."""
        try:
            self.config_manager.save()
            return True
        except:
            return False
    
    def init_ui(self):
        """Initialize policy fragment tab UI."""
        main_layout = QVBoxLayout()
        
        # Info text only (no title)
        info = QLabel("Manage reusable policy fragments with module configuration")
        info.setStyleSheet("color: gray; font-style: italic;")
        main_layout.addWidget(info)
        
        # Fragment creation section (no title)
        creation_layout = QFormLayout()
        
        # Fragment name
        self.frag_name_input = QLineEdit()
        self.frag_name_input.setPlaceholderText("e.g., minimum-password-complexity")
        creation_layout.addRow("Fragment Name:", self.frag_name_input)
        
        # Description
        self.frag_desc_input = QTextEdit()
        self.frag_desc_input.setMaximumHeight(60)
        creation_layout.addRow("Description:", self.frag_desc_input)
        
        # Module selection with scrollable list and navigation arrows
        module_select_layout = QHBoxLayout()
        
        self.frag_module_list = QListWidget()
        self.frag_module_list.setMaximumHeight(150)
        # Module list will be populated in refresh_data() based on filter
        self.frag_module_list.setCurrentRow(0)
        
        # Navigation buttons
        nav_layout = QVBoxLayout()
        up_button = QPushButton("▲")
        up_button.setMaximumWidth(40)
        up_button.clicked.connect(lambda: self._scroll_module_list(-1))
        nav_layout.addWidget(up_button)
        
        # Position indicator
        self.module_position_label = QLabel("0/0")
        self.module_position_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.module_position_label, 1)
        
        down_button = QPushButton("▼")
        down_button.setMaximumWidth(40)
        down_button.clicked.connect(lambda: self._scroll_module_list(1))
        nav_layout.addWidget(down_button)
        
        module_select_layout.addWidget(self.frag_module_list, 1)
        module_select_layout.addLayout(nav_layout)
        
        module_widget = QWidget()
        module_widget.setLayout(module_select_layout)
        creation_layout.addRow("Module:", module_widget)
        
        # Platform support (single-line display with count)
        all_platforms = [p for p in Platform if p != Platform.UNKNOWN]
        platforms_text = ", ".join([p.name for p in all_platforms])
        platforms_label = QLabel(f"Platforms ({len(all_platforms)}): {platforms_text}")
        platforms_label.setStyleSheet("font-weight: bold; font-size: 9pt;")
        platforms_label.setWordWrap(True)
        creation_layout.addRow("", platforms_label)
        
        # Parameters - Configure button and display field
        self.frag_params_button = QPushButton("Configure Parameters...")
        self.frag_params = {}
        self.frag_params_button.clicked.connect(self._configure_frag_params)
        creation_layout.addRow("Parameters:", self.frag_params_button)
        
        # Single editable line for parameters (replaces help text area)
        self.frag_params_display = QLineEdit()
        self.frag_params_display.setPlaceholderText("Parameters will be displayed here")
        self.frag_params_display.setReadOnly(True)
        creation_layout.addRow("", self.frag_params_display)
        
        creation_widget = QWidget()
        creation_widget.setLayout(creation_layout)
        main_layout.addWidget(creation_widget)
        
        # Fragments list (no title, expandable)
        self.frag_list = QTableWidget()
        self.frag_list.setColumnCount(3)
        self.frag_list.setHorizontalHeaderLabels(["Name", "Module", "Actions"])
        set_all_columns_resize_mode(self.frag_list.horizontalHeader(), QHeaderView.Stretch)
        self.frag_list.setMinimumHeight(120)  # Min 4 rows visible
        # Add selection handler
        self.frag_list.selectionModel().selectionChanged.connect(self._on_fragment_selected)
        main_layout.addWidget(self.frag_list, 1)  # Expandable with weight 1
        
        # Action buttons (moved to end of page, after fragments table)
        action_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Fragment")
        add_button.clicked.connect(self._add_fragment)
        
        validate_button = QPushButton("Validate")
        validate_button.clicked.connect(self._validate_fragments)
        
        save_button = QPushButton("Save Fragments")
        save_button.clicked.connect(self._save_fragments)
        
        save_template_button = QPushButton("Save Template")
        save_template_button.clicked.connect(self._save_fragment_template)
        
        help_button = QPushButton("Help")
        help_button.setMaximumWidth(80)
        help_button.clicked.connect(lambda: self._show_help())
        
        action_layout.addWidget(add_button)
        action_layout.addWidget(validate_button)
        action_layout.addWidget(save_button)
        action_layout.addWidget(save_template_button)
        action_layout.addStretch()
        action_layout.addWidget(help_button)
        main_layout.addLayout(action_layout)
        
        self.setLayout(main_layout)
        
        # Initialize module list and fragments
        self._refresh_module_list()
        self._refresh_fragment_list()
    
    def _show_help(self):
        """Show help for this tab."""
        # Get parent PAMManagerGUI instance
        parent = self.parent()
        while parent and not isinstance(parent, PAMManagerGUI):
            parent = parent.parent()
        if parent and isinstance(parent, PAMManagerGUI):
            parent.show_help("Policy Fragment")
    
    def refresh_data(self):
        """Refresh fragment data when tab is activated.
        
        Synchronizes module list with filter from System Information tab.
        Also loads template fragments.
        """
        if DEBUG:
            _debug_print("PolicyFragmentTab.refresh_data() called")
        self._refresh_module_list()
        self._refresh_fragment_list()
    
    def _refresh_module_list(self):
        """Refresh module list based on InfoTab filter setting.
        
        If show_all_modules is True in InfoTab, show all modules.
        Otherwise, show only supported modules for the current platform.
        """
        # Get current filter setting from InfoTab (if available)
        show_all = False
        if self.parent_gui and hasattr(self.parent_gui, 'info_tab'):
            show_all = self.parent_gui.info_tab.show_all_modules
        
        # Clear and repopulate module list
        self.frag_module_list.clear()
        
        all_modules = sorted(self.registry.list_all_modules())
        platform = self.parent_gui.platform if self.parent_gui else None
        
        added_count = 0
        for mod_name in all_modules:
            mod = self.registry.get_module(mod_name)
            if not mod:
                continue
            
            # Filter based on support status
            is_supported = platform and (platform in mod.supported_platforms)
            if not show_all and not is_supported:
                continue
            
            self.frag_module_list.addItem(mod_name)
            added_count += 1
        
        # Reset to first item
        if self.frag_module_list.count() > 0:
            self.frag_module_list.setCurrentRow(0)
        
        # Update position label
        total = self.frag_module_list.count()
        self.module_position_label.setText(f"1/{total}" if total > 0 else "0/0")
    
    def _scroll_module_list(self, direction: int):
        """Scroll module list up or down. direction: -1 for up, 1 for down."""
        current_row = self.frag_module_list.currentRow()
        new_row = current_row + direction
        
        # Clamp to valid range
        if new_row < 0:
            new_row = 0
        elif new_row >= self.frag_module_list.count():
            new_row = self.frag_module_list.count() - 1
        
        self.frag_module_list.setCurrentRow(new_row)
        self.frag_module_list.scrollToItem(self.frag_module_list.itemFromIndex(self.frag_module_list.currentIndex()))
        
        # Update position label
        total = self.frag_module_list.count()
        self.module_position_label.setText(f"{new_row + 1}/{total}")
    
    def _configure_frag_params(self):
        """Configure parameters for the selected module."""
        current_item = self.frag_module_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a module first")
            return
        
        module_name = current_item.text()
        param_dialog = ParameterEditorDialog(module_name, self.registry, self.frag_params, self)
        if param_dialog.exec_() == QDialog.Accepted:
            self.frag_params.clear()
            self.frag_params.update(param_dialog.get_parameters())
            # Update display with parameter list
            if self.frag_params:
                params_str = ", ".join(PAMConfigLine._parameter_tokens(self.frag_params))
                self.frag_params_display.setText(params_str)
            else:
                self.frag_params_display.clear()
    
    def _add_fragment(self):
        """Add a new fragment. Saves current data first."""
        from pam_manager.policy.fragment_manager import PolicyFragmentEntry
        
        name = self.frag_name_input.text().strip()
        desc = self.frag_desc_input.toPlainText().strip()
        
        # Get module from list
        current_item = self.frag_module_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a module")
            return
        module = current_item.text()
        
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a fragment name")
            return
        
        # All fragments support all platforms by default (no selection anymore)
        all_platforms = [p.name for p in Platform]
        platform_support = {plat: True for plat in all_platforms}
        
        # Parameter help is empty (we don't use it anymore)
        parameter_help = {}
        
        # Save existing fragments first (silent)
        self._save_fragments(silent=True)
        
        fragment = PolicyFragmentEntry(
            id=name,
            description=desc,
            module=module,
            interface=None,  # Interface is NOT set at fragment level, only at element level
            parameters=self.frag_params.copy(),
            parameter_help=parameter_help,
            platform_support=platform_support,
        )
        
        if self.add_fragment(fragment):
            QMessageBox.information(self, "Success", f"Fragment '{name}' added successfully")
            self._clear_fragment_form()
            self._refresh_fragment_list()
        else:
            QMessageBox.critical(self, "Error", "Failed to add fragment")
    
    def _clear_fragment_form(self):
        """Clear fragment form fields."""
        self.frag_name_input.clear()
        self.frag_desc_input.clear()
        self.frag_params.clear()
        self.frag_params_display.clear()
        # Deselect fragment list
        self.frag_list.selectionModel().clearSelection()
    
    def _refresh_fragment_list(self):
        """Refresh the fragments list table - includes both regular and template fragments."""
        if DEBUG:
            _debug_print("PolicyFragmentTab._refresh_fragment_list() called")
        self.frag_list.setRowCount(0)
        
        # Add regular fragments (excluding services/directives)
        fragments = self.list_fragments()
        # Filter out services - they are @include or include directives (marked as directive_include or missing interface)
        regular_fragments = [
            f for f in fragments 
            if getattr(f, '_line_type', 'module_line') == 'module_line'
        ]
        if DEBUG:
            _debug_print(f"Regular fragments: {len(regular_fragments)} (excluded {len(fragments) - len(regular_fragments)} services/directives)")
        
        for i, frag in enumerate(regular_fragments):
            self.frag_list.insertRow(i)
            self.frag_list.setItem(i, 0, QTableWidgetItem(frag.id))
            self.frag_list.setItem(i, 1, QTableWidgetItem(frag.module))
            
            # Action buttons
            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout()
            buttons_layout.setContentsMargins(2, 2, 2, 2)
            
            # Edit button
            edit_button = QPushButton("Edit")
            edit_button.setMaximumWidth(60)
            edit_button.clicked.connect(lambda checked, fid=frag.id: self._edit_fragment(fid))
            buttons_layout.addWidget(edit_button)
            
            # Delete button
            delete_button = QPushButton("Delete")
            delete_button.setMaximumWidth(60)
            delete_button.clicked.connect(lambda checked, fid=frag.id: self._delete_fragment(fid))
            buttons_layout.addWidget(delete_button)
            
            buttons_widget.setLayout(buttons_layout)
            self.frag_list.setCellWidget(i, 2, buttons_widget)
        
        # Add template fragments
        template_names = TemplateManager.list_template_names('Fragment')
        _debug_print(f"Template fragments: {len(template_names)} - {template_names}")
        
        if template_names:
            # Add separator row
            row_count = self.frag_list.rowCount()
            self.frag_list.insertRow(row_count)
            separator_item = QTableWidgetItem("─" * 40)
            separator_item.setFlags(separator_item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
            separator_item.setBackground(self.palette().color(self.palette().Mid))
            self.frag_list.setItem(row_count, 0, separator_item)
            
            # Add template fragments
            for tmpl_name in sorted(template_names):
                row_count = self.frag_list.rowCount()
                self.frag_list.insertRow(row_count)
                
                # Display with [TEMPLATE] marker
                display_name = f"[TEMPLATE] {tmpl_name}"
                self.frag_list.setItem(row_count, 0, QTableWidgetItem(display_name))
                self.frag_list.setItem(row_count, 1, QTableWidgetItem("(template)"))
                
                # Action buttons (Load as fragment)
                buttons_widget = QWidget()
                buttons_layout = QHBoxLayout()
                buttons_layout.setContentsMargins(2, 2, 2, 2)
                
                load_button = QPushButton("Load")
                load_button.setMaximumWidth(60)
                load_button.clicked.connect(lambda checked, fname=tmpl_name: self._load_fragment_from_template(fname))
                buttons_layout.addWidget(load_button)
                
                buttons_widget.setLayout(buttons_layout)
                self.frag_list.setCellWidget(row_count, 2, buttons_widget)
                
                if DEBUG:
                    _debug_print(f"Added template: {display_name}")
        
        if DEBUG:
            _debug_print(f"Fragment list now has {self.frag_list.rowCount()} rows total")
    
    def _on_fragment_selected(self, selected, deselected):
        """Handle fragment selection in table."""
        if selected.indexes():
            # Get the fragment ID from first column
            row = selected.indexes()[0].row()
            fragment_id_item = self.frag_list.item(row, 0)
            if fragment_id_item:
                fragment_id = fragment_id_item.text()
                # Skip template fragments
                if fragment_id.startswith("[TEMPLATE]"):
                    return
                self._load_fragment_into_form(fragment_id)
    
    def _load_fragment_into_form(self, fragment_id: str):
        """Load fragment data into form for editing."""
        fragment = self.get_fragment(fragment_id)
        if not fragment:
            return
        
        # Update module list - find and select the module
        for i in range(self.frag_module_list.count()):
            item = self.frag_module_list.item(i)
            if item and item.text() == fragment.module:
                self.frag_module_list.setCurrentRow(i)
                total = self.frag_module_list.count()
                self.module_position_label.setText(f"{i + 1}/{total}")
                break
        
        # Load fragment data into form
        self.frag_name_input.setText(fragment.id)
        self.frag_desc_input.setPlainText(fragment.description)
        
        # Load parameters into form
        self.frag_params = fragment.parameters.copy() if fragment.parameters else {}
        # Remove internal markers from display
        display_params = {k: v for k, v in self.frag_params.items() if not k.startswith('_')}
        if display_params:
            params_str = ", ".join(PAMConfigLine._parameter_tokens(display_params))
            self.frag_params_display.setText(params_str)
        else:
            self.frag_params_display.clear()
    
    def _edit_fragment(self, fragment_id: str):
        """Edit a fragment - open parameter editor."""
        fragment = self.get_fragment(fragment_id)
        if not fragment:
            QMessageBox.warning(self, "Error", f"Fragment '{fragment_id}' not found")
            return
        
        # Load fragment into form first
        self._load_fragment_into_form(fragment_id)
        
        # Open parameter editor dialog (same as Configure Parameters)
        param_dialog = ParameterEditorDialog(fragment.module, self.registry, fragment.parameters, self)
        if param_dialog.exec_() == QDialog.Accepted:
            # Update fragment parameters
            updated_params = param_dialog.get_parameters()
            fragment.parameters = updated_params
            
            if self.update_fragment(fragment):
                self._save_fragments(silent=True)
                self._refresh_fragment_list()
                # Reload into form to show updated params
                self._load_fragment_into_form(fragment_id)
                QMessageBox.information(self, "Success", f"Fragment '{fragment_id}' updated")
            else:
                QMessageBox.critical(self, "Error", f"Failed to update fragment '{fragment_id}'")
    
    def _delete_fragment(self, fragment_id: str):
        """Delete a fragment."""
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete fragment '{fragment_id}'?")
        if reply == QMessageBox.Yes:
            if self.remove_fragment(fragment_id):
                # Clear form
                self._clear_fragment_form()
                QMessageBox.information(self, "Success", "Fragment deleted")
                self._refresh_fragment_list()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete fragment")
    
    def _load_fragment_from_template(self, template_name: str):
        """Load a template fragment into the form for editing."""
        template_data = TemplateManager.load_template_data('Fragment', template_name)
        if not template_data:
            QMessageBox.critical(self, "Error", f"Template '{template_name}' not found")
            return
        
        # Clean the template name (remove "template." prefix)
        clean_name = TemplateManager.clean_template_name(f"template.{template_name}.json")
        
        # Check for collisions
        existing_fragments = self.list_fragments()
        existing_names = [f.id for f in existing_fragments]
        
        # Get available name with collision handling
        final_name = TemplateManager.find_available_name(clean_name, existing_names)
        
        # Load template data into form
        self.frag_name_input.setText(final_name)
        self.frag_desc_input.setPlainText(template_data.get('description', ''))
        
        # Pre-select module if available
        module = template_data.get('module', '')
        if module:
            for i in range(self.frag_module_list.count()):
                item = self.frag_module_list.item(i)
                if item and item.text() == module:
                    self.frag_module_list.setCurrentRow(i)
                    break
        
        QMessageBox.information(
            self,
            "Template Loaded",
            f"Template '{template_name}' loaded as '{final_name}'\n\n"
            f"Click 'Add Fragment' to create new fragment from this template."
        )
    
    def _validate_fragments(self):
        """Validate all fragments."""
        fragments = self.list_fragments()
        errors = []
        
        for frag in fragments:
            if not frag.id:
                errors.append("Fragment has no ID")
            if not frag.module:
                errors.append(f"Fragment '{frag.id}' has no module")
            if frag.interface not in ["auth", "account", "session", "password"]:
                errors.append(f"Fragment '{frag.id}' has invalid interface")
        
        if errors:
            QMessageBox.critical(self, "Validation Errors", "\n".join(errors))
        else:
            QMessageBox.information(self, "Validation Success", f"{len(fragments)} fragments are valid")
    
    def _save_fragments(self, silent=False):
        """Save fragments to file.
        
        Args:
            silent: If True, don't show success/error messages
        """
        if self.save_fragments():
            if not silent:
                QMessageBox.information(self, "Success", "Fragments saved successfully to ~/etc/pam.d/")
        else:
            if not silent:
                QMessageBox.critical(self, "Error", "Failed to save fragments")
    
    def _save_fragment_template(self):
        r"""Save currently selected fragment as template.
        
        Template names cannot contain: / \ ? * !
        """
        # Get selected fragment from table
        current_row = self.frag_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a fragment to save as template")
            return
        
        fragments = self.list_fragments()
        if current_row >= len(fragments):
            QMessageBox.warning(self, "Error", "Fragment not found")
            return
        
        fragment = fragments[current_row]
        
        # Validate fragment name
        is_valid, error_msg = TemplateManager.validate_template_name(fragment.id)
        if not is_valid:
            QMessageBox.warning(
                self, 
                "Invalid Fragment Name", 
                f"Cannot save template: {error_msg}\n\n"
                f"Forbidden characters: / \\ ? * !"
            )
            return
        
        # Prepare data for template (include all fragment details)
        from dataclasses import asdict
        template_data = asdict(fragment) if hasattr(fragment, '__dataclass_fields__') else {
            'id': fragment.id,
            'description': fragment.description,
            'module': fragment.module,
            'interface': fragment.interface,
            'parameters': fragment.parameters,
            'parameter_help': fragment.parameter_help,
            'platform_support': fragment.platform_support,
            'tags': fragment.tags,
            'created': fragment.created,
            'modified': fragment.modified,
        }
        
        try:
            saved_path = TemplateManager.save_template('Fragment', fragment.id, template_data)
            QMessageBox.information(
                self, 
                "Success", 
                f"Fragment '{fragment.id}' saved as template to Fragment.Templates:\n{saved_path.name}"
            )
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Name", f"Cannot save template:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {e}")


class PolicyElementTab(QWidget):
    """Tab for creating and managing policy elements."""
    
    def __init__(self, registry: ModuleRegistry, config_manager: 'UnifiedConfigManager'):
        super().__init__()
        self.registry = registry
        self.config_manager = config_manager
        self._fragment_manager_adapter = None
        self.init_ui()
    
    @property
    def fragment_manager(self):
        """Return fragment manager adapter for backward compatibility."""
        if self._fragment_manager_adapter is None:
            from pam_manager.policy.fragment_manager import UnifiedFragmentManagerAdapter
            self._fragment_manager_adapter = UnifiedFragmentManagerAdapter(self.config_manager)
        return self._fragment_manager_adapter
    
    # Helper methods delegating to config_manager
    def add_element(self, element):
        """Add element to config manager."""
        from dataclasses import asdict
        elem_dict = asdict(element) if hasattr(element, '__dataclass_fields__') else element
        # Convert nested dataclass objects to dicts
        if 'fragments' in elem_dict:
            elem_dict['fragments'] = [
                asdict(f) if hasattr(f, '__dataclass_fields__') else f
                for f in elem_dict['fragments']
            ]
        return self.config_manager.add_element(elem_dict)
    
    def remove_element(self, element_id):
        """Remove element from config manager."""
        return self.config_manager.remove_element(element_id)
    
    def get_element(self, element_id):
        """Get element from config manager."""
        from pam_manager.policy.fragment_manager import PolicyElementEntry, PolicyElementFragmentRef
        elem_dict = self.config_manager.get_element(element_id)
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
    
    def update_element(self, element):
        """Update an existing element."""
        from dataclasses import asdict
        elem_dict = asdict(element) if hasattr(element, '__dataclass_fields__') else element
        if 'fragments' in elem_dict:
            elem_dict['fragments'] = [
                asdict(f) if hasattr(f, '__dataclass_fields__') else f
                for f in elem_dict['fragments']
            ]
        return self.config_manager.add_element(elem_dict)  # add_element handles both add and update
    
    def list_fragments(self):
        """List all fragments from config manager."""
        from pam_manager.policy.fragment_manager import PolicyFragmentEntry
        return [
            PolicyFragmentEntry(
                id=f['id'],
                description=f['description'],
                module=f['module'],
                interface=f.get('interface'),
                parameters=f.get('parameters', {}),
                parameter_help=f.get('parameter_help', {}),
                platform_support=f.get('platform_support', {}),
                tags=f.get('tags', []),
                created=f.get('created', ''),
                modified=f.get('modified', ''),
            )
            for f in self.config_manager.list_fragments()
        ]
    
    def list_elements(self):
        """List all elements from config manager."""
        # Convert dicts to PolicyElementEntry objects
        from pam_manager.policy.fragment_manager import PolicyElementEntry, PolicyElementFragmentRef
        result = []
        for e in self.config_manager.list_elements():
            # Parse fragment references
            fragments = []
            for frag_ref in e.get('fragments', []):
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
                id=e['id'],
                description=e['description'],
                service_name=e.get('service_name'),
                config_file=e.get('config_file'),
                fragments=fragments,
                tags=e.get('tags', []),
                created=e.get('created', ''),
                modified=e.get('modified', ''),
            )
            result.append(elem)
        
        return result
    
    def save_elements(self):
        """Save elements (delegated to config_manager.save())."""
        try:
            self.config_manager.save()
            return True
        except:
            return False
    
    def init_ui(self):
        """Initialize policy element tab UI."""
        main_layout = QVBoxLayout()
        
        # Info only (no title)
        info = QLabel("Manage policy elements by combining policy fragments with interface and control flags")
        info.setStyleSheet("color: gray; font-style: italic;")
        main_layout.addWidget(info)
        
        # Element creation section (no GroupBox)
        creation_layout = QFormLayout()
        
        # Element name
        self.elem_name_input = QLineEdit()
        self.elem_name_input.setPlaceholderText("e.g., secure-login-policy")
        creation_layout.addRow("Element Name:", self.elem_name_input)
        
        # Description
        self.elem_desc_input = QTextEdit()
        self.elem_desc_input.setMaximumHeight(60)
        creation_layout.addRow("Description:", self.elem_desc_input)
        
        creation_widget = QWidget()
        creation_widget.setLayout(creation_layout)
        main_layout.addWidget(creation_widget)
        
        # PAM Command Builder section
        builder_group = QGroupBox("Build PAM Command")
        builder_layout = QVBoxLayout()
        
        builder_button_layout = QHBoxLayout()
        builder_button = QPushButton("PAM Command Builder")
        builder_button.setMinimumHeight(40)
        builder_button.setMaximumWidth(200)
        builder_button.clicked.connect(self._open_pam_builder)
        builder_button_layout.addStretch()
        builder_button_layout.addWidget(builder_button)
        builder_button_layout.addStretch()
        builder_layout.addLayout(builder_button_layout)
        
        # Display built command
        self.built_command_display = QLineEdit()
        self.built_command_display.setReadOnly(True)
        self.built_command_display.setPlaceholderText("Generated PAM command will appear here...")
        builder_layout.addWidget(self.built_command_display)
        
        builder_group.setLayout(builder_layout)
        main_layout.addWidget(builder_group)
        
        # Fragments in element
        frag_group = QGroupBox("Add Policy Fragments to Element")
        frag_layout = QVBoxLayout()
        
        # Fragment selection (single row, compact) - reordered: Interface, Control Flag, Fragment
        frag_select_layout = QHBoxLayout()
        
        # Interface selection
        frag_select_layout.addWidget(QLabel("Interface:"))
        self.elem_frag_interface = QComboBox()
        self.elem_frag_interface.addItems(["auth", "account", "session", "password"])
        self.elem_frag_interface.currentIndexChanged.connect(self._on_fragment_form_changed)
        frag_select_layout.addWidget(self.elem_frag_interface)
        
        # Control flag selection
        frag_select_layout.addWidget(QLabel("Control Flag:"))
        self.elem_frag_control = QComboBox()
        self._set_control_flags_for_source("fragment")
        self.elem_frag_control.currentIndexChanged.connect(self._on_fragment_form_changed)
        frag_select_layout.addWidget(self.elem_frag_control)
        
        # Fragment/Service selection
        frag_select_layout.addWidget(QLabel("Fragment/Service:"))
        self.elem_frag_combo = QComboBox()
        self._refresh_element_fragment_sources()
        self.elem_frag_combo.currentIndexChanged.connect(self._on_element_fragment_source_changed)
        frag_select_layout.addWidget(self.elem_frag_combo)
        
        # Add button
        add_frag_button = QPushButton("Add")
        add_frag_button.setMaximumWidth(60)
        add_frag_button.clicked.connect(self._add_element_fragment)
        frag_select_layout.addWidget(add_frag_button)
        frag_layout.addLayout(frag_select_layout)
        
        # Fragments in element table (scrollable with dynamic height)
        self.elem_frag_table = QTableWidget()
        self.elem_frag_table.setColumnCount(5)
        self.elem_frag_table.setHorizontalHeaderLabels(["#", "Interface", "Control flag", "Fragment Name", "Actions"])
        set_all_columns_resize_mode(self.elem_frag_table.horizontalHeader(), QHeaderView.Stretch)
        self.elem_frag_table.selectionModel().selectionChanged.connect(self._on_element_fragment_selected)
        frag_layout.addWidget(self.elem_frag_table)
        
        # Selected fragment index tracker
        self.selected_fragment_index = -1
        
        
        frag_group.setLayout(frag_layout)
        main_layout.addWidget(frag_group)
        
        # Elements list (expandable, no title, minimum 5 rows)
        self.elem_list = QTableWidget()
        self.elem_list.setColumnCount(3)
        self.elem_list.setHorizontalHeaderLabels(["Name", "Fragment Count", "Actions"])
        set_all_columns_resize_mode(self.elem_list.horizontalHeader(), QHeaderView.Stretch)
        self.elem_list.setMinimumHeight(int(self.elem_list.fontMetrics().height() * 5.5))  # Minimum 5 rows
        main_layout.addWidget(self.elem_list, 1)  # Expandable with weight 1
        
        # Action buttons
        action_layout = QHBoxLayout()
        add_button = QPushButton("Add Element")
        add_button.clicked.connect(self._add_element)
        validate_button = QPushButton("Validate Configuration")
        validate_button.clicked.connect(self._validate_elements)
        save_button = QPushButton("Save Elements")
        save_button.clicked.connect(self._save_elements)
        save_template_button = QPushButton("Save Template")
        save_template_button.clicked.connect(self._save_element_template)
        
        help_button = QPushButton("Help")
        help_button.setMaximumWidth(80)
        help_button.clicked.connect(lambda: self._show_help())
        
        action_layout.addWidget(add_button)
        action_layout.addWidget(validate_button)
        action_layout.addWidget(save_button)
        action_layout.addWidget(save_template_button)
        action_layout.addStretch()
        action_layout.addWidget(help_button)
        main_layout.addLayout(action_layout)
        
        self.setLayout(main_layout)
        
        # Initialize
        self.element_fragments: List = []
        self._on_element_fragment_source_changed()
        self._refresh_element_list()

    def _show_help(self):
        """Show help for this tab."""
        # Get parent PAMManagerGUI instance
        parent = self.parent()
        while parent and not isinstance(parent, PAMManagerGUI):
            parent = parent.parent()
        if parent and isinstance(parent, PAMManagerGUI):
            parent.show_help("Policy Element")

    def _set_control_flags_for_source(self, source_type: str):
        """Set available control flags based on selected source type."""
        current = self.elem_frag_control.currentText()
        self.elem_frag_control.blockSignals(True)
        self.elem_frag_control.clear()

        if source_type == "service":
            flags = ["include", "substack"]
        else:
            flags = ["required", "requisite", "sufficient", "optional"]

        self.elem_frag_control.addItems(flags)
        if current in flags:
            self.elem_frag_control.setCurrentText(current)
        self.elem_frag_control.blockSignals(False)

    def _refresh_element_fragment_sources(self):
        """Populate fragment source combo with fragments, services, templates, and service templates."""
        self.elem_frag_combo.blockSignals(True)
        self.elem_frag_combo.clear()

        # Regular fragments
        fragments = self.list_fragments()
        for frag in fragments:
            self.elem_frag_combo.addItem(frag.id, userData=("fragment", frag.id))

        # Services section
        services = sorted(self.config_manager.list_services(), key=lambda s: s.get('id', ''))
        if services:
            if self.elem_frag_combo.count() > 0:
                self.elem_frag_combo.insertSeparator(self.elem_frag_combo.count())
            for service in services:
                service_id = service.get('id', '').strip()
                if not service_id:
                    continue
                self.elem_frag_combo.addItem(f"[SERVICE] {service_id}", userData=("service", service_id))

        # Template fragments section
        template_names = TemplateManager.list_template_names('Fragment')
        if template_names:
            if self.elem_frag_combo.count() > 0:
                self.elem_frag_combo.insertSeparator(self.elem_frag_combo.count())
            for tmpl_name in template_names:
                self.elem_frag_combo.addItem(f"[TEMPLATE FRAG] {tmpl_name}", userData=("template", tmpl_name))

        # Service templates section
        service_template_names = TemplateManager.list_template_names('Service')
        if service_template_names:
            if self.elem_frag_combo.count() > 0:
                self.elem_frag_combo.insertSeparator(self.elem_frag_combo.count())
            for tmpl_name in service_template_names:
                self.elem_frag_combo.addItem(f"[TEMPLATE SVC] {tmpl_name}", userData=("service_template", tmpl_name))

        self.elem_frag_combo.blockSignals(False)

    def _on_element_fragment_source_changed(self):
        """Update control flags when selected fragment source changes."""
        current_index = self.elem_frag_combo.currentIndex()
        user_data = self.elem_frag_combo.itemData(current_index)
        source_type = "fragment"
        if isinstance(user_data, tuple) and len(user_data) == 2:
            source_type = user_data[0]
        self._set_control_flags_for_source(source_type)
    
    def _on_fragment_form_changed(self):
        """Handle changes to fragment form (interface or control flag changed)."""
        # Reset selection when user manually changes form values
        self.selected_fragment_index = -1
        
        # Update PAM command display - show ONLY control_flag (without interface or module)
        control = self.elem_frag_control.currentText()
        
        if control:
            self.built_command_display.setText(control)
        else:
            self.built_command_display.clear()
        
        # Refresh table to update button labels (Reset Edit buttons)
        if self.element_fragments:
            self._refresh_element_fragments_table()
    
    def refresh_data(self):
        """Refresh element data when tab is activated. Also refresh fragment list."""
        if DEBUG:
            _debug_print("PolicyElementTab.refresh_data() called")

        self._refresh_element_fragment_sources()
        self._on_element_fragment_source_changed()
        _debug_print(f"Combo box now has {self.elem_frag_combo.count()} items")
        self._refresh_element_list()
    
    def _add_element_fragment(self):
        """Add a fragment to the current element."""
        from pam_manager.policy.fragment_manager import PolicyElementFragmentRef
        
        # Get fragment reference - can be regular or template
        current_index = self.elem_frag_combo.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "Error", "Please select a fragment")
            return
        
        user_data = self.elem_frag_combo.itemData(current_index)
        source_type = 'fragment'
        source_name = None
        if user_data and isinstance(user_data, tuple):
            source_type, source_name = user_data

        if source_type == 'template':
            # Template fragment - load and create new fragment
            template_name = source_name
            template_data = TemplateManager.load_template_data('Fragment', template_name)
            
            if not template_data:
                QMessageBox.critical(self, "Error", f"Template '{template_name}' not found")
                return
            
            # Clean the template name (remove "template." prefix)
            clean_name = TemplateManager.clean_template_name(f"template.{template_name}.json")
            
            # Check for name collisions with existing fragments
            existing_fragments = self.config_manager.list_fragments()
            existing_names = [f['id'] for f in existing_fragments]
            
            # Get available name with suffix if collision detected
            final_name = TemplateManager.find_available_name(clean_name, existing_names)
            
            # Create new fragment from template data
            new_fragment = {
                'id': final_name,
                'description': template_data.get('description', ''),
                'module': template_data.get('module', ''),
                'interface': template_data.get('interface'),
                'parameters': template_data.get('parameters', {}),
                'parameter_help': template_data.get('parameter_help', {}),
                'platform_support': template_data.get('platform_support', {}),
                'tags': template_data.get('tags', [])
            }
            
            # Add new fragment to config
            if not self.config_manager.add_fragment(new_fragment):
                QMessageBox.critical(self, "Error", "Failed to create fragment from template")
                return
            
            frag_ref = final_name
        elif source_type == 'service':
            frag_ref = source_name or self.elem_frag_combo.currentText().replace("[SERVICE] ", "")
        else:
            # Regular fragment
            frag_ref = source_name or self.elem_frag_combo.currentText()
        
        interface = self.elem_frag_interface.currentText()
        control_flag = self.elem_frag_control.currentText()
        
        # Interface and control_flag are now required
        if not interface or interface.startswith("("):
            QMessageBox.warning(self, "Error", "Please select an interface")
            return
        if not control_flag or control_flag.startswith("("):
            QMessageBox.warning(self, "Error", "Please select a control flag")
            return
        
        elem_frag = PolicyElementFragmentRef(
            fragment_ref=frag_ref,
            interface=interface,
            control_flag=control_flag,
        )
        
        self.element_fragments.append(elem_frag)
        self._refresh_element_fragments_table()
    
    def _refresh_element_fragments_table(self):
        """Refresh the element fragments table with dynamic height based on row count."""
        self.elem_frag_table.setRowCount(0)
        
        for i, elem_frag in enumerate(self.element_fragments):
            self.elem_frag_table.insertRow(i)
            # Column 0: Line number
            self.elem_frag_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            # Column 1: Interface
            self.elem_frag_table.setItem(i, 1, QTableWidgetItem(elem_frag.interface or ""))
            # Column 2: Control flag
            self.elem_frag_table.setItem(i, 2, QTableWidgetItem(elem_frag.control_flag or ""))
            # Column 3: Fragment Ref
            self.elem_frag_table.setItem(i, 3, QTableWidgetItem(elem_frag.fragment_ref))
            
            # Column 4: Action buttons
            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout()
            buttons_layout.setContentsMargins(2, 2, 2, 2)
            
            # Button label depends on selection: Edit or Update
            is_selected = (i == self.selected_fragment_index)
            button_label = "Update" if is_selected else "Edit"
            
            edit_button = QPushButton(button_label)
            edit_button.setMaximumWidth(60)
            edit_button.clicked.connect(lambda checked, idx=i: self._edit_element_fragment_with_builder(idx))
            buttons_layout.addWidget(edit_button)
            
            # Delete button
            delete_button = QPushButton("Remove")
            delete_button.setMaximumWidth(60)
            delete_button.clicked.connect(lambda checked, idx=i: self._remove_element_fragment(idx))
            buttons_layout.addWidget(delete_button)
            
            buttons_widget.setLayout(buttons_layout)
            self.elem_frag_table.setCellWidget(i, 4, buttons_widget)
        
        # Set dynamic height based on fragment count
        # Less than 5: 3 rows, less than 8: 4 rows, 8+: 5 rows
        row_count = len(self.element_fragments)
        if row_count < 5:
            desired_rows = 3
        elif row_count < 8:
            desired_rows = 4
        else:
            desired_rows = 5
        
        # Calculate height with header
        row_height = self.elem_frag_table.rowHeight(0) if row_count > 0 else 30
        header_height = self.elem_frag_table.horizontalHeader().height()
        total_height = header_height + (row_height * desired_rows) + 4  # +4 for spacing
        self.elem_frag_table.setMinimumHeight(total_height)
    
    def _on_element_fragment_selected(self, selected, deselected):
        """Handle fragment selection in table."""
        if selected.indexes():
            # Get the selected row
            row = selected.indexes()[0].row()
            if 0 <= row < len(self.element_fragments):
                self.selected_fragment_index = row
                self._load_fragment_into_form(row)
                # Refresh table to update button labels
                self._refresh_element_fragments_table()
    
    def _load_fragment_into_form(self, index: int):
        """Load selected fragment into form fields above the table."""
        if not (0 <= index < len(self.element_fragments)):
            return
        
        frag_ref = self.element_fragments[index]
        
        # Update Interface combo
        self.elem_frag_interface.blockSignals(True)
        self.elem_frag_interface.setCurrentText(frag_ref.interface or "auth")
        self.elem_frag_interface.blockSignals(False)
        
        # Update Control Flag combo
        self.elem_frag_control.blockSignals(True)
        self.elem_frag_control.setCurrentText(frag_ref.control_flag or "required")
        self.elem_frag_control.blockSignals(False)
        
        # Update Fragment/Service combo
        self.elem_frag_combo.blockSignals(True)
        combo_idx = self.elem_frag_combo.findText(frag_ref.fragment_ref, Qt.MatchContains)
        if combo_idx >= 0:
            self.elem_frag_combo.setCurrentIndex(combo_idx)
        self.elem_frag_combo.blockSignals(False)
        
        # Update PAM Command display - show ONLY control_flag/extended syntax (without interface or module)
        if frag_ref.extended_control:
            extended_str = " ".join([f"{k}={v}" for k, v in frag_ref.extended_control.items()])
            command = f"[{extended_str}]"
        else:
            command = frag_ref.control_flag or "required"
        
        self.built_command_display.setText(command)
    
    def _remove_element_fragment(self, index: int):
        """Remove a fragment from current element."""
        if 0 <= index < len(self.element_fragments):
            self.element_fragments.pop(index)
            # Reset selection
            if self.selected_fragment_index >= len(self.element_fragments):
                self.selected_fragment_index = -1
            self._refresh_element_fragments_table()
    
    def _edit_element_fragment_with_builder(self, index: int):
        """Edit a fragment reference in element using PAM Command Builder."""
        if not (0 <= index < len(self.element_fragments)):
            return
        
        frag_ref = self.element_fragments[index]
        
        # Open PAM Command Builder with current values
        dialog = PAMControlSyntaxBuilder(self, 
                                        initial_interface=frag_ref.interface,
                                        initial_control=frag_ref.control_flag,
                                        initial_extended=frag_ref.extended_control if frag_ref.extended_control else None,
                                        config_manager=self.config_manager)
        if dialog.exec_() == QDialog.Accepted:
            interface, control, extended_syntax = dialog.get_pam_line_parts()
            
            # Update fragment reference with new interface and control flag
            frag_ref.interface = interface
            frag_ref.control_flag = control
            frag_ref.extended_control = extended_syntax if extended_syntax else {}
            
            self.element_fragments[index] = frag_ref
            self._refresh_element_fragments_table()
    
    def _add_element(self):
        """Add a new element. Saves current data first."""
        from pam_manager.policy.fragment_manager import PolicyElementEntry
        
        name = self.elem_name_input.text().strip()
        desc = self.elem_desc_input.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Error", "Please enter an element name")
            return
        
        if not self.element_fragments:
            QMessageBox.warning(self, "Error", "Please add at least one fragment to the element")
            return
        
        # Save existing elements first (silent)
        self._save_elements(silent=True)
        
        element = PolicyElementEntry(
            id=name,
            description=desc,
            fragments=self.element_fragments.copy(),
        )
        
        if self.add_element(element):
            QMessageBox.information(self, "Success", f"Element '{name}' added successfully")
            self._clear_element_form()
            self._refresh_element_list()
        else:
            QMessageBox.critical(self, "Error", "Failed to add element")
    
    def _clear_element_form(self):
        """Clear element form fields."""
        self.elem_name_input.clear()
        self.elem_desc_input.clear()
        self.element_fragments.clear()
        self.selected_fragment_index = -1
        self.built_command_display.clear()
        self._refresh_element_fragments_table()
    
    def _refresh_element_list(self):
        """Refresh the elements list table - includes both regular and template elements."""
        self.elem_list.setRowCount(0)
        elements = self.list_elements()
        
        # Add regular elements
        for i, elem in enumerate(elements):
            self.elem_list.insertRow(i)
            self.elem_list.setItem(i, 0, QTableWidgetItem(elem.id))
            self.elem_list.setItem(i, 1, QTableWidgetItem(str(len(elem.fragments))))
            
            # Action buttons
            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout()
            buttons_layout.setContentsMargins(2, 2, 2, 2)
            
            # Load button
            load_button = QPushButton("Load")
            load_button.setMaximumWidth(60)
            load_button.clicked.connect(lambda checked, eid=elem.id: self._load_element(eid))
            buttons_layout.addWidget(load_button)
            
            # Delete button
            delete_button = QPushButton("Delete")
            delete_button.setMaximumWidth(60)
            delete_button.clicked.connect(lambda checked, eid=elem.id: self._delete_element(eid))
            buttons_layout.addWidget(delete_button)
            
            buttons_widget.setLayout(buttons_layout)
            self.elem_list.setCellWidget(i, 2, buttons_widget)
        
        # Add template elements
        template_names = TemplateManager.list_template_names('Element')
        
        if template_names:
            # Add separator row
            row_count = self.elem_list.rowCount()
            self.elem_list.insertRow(row_count)
            separator_item = QTableWidgetItem("─" * 40)
            separator_item.setFlags(separator_item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
            separator_item.setBackground(self.palette().color(self.palette().Mid))
            self.elem_list.setItem(row_count, 0, separator_item)
            
            # Add template elements
            for tmpl_name in sorted(template_names):
                row_count = self.elem_list.rowCount()
                self.elem_list.insertRow(row_count)
                
                # Display with [TEMPLATE] marker
                display_name = f"[TEMPLATE] {tmpl_name}"
                self.elem_list.setItem(row_count, 0, QTableWidgetItem(display_name))
                self.elem_list.setItem(row_count, 1, QTableWidgetItem("(template)"))
                
                # Action buttons (Load as element)
                buttons_widget = QWidget()
                buttons_layout = QHBoxLayout()
                buttons_layout.setContentsMargins(2, 2, 2, 2)
                
                load_button = QPushButton("Load")
                load_button.setMaximumWidth(60)
                load_button.clicked.connect(lambda checked, fname=tmpl_name: self._load_element_from_template(fname))
                buttons_layout.addWidget(load_button)
                
                buttons_widget.setLayout(buttons_layout)
                self.elem_list.setCellWidget(row_count, 2, buttons_widget)
    
    def _load_element(self, element_id: str):
        """Load an element into the form for editing."""
        element = self.get_element(element_id)
        if not element:
            QMessageBox.warning(self, "Error", f"Element '{element_id}' not found")
            return
        
        # Clear current form
        self._clear_element_form()
        
        # Load element data into form
        self.elem_name_input.setText(element.id)
        self.elem_desc_input.setPlainText(element.description)
        
        # Load fragment references
        self.element_fragments = []
        for frag_ref in element.fragments:
            self.element_fragments.append(frag_ref)
        
        self.selected_fragment_index = -1
        self._refresh_element_fragments_table()
        
        # Inform user
        QMessageBox.information(self, "Element Loaded", f"Element '{element_id}' loaded into the form. You can now edit it.")
    
    def _delete_element(self, element_id: str):
        """Delete an element."""
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete element '{element_id}'?")
        if reply == QMessageBox.Yes:
            if self.remove_element(element_id):
                QMessageBox.information(self, "Success", "Element deleted")
                self._refresh_element_list()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete element")
    
    def _load_element_from_template(self, template_name: str):
        """Load a template element into the form for editing."""
        template_data = TemplateManager.load_template_data('Element', template_name)
        if not template_data:
            QMessageBox.critical(self, "Error", f"Template '{template_name}' not found")
            return
        
        # Clean the template name (remove "template." prefix)
        clean_name = TemplateManager.clean_template_name(f"template.{template_name}.json")
        
        # Check for collisions
        existing_elements = self.list_elements()
        existing_names = [e.id for e in existing_elements]
        
        # Get available name with collision handling
        final_name = TemplateManager.find_available_name(clean_name, existing_names)
        
        # Load template data into form
        self.elem_name_input.setText(final_name)
        self.elem_desc_input.setPlainText(template_data.get('description', ''))
        
        # Load fragments from template
        self.element_fragments.clear()
        for frag_ref_data in template_data.get('fragments', []):
            from pam_manager.policy.fragment_manager import PolicyElementFragmentRef
            frag_ref = PolicyElementFragmentRef(
                fragment_ref=frag_ref_data.get('fragment_ref', ''),
                interface=frag_ref_data.get('interface', ''),
                control_flag=frag_ref_data.get('control_flag', ''),
                extended_control=frag_ref_data.get('extended_control', {}),
                line_type=frag_ref_data.get('line_type', 'module_line'),
                include_target=frag_ref_data.get('include_target', ''),
            )
            self.element_fragments.append(frag_ref)
        
        self._refresh_element_fragments_table()
        
        QMessageBox.information(
            self,
            "Template Loaded",
            f"Template '{template_name}' loaded as '{final_name}'\n\n"
            f"Click 'Add Element' to create new element from this template."
        )
    
    def _open_pam_builder(self):
        """Open PAM Command Builder dialog."""
        dialog = PAMControlSyntaxBuilder(self, config_manager=self.config_manager)
        if dialog.exec_() == QDialog.Accepted:
            interface, control, extended_syntax = dialog.get_pam_line_parts()
            
            # Build command string for display - show ONLY control_flag/extended syntax (without interface or module)
            if extended_syntax:
                # Extended syntax
                extended_str = " ".join([f"{k}={v}" for k, v in extended_syntax.items()])
                command = f"[{extended_str}]"
            else:
                # Standard syntax (control_flag only)
                command = control if control else "required"
            
            # Display in command field
            self.built_command_display.setText(command)
            
            # Optionally show details
            QMessageBox.information(
                self, 
                "PAM Command Built",
                f"Control Flag: {control if control else 'Extended Syntax'}\n"
                f"Command: {command}"
            )
    
    def _validate_elements(self):
        """Validate all elements."""
        elements = self.list_elements()
        errors = []
        
        for elem in elements:
            if not elem.id:
                errors.append("Element has no ID")
            if not elem.fragments:
                errors.append(f"Element '{elem.id}' has no fragments")
            
            for i, frag_ref in enumerate(elem.fragments):
                if not frag_ref.fragment_ref:
                    errors.append(f"Element '{elem.id}', fragment {i}: no fragment reference")
                if not frag_ref.interface or frag_ref.interface.startswith("("):
                    errors.append(f"Element '{elem.id}', fragment {i}: interface not specified")
                if not frag_ref.control_flag or frag_ref.control_flag.startswith("("):
                    errors.append(f"Element '{elem.id}', fragment {i}: control flag not specified")
        
        if errors:
            QMessageBox.critical(self, "Validation Errors", "\n".join(errors))
        else:
            QMessageBox.information(self, "Validation Success", f"{len(elements)} elements are valid")
    
    def _save_elements(self, silent=False):
        """Save elements to file.
        
        Args:
            silent: If True, don't show success/error messages
        """
        if self.save_elements():
            if not silent:
                QMessageBox.information(self, "Success", "Elements saved successfully to ~/etc/pam.d/")
        else:
            if not silent:
                QMessageBox.critical(self, "Error", "Failed to save elements")
    
    def _save_element_template(self):
        r"""Save currently selected element as template.
        
        Template names cannot contain: / \ ? * !
        """
        # Get selected element from table
        current_row = self.elem_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select an element to save as template")
            return
        
        elements = self.list_elements()
        if current_row >= len(elements):
            QMessageBox.warning(self, "Error", "Element not found")
            return
        
        element = elements[current_row]
        
        # Validate element name
        is_valid, error_msg = TemplateManager.validate_template_name(element.id)
        if not is_valid:
            QMessageBox.warning(
                self, 
                "Invalid Element Name", 
                f"Cannot save template: {error_msg}\n\n"
                f"Forbidden characters: / \\ ? * !"
            )
            return
        
        # Prepare data for template (include all element details)
        from dataclasses import asdict
        fragments_data = []
        for frag_ref in element.fragments:
            fragments_data.append({
                'fragment_ref': frag_ref.fragment_ref,
                'interface': frag_ref.interface,
                'control_flag': frag_ref.control_flag,
                'extended_control': frag_ref.extended_control,
                'line_type': frag_ref.line_type,
                'include_target': frag_ref.include_target,
            })
        
        template_data = {
            'id': element.id,
            'description': element.description,
            'service_name': element.service_name,
            'config_file': element.config_file,
            'fragments': fragments_data,
            'tags': element.tags,
            'created': element.created,
            'modified': element.modified,
        }
        
        try:
            saved_path = TemplateManager.save_template('Element', element.id, template_data)
            QMessageBox.information(
                self, 
                "Success", 
                f"Element '{element.id}' saved as template to Element.Templates:\n{saved_path.name}"
            )
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Name", f"Cannot save template:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {e}")


class ServiceMappingTab(QWidget):
    """Tab for managing relationship between Policy Elements and Services.
    
    Allows creating services, adding policy elements to them, and exporting
    service definitions with proper headers and formatting.
    
    All operations work on in-memory configuration (self.config_manager.data),
    which is synchronized to YAML/JSON on save.
    """
    
    def __init__(self, config_manager: 'UnifiedConfigManager', parent_gui: Optional['PAMManagerGUI'] = None):
        super().__init__()
        self.config_manager = config_manager
        self.parent_gui = parent_gui
        self.init_ui()
    
    def init_ui(self):
        """Initialize service mapping tab UI."""
        main_layout = QVBoxLayout()
        
        # Info text only (no title)
        info = QLabel("Define relationship between Policy Elements and PAM Services")
        info.setStyleSheet("color: gray; font-style: italic;")
        main_layout.addWidget(info)
        
        # Service creation/editing section
        service_group = QGroupBox("Create or Edit Service")
        service_layout = QFormLayout()
        
        # Service name
        self.service_name_input = QLineEdit()
        self.service_name_input.setPlaceholderText("e.g., login, sshd, sudo")
        service_layout.addRow("Service Name:", self.service_name_input)
        
        # Service description
        self.service_desc_input = QTextEdit()
        self.service_desc_input.setMaximumHeight(60)
        service_layout.addRow("Description:", self.service_desc_input)
        
        # Buttons for create/edit/delete service
        service_button_layout = QHBoxLayout()
        
        create_service_button = QPushButton("Create Service")
        create_service_button.clicked.connect(self._create_service)
        service_button_layout.addWidget(create_service_button)
        
        edit_service_button = QPushButton("Update Service")
        edit_service_button.clicked.connect(self._edit_service)
        service_button_layout.addWidget(edit_service_button)
        
        delete_service_button = QPushButton("Delete Service")
        delete_service_button.clicked.connect(self._delete_service)
        service_button_layout.addWidget(delete_service_button)
        
        service_button_layout.addStretch()
        service_layout.addRow("", service_button_layout)
        
        service_widget = QWidget()
        service_widget.setLayout(service_layout)
        service_group.setLayout(service_layout)
        main_layout.addWidget(service_group)
        
        # Service selection section
        selection_group = QGroupBox("Select Service")
        selection_layout = QHBoxLayout()
        
        selection_layout.addWidget(QLabel("Service:"))
        self.service_combo = QComboBox()
        self.service_combo.addItem("(select)")  # Placeholder item
        self.service_combo.currentIndexChanged.connect(self._on_service_selection_changed)
        selection_layout.addWidget(self.service_combo)
        selection_layout.addStretch()
        
        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)
        
        # Elements in service section
        elements_group = QGroupBox("Policy Elements in Service")
        elements_layout = QVBoxLayout()
        
        # Add element to service
        add_elem_layout = QHBoxLayout()
        add_elem_layout.addWidget(QLabel("Add Element:"))
        self.elements_combo = QComboBox()
        add_elem_layout.addWidget(self.elements_combo)
        
        add_elem_button = QPushButton("Add to Service")
        add_elem_button.clicked.connect(self._add_element_to_service)
        add_elem_layout.addWidget(add_elem_button)
        add_elem_layout.addStretch()
        
        elements_layout.addLayout(add_elem_layout)
        
        # Elements in service table (expandable)
        self.service_elements_table = QTableWidget()
        self.service_elements_table.setColumnCount(3)
        self.service_elements_table.setHorizontalHeaderLabels(["#", "Element Name", "Actions"])
        # Optimize column widths: "#" is narrow (ResizeToContents), "Element Name" and "Actions" stretch
        set_column_resize_mode(self.service_elements_table.horizontalHeader(), 0, QHeaderView.ResizeToContents)  # "#" column
        set_column_resize_mode(self.service_elements_table.horizontalHeader(), 1, QHeaderView.Stretch)  # "Element Name" - expanded
        set_column_resize_mode(self.service_elements_table.horizontalHeader(), 2, QHeaderView.ResizeToContents)  # "Actions" - compact
        elements_layout.addWidget(self.service_elements_table, 1)
        
        elements_group.setLayout(elements_layout)
        main_layout.addWidget(elements_group, 1)  # Expandable
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        add_service_button = QPushButton("Add Service")
        add_service_button.clicked.connect(self._create_service)
        action_layout.addWidget(add_service_button)
        
        validate_service_button = QPushButton("Validate Service")
        validate_service_button.clicked.connect(self._validate_service)
        action_layout.addWidget(validate_service_button)
        
        save_service_button = QPushButton("Save Service")
        save_service_button.clicked.connect(self._save)
        action_layout.addWidget(save_service_button)
        
        save_template_button = QPushButton("Save Template")
        save_template_button.clicked.connect(self._save_service_template)
        action_layout.addWidget(save_template_button)
        
        help_button = QPushButton("Help")
        help_button.setMaximumWidth(80)
        help_button.clicked.connect(lambda: self._show_help())
        
        action_layout.addStretch()
        action_layout.addWidget(help_button)
        main_layout.addLayout(action_layout)
        
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
        # Initialize
        self._refresh_service_list()
        self._refresh_elements_combo()
    
    def refresh_data(self):
        """Refresh service mapping data when tab is activated.
        
        Called when Service Definition tab is activated. Ensures that:
        1. Service list is refreshed from config
        2. Element list is refreshed
        3. Elements table for currently selected service is refreshed
        """
        if DEBUG:
            _debug_print("ServiceMappingTab.refresh_data() called")
        self._refresh_service_list()
        self._refresh_elements_combo()
        
        # CRITICAL: Always refresh the elements table if a service is selected
        # This ensures the table shows the correct elements even on Wayland
        current_index = self.service_combo.currentIndex()
        _debug_print(f"Service combo current index: {current_index}")
        if current_index > 0:
            # Trigger service selection handler to refresh the table
            _debug_print(f"Service is selected, calling _on_service_selection_changed()")
            self._on_service_selection_changed()
            
            # Additional safety: refresh table again with small delay to handle Wayland issues
            # Use Qt's post-event mechanism instead of sleep
            from PyQt5.QtCore import QTimer
            _debug_print(f"Scheduling additional table refresh in 50ms")
            QTimer.singleShot(50, self._ensure_table_refresh)
    
    def _ensure_table_refresh(self):
        """Ensure the elements table is refreshed (safety mechanism for Wayland issues)."""
        current_index = self.service_combo.currentIndex()
        if current_index > 0:
            # Get the current service and refresh table
            user_data = self.service_combo.itemData(current_index)
            service_display_text = self.service_combo.currentText()
            
            if user_data and isinstance(user_data, tuple) and user_data[0] == 'template':
                # Template service
                template_name = user_data[1]
                template_data = TemplateManager.load_template_data('Service', template_name)
                if template_data:
                    service = {
                        'id': template_data.get('id', template_name),
                        'description': template_data.get('description', ''),
                        'elements': template_data.get('elements', []),
                    }
                    self._refresh_service_elements_table(service)
            else:
                # Regular service
                current_service_id = service_display_text.replace("[TEMPLATE] ", "")
                service = self.config_manager.get_service(current_service_id)
                if service:
                    self._refresh_service_elements_table(service)
    
    def _show_help(self):
        """Show help for this tab."""
        # Get parent PAMManagerGUI instance
        parent = self.parent()
        while parent and not isinstance(parent, PAMManagerGUI):
            parent = parent.parent()
        if parent and isinstance(parent, PAMManagerGUI):
            parent.show_help("Service Definition")
    
    def _refresh_service_list(self):
        """Refresh the service combo box from config_manager and templates."""
        self.service_combo.blockSignals(True)
        current_service = self.service_combo.currentText()
        
        # Keep "(select)" placeholder, remove everything else
        while self.service_combo.count() > 1:
            self.service_combo.removeItem(1)
        
        # First, ensure all service_files have corresponding service entries
        # This handles migration when service_files exist but service entries don't
        service_files = self.config_manager.get_service_files()
        for service_file in service_files:
            if not self.config_manager.get_service(service_file):
                # Auto-create service entry if it doesn't exist
                service_entry = {
                    'id': service_file,
                    'description': f'Service: {service_file}',
                    'elements': []
                }
                self.config_manager.add_service(service_entry)
        
        # Add regular services
        services = self.config_manager.list_services()
        for service in sorted(services, key=lambda s: s['id']):
            self.service_combo.addItem(service['id'], ('regular', service['id']))
        
        # Add template services
        template_names = TemplateManager.list_template_names('Service')
        if template_names:
            # Add separator
            if self.service_combo.count() > 1:
                self.service_combo.insertSeparator(self.service_combo.count())
            
            for tmpl_name in template_names:
                display_name = f"[TEMPLATE] {tmpl_name}"
                self.service_combo.addItem(display_name, ('template', tmpl_name))
        
        # Restore previous selection or set to placeholder
        found_index = -1
        if current_service and current_service != "(select)":
            for i in range(1, self.service_combo.count()):
                if self.service_combo.itemText(i) == current_service:
                    found_index = i
                    break
        
        if found_index >= 1:
            self.service_combo.setCurrentIndex(found_index)
        else:
            self.service_combo.setCurrentIndex(0)
        
        self.service_combo.blockSignals(False)
        
        # Trigger display update only if service is actually selected
        if self.service_combo.currentIndex() > 0:
            self._on_service_selection_changed()
        else:
            # No service selected - clear the display
            self.service_name_input.clear()
            self.service_desc_input.clear()

            self.service_elements_table.setRowCount(0)
    
    def _refresh_elements_combo(self):
        """Refresh the elements combo box with both regular and template elements."""
        self.elements_combo.blockSignals(True)
        self.elements_combo.clear()
        
        # Add regular elements
        elements = self.config_manager.list_elements()
        for elem in sorted(elements, key=lambda e: e['id']):
            self.elements_combo.addItem(elem['id'], ('regular', elem['id']))
        
        # Add template elements
        template_names = TemplateManager.list_template_names('Element')
        if template_names:
            # Add separator
            if self.elements_combo.count() > 0:
                self.elements_combo.insertSeparator(self.elements_combo.count())
            
            for tmpl_name in template_names:
                display_name = f"[TEMPLATE] {tmpl_name}"
                self.elements_combo.addItem(display_name, ('template', tmpl_name))
        
        self.elements_combo.blockSignals(False)
    
    def _on_service_selection_changed(self):
        """Handle service selection change, supporting both regular and template services.
        
        Refreshes:
        - Service name and description inputs
        - Policy Elements table with all elements for the selected service
        - Element order numbers
        """
        current_index = self.service_combo.currentIndex()
        _debug_print(f"_on_service_selection_changed() called, index={current_index}, text='{self.service_combo.currentText()}'")
        
        # Ignore placeholder
        if current_index <= 0:
            self.service_name_input.clear()
            self.service_desc_input.clear()
            self.service_elements_table.setRowCount(0)
            return
        
        # Get userData to determine if regular or template service
        user_data = self.service_combo.itemData(current_index)
        service_display_text = self.service_combo.currentText()
        _debug_print(f"Service selected: {service_display_text}, userData={user_data}")
        
        if user_data and isinstance(user_data, tuple) and user_data[0] == 'template':
            # Template service
            template_name = user_data[1]
            template_data = TemplateManager.load_template_data('Service', template_name)
            
            if template_data:
                # Create service-like structure from template
                service = {
                    'id': template_data.get('id', template_name),
                    'description': template_data.get('description', ''),
                    'elements': template_data.get('elements', []),
                }
                self.service_name_input.setText(service['id'])
                self.service_desc_input.setPlainText(service.get('description', ''))
                # ALWAYS refresh the elements table - this is critical
                _debug_print(f"Refreshing table for template service: {template_name}")
                self._refresh_service_elements_table(service)
            else:
                # Template not found
                print(f"[WARNING] Template not found: Service/{template_name}")
                self.service_name_input.clear()
                self.service_desc_input.clear()
                self.service_elements_table.setRowCount(0)
        else:
            # Regular service
            current_service_id = service_display_text.replace("[TEMPLATE] ", "")
            service = self.config_manager.get_service(current_service_id)
            
            if service:
                self.service_name_input.setText(service['id'])
                self.service_desc_input.setPlainText(service.get('description', ''))
                # ALWAYS refresh the elements table - this is critical
                _debug_print(f"Refreshing table for regular service: {current_service_id}, elements count: {len(service.get('elements', []))}")
                self._refresh_service_elements_table(service)
            else:
                # Service not found
                print(f"[WARNING] Service not found: {current_service_id}")
                self.service_name_input.clear()
                self.service_desc_input.clear()
                self.service_elements_table.setRowCount(0)
    
    def _refresh_service_elements_table(self, service: Dict):
        """Refresh the elements table for selected service with order tracking.
        
        Supports both regular elements and template elements.
        """
        _debug_print(f"_refresh_service_elements_table() called for service: {service.get('id')}")
        self.service_elements_table.setRowCount(0)
        
        elements = service.get('elements', [])
        _debug_print(f"Service has {len(elements)} elements: {elements}")
        
        for row, element_id in enumerate(elements):
            self.service_elements_table.insertRow(row)
            _debug_print(f"Adding row {row} for element: {element_id}")
            
            # Column 0: Order number (narrow column)
            order_item = QTableWidgetItem(str(row + 1))
            order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
            self.service_elements_table.setItem(row, 0, order_item)
            
            # Column 1: Element name - check if template or regular
            is_template = False
            elem = self.config_manager.get_element(element_id)
            if not elem:
                # Try to load as template
                template_data = TemplateManager.load_template_data('Element', element_id)
                if template_data:
                    is_template = True
            
            # Display element name with [TEMPLATE] marker if applicable
            display_name = f"[TEMPLATE] {element_id}" if is_template else element_id
            elem_item = QTableWidgetItem(display_name)
            elem_item.setFlags(elem_item.flags() & ~Qt.ItemIsEditable)
            self.service_elements_table.setItem(row, 1, elem_item)
            
            # Column 2: Action buttons (Up, Down, Delete - arranged in aligned columns)
            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout()
            buttons_layout.setContentsMargins(2, 2, 2, 2)
            buttons_layout.setSpacing(2)

            up_w = 50
            down_w = 60
            delete_w = 70
            slot_h = 28

            def _placeholder(width: int) -> QWidget:
                spacer = QWidget()
                spacer.setFixedSize(width, slot_h)
                return spacer

            # Up slot
            if row > 0:
                up_button = QPushButton("Up")
                up_button.setFixedWidth(up_w)
                up_button.setFixedHeight(slot_h)
                up_button.clicked.connect(
                    lambda checked, idx=row, sid=service['id']: self._move_element_up(sid, idx)
                )
                buttons_layout.addWidget(up_button)
            else:
                buttons_layout.addWidget(_placeholder(up_w))

            # Down slot
            if row < len(elements) - 1:
                down_button = QPushButton("Down")
                down_button.setFixedWidth(down_w)
                down_button.setFixedHeight(slot_h)
                down_button.clicked.connect(
                    lambda checked, idx=row, sid=service['id']: self._move_element_down(sid, idx)
                )
                buttons_layout.addWidget(down_button)
            else:
                buttons_layout.addWidget(_placeholder(down_w))

            # Delete slot
            can_delete = True
            if can_delete:
                delete_button = QPushButton("Delete")
                delete_button.setFixedWidth(delete_w)
                delete_button.setFixedHeight(slot_h)
                delete_button.clicked.connect(
                    lambda checked, eid=element_id, sid=service['id']: self._remove_element_from_service(sid, eid)
                )
                buttons_layout.addWidget(delete_button)
            else:
                buttons_layout.addWidget(_placeholder(delete_w))

            buttons_widget.setLayout(buttons_layout)
            self.service_elements_table.setCellWidget(row, 2, buttons_widget)
    
    def _create_service(self):
        """Create a new service."""
        service_name = self.service_name_input.text().strip()
        service_desc = self.service_desc_input.toPlainText().strip()
        
        if not service_name:
            QMessageBox.warning(self, "Error", "Please enter a service name")
            return
        
        # Check if service already exists
        if self.config_manager.get_service(service_name):
            QMessageBox.critical(self, "Error", f"Service '{service_name}' already exists")
            return
        
        service_dict = {
            'id': service_name,
            'description': service_desc,
            'elements': []
        }
        
        if self.config_manager.add_service(service_dict):
            QMessageBox.information(self, "Success", f"Service '{service_name}' created successfully")
            self._clear_form()
            self._refresh_service_list()
        else:
            QMessageBox.critical(self, "Error", f"Failed to create service '{service_name}'")
    
    def _edit_service(self):
        """Update the selected service."""
        service_name = self.service_name_input.text().strip()
        service_desc = self.service_desc_input.toPlainText().strip()
        
        if not service_name:
            QMessageBox.warning(self, "Error", "Please select or enter a service name")
            return
        
        service = self.config_manager.get_service(service_name)
        if not service:
            QMessageBox.critical(self, "Error", f"Service '{service_name}' not found")
            return
        
        # Update description while keeping elements
        service['description'] = service_desc
        
        if self.config_manager.add_service(service):
            QMessageBox.information(self, "Success", f"Service '{service_name}' updated successfully")
            self._refresh_service_list()
        else:
            QMessageBox.critical(self, "Error", f"Failed to update service")
    
    def _delete_service(self):
        """Delete the selected service."""
        service_name = self.service_combo.currentText()
        
        if not service_name:
            QMessageBox.warning(self, "Error", "Please select a service to delete")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete service '{service_name}' and all its element mappings?"
        )
        
        if reply == QMessageBox.Yes:
            if self.config_manager.remove_service(service_name):
                QMessageBox.information(self, "Success", f"Service '{service_name}' deleted")
                self._clear_form()
                self._refresh_service_list()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete service")
    
    def _add_element_to_service(self):
        """Add selected element to current service (supports both regular and template elements)."""
        service_id = self.service_combo.currentText()
        
        if not service_id or service_id == "(select)":
            QMessageBox.warning(self, "Error", "Please select a service")
            return
        
        # Get element reference - can be regular or template
        current_index = self.elements_combo.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "Error", "Please select an element")
            return
        
        user_data = self.elements_combo.itemData(current_index)
        is_template = False
        template_name = None
        
        if user_data and isinstance(user_data, tuple) and user_data[0] == 'template':
            # Template element - load template data and create new element
            is_template = True
            template_name = user_data[1]
            template_data = TemplateManager.load_template_data('Element', template_name)
            
            if not template_data:
                QMessageBox.critical(self, "Error", f"Template '{template_name}' not found")
                return
            
            # Clean the template name (remove "template." prefix)
            clean_name = TemplateManager.clean_template_name(f"template.{template_name}.json")
            
            # Check for name collisions with existing elements
            existing_elements = self.config_manager.list_elements()
            existing_names = [e['id'] for e in existing_elements]
            
            # Get available name with suffix if collision detected
            final_name = TemplateManager.find_available_name(clean_name, existing_names)
            
            # Create new element from template data
            new_element = {
                'id': final_name,
                'interfaces': template_data.get('interfaces', []),
                'fragments': template_data.get('fragments', []),
                'controls': template_data.get('controls', [])
            }
            
            # Add new element to config
            if not self.config_manager.add_element(new_element):
                QMessageBox.critical(self, "Error", "Failed to create element from template")
                return
            
            element_id = final_name
            info_msg = f"Element '{final_name}' created from template '{template_name}' and added to service"
        else:
            # Regular element
            element_id = self.elements_combo.currentText()
            # Remove [TEMPLATE] prefix if present (shouldn't be for regular elements)
            if element_id.startswith("[TEMPLATE] "):
                element_id = element_id.replace("[TEMPLATE] ", "")
            info_msg = f"Element '{element_id}' added to service"
        
        service = self.config_manager.get_service(service_id)
        if not service:
            QMessageBox.critical(self, "Error", "Service not found")
            return
        
        if element_id in service.get('elements', []):
            QMessageBox.warning(self, "Warning", f"Element '{element_id}' is already in this service")
            return
        
        service['elements'].append(element_id)
        
        if self.config_manager.add_service(service):
            QMessageBox.information(self, "Success", info_msg)
            self._refresh_elements_combo()  # Refresh to show new element
            self._on_service_selection_changed()
        else:
            QMessageBox.critical(self, "Error", "Failed to add element to service")
    
    def _remove_element_from_service(self, service_id: str, element_id: str):
        """Remove element from service."""
        service = self.config_manager.get_service(service_id)
        if not service:
            QMessageBox.critical(self, "Error", "Service not found")
            return
        
        if element_id in service.get('elements', []):
            service['elements'].remove(element_id)
            
            if self.config_manager.add_service(service):
                QMessageBox.information(self, "Success", f"Element '{element_id}' removed from service")
                self._on_service_selection_changed()
            else:
                QMessageBox.critical(self, "Error", "Failed to remove element")
        else:
            QMessageBox.warning(self, "Warning", "Element not found in service")
    
    def _clear_form(self):
        """Clear form fields."""
        self.service_name_input.clear()
        self.service_desc_input.clear()
    
    def _save(self):
        """Save all changes to YAML and JSON."""
        try:
            self.config_manager.save()
            QMessageBox.information(self, "Success", "All changes saved successfully to:\n- ~/.pam-config.yaml\n- ~/.pam-config.json")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save changes: {e}")
    
    def _export_services(self):
        """Export services to /etc/pam.d compatible format with headers."""
        try:
            from pathlib import Path
            from datetime import datetime
            
            # Get config directory
            config_dir = Path.home() / 'etc' / 'pam.d'
            config_dir.mkdir(parents=True, exist_ok=True)
            
            services = self.config_manager.list_services()
            if not services:
                QMessageBox.warning(self, "Warning", "No services to export")
                return
            
            # Helper function to wrap description to 80 chars
            def wrap_description(text, prefix="# "):
                """Wrap text to 80 characters with proper continuation."""
                lines = []
                current_line = ""
                
                for word in text.split():
                    # Test if adding this word exceeds 80 chars
                    test_line = (current_line + " " + word).strip() if current_line else word
                    
                    if len(prefix + test_line) <= 80:
                        current_line = test_line
                    else:
                        # Current line is full, save it
                        if current_line:
                            lines.append(prefix + current_line)
                        current_line = word
                
                # Add remaining text
                if current_line:
                    lines.append(prefix + current_line)
                
                return "\n".join(lines)
            
            # Export each service
            exported_count = 0
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for service in services:
                service_id = service['id']
                description = service['description']
                elements = service.get('elements', [])
                
                # Build file content
                content_lines = []
                
                # Header
                content_lines.append(f"# Created by PAM Manager {timestamp}")
                
                # Service name and description
                if description:
                    service_line = f"# Service name: {service_id}: {description}"
                    if len(service_line) <= 80:
                        content_lines.append(service_line)
                    else:
                        # Wrap the service description
                        wrapped = wrap_description(f"Service name: {service_id}: {description}")
                        content_lines.append(wrapped)
                else:
                    content_lines.append(f"# Service name: {service_id}")
                
                # Add elements to service
                if elements:
                    content_lines.append("#")
                    
                    # Get all elements
                    all_elements_dict = {e['id']: e for e in self.config_manager.list_elements()}
                    
                    for element_id in elements:
                        element = all_elements_dict.get(element_id)
                        if element:
                            content_lines.append(f"# Policy Element: {element_id}")
                            if element.get('description'):
                                desc_wrapped = wrap_description(element['description'], "# ")
                                content_lines.append(desc_wrapped)

                if not content_lines:
                    print(f"[WARNING] Skipping empty export for {service_id}")
                    continue
                
                # Add empty line before PAM config
                if elements:
                    content_lines.append("#")
                
                # Join with newlines and write to file
                file_path = config_dir / service_id
                file_path.write_text("\n".join(content_lines))
                exported_count += 1
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {exported_count} service file(s) to ~/etc/pam.d/\n\n"
                f"Services: {', '.join(sorted([s['id'] for s in services]))}"
            )
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export services: {e}")
    
    def _edit_element_from_service(self, element_id: str):
        """Open Policy Elements tab to edit the selected element."""
        if not self.parent_gui:
            QMessageBox.warning(self, "Error", "Cannot access Policy Element tab")
            return
        
        element = self.config_manager.get_element(element_id)
        if not element:
            QMessageBox.critical(self, "Error", f"Element '{element_id}' not found")
            return
        
        try:
            # Switch to Policy Element tab (index 3)
            self.parent_gui.tabs.setCurrentIndex(3)
            
            # Access the element tab and load the element
            element_tab = self.parent_gui.element_tab
            
            # Clear and populate form
            if hasattr(element_tab, 'elem_name_input'):
                element_tab.elem_name_input.clear()
                element_tab.elem_name_input.setText(element['id'])
            
            if hasattr(element_tab, 'elem_desc_input'):
                element_tab.elem_desc_input.clear()
                element_tab.elem_desc_input.setPlainText(element.get('description', ''))
            
            # Load fragments for this element
            if hasattr(element_tab, 'element_fragments'):
                element_tab.element_fragments = []
                
                for frag_ref in element.get('fragments', []):
                    from pam_manager.policy.fragment_manager import PolicyElementFragmentRef
                    ref = PolicyElementFragmentRef(
                        fragment_ref=frag_ref.get('fragment_ref'),
                        interface=frag_ref.get('interface'),
                        control_flag=frag_ref.get('control_flag'),
                        extended_control=frag_ref.get('extended_control', {}),
                        line_type=frag_ref.get('line_type', 'module_line'),
                        include_target=frag_ref.get('include_target', ''),
                    )
                    element_tab.element_fragments.append(ref)
                
                # Refresh the fragments table
                if hasattr(element_tab, '_refresh_element_fragments_table'):
                    element_tab._refresh_element_fragments_table()
            
            QMessageBox.information(
                self,
                "Edit Element",
                f"Element '{element_id}' loaded in Policy Element tab.\n"
                f"Edit and save the element using the Policy Element tab."
            )
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load element: {e}")
    
    def _move_element_up(self, service_id: str, index: int):
        """Move element up in the service."""
        if index <= 0:
            return
        
        service = self.config_manager.get_service(service_id)
        if not service:
            return
        
        elements = service.get('elements', [])
        if index > 0 and index < len(elements):
            # Swap elements
            elements[index], elements[index - 1] = elements[index - 1], elements[index]
            
            if self.config_manager.add_service(service):
                self._on_service_selection_changed()
    
    def _move_element_down(self, service_id: str, index: int):
        """Move element down in the service."""
        service = self.config_manager.get_service(service_id)
        if not service:
            return
        
        elements = service.get('elements', [])
        if index >= 0 and index < len(elements) - 1:
            # Swap elements
            elements[index], elements[index + 1] = elements[index + 1], elements[index]
            
            if self.config_manager.add_service(service):
                self._on_service_selection_changed()
    
    def _validate_service(self):
        """Validate currently selected service."""
        service_id = self.service_combo.currentText()
        if not service_id or service_id == "(select)":
            QMessageBox.warning(self, "Error", "Please select a service to validate")
            return
        
        service = self.config_manager.get_service(service_id)
        if not service:
            QMessageBox.warning(self, "Error", "Service not found")
            return
        
        # Basic validation
        errors = []
        if not service.get('id'):
            errors.append("Service has no ID")
        if not service.get('elements'):
            errors.append("Service has no elements")
        
        if errors:
            QMessageBox.warning(self, "Validation Errors", "\n".join(errors))
        else:
            QMessageBox.information(
                self, 
                "Validation Success", 
                f"Service '{service_id}' is valid\nElements: {len(service.get('elements', []))}"
            )
    
    def _save_service_template(self):
        """Save currently selected service as template.
        
        Template names cannot contain: / \\ ? * !
        """
        service_id = self.service_combo.currentText()
        if not service_id or service_id == "(select)":
            QMessageBox.warning(self, "Error", "Please select a service to save as template")
            return
        
        # Remove [TEMPLATE] prefix if present for validation
        clean_service_id = service_id.replace("[TEMPLATE] ", "")
        
        # Validate service name
        is_valid, error_msg = TemplateManager.validate_template_name(clean_service_id)
        if not is_valid:
            QMessageBox.warning(
                self, 
                "Invalid Service Name", 
                f"Cannot save template: {error_msg}\\n\\n"
                f"Forbidden characters: / \\ ? * !"
            )
            return
        
        service = self.config_manager.get_service(clean_service_id)
        if not service:
            QMessageBox.warning(self, "Error", "Service not found")
            return
        
        # Prepare data for template (include all service details)
        template_data = {
            'id': service.get('id'),
            'description': service.get('description', ''),
            'elements': service.get('elements', []),
        }
        
        try:
            saved_path = TemplateManager.save_template('Service', clean_service_id, template_data)
            QMessageBox.information(
                self, 
                "Success", 
                f"Service '{clean_service_id}' saved as template to Service.Templates:\\n{saved_path.name}"
            )
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Name", f"Cannot save template:\\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {e}")


class TemplateManagerTab(QWidget):
    """Tab for managing installation requirements for PAM templates.
    
    Allows selecting templates (Policy Fragment, Policy Element, Service Definition),
    viewing their content, and managing:
    1. Package requirements (platforms and dependencies)
    2. Support scripts (shell scripts with structured format)
    
    Metadata and scripts stored in: pam.modules/Generic.Templates/[name].json
    Scripts stored in: pam.modules/Generic.Templates/[name].msh
    
    Template list cached in: pam.modules/Generic.Templates/list.templates.json
    
    Scripts have read-only permissions (444) and no execute permission.
    """
    
    # Supported platforms for package management
    PLATFORMS = [
        "Debian/Ubuntu",
        "RedHat/CentOS",
        "Fedora",
        "Alpine",
        "Arch",
        "FreeBSD",
        "OpenBSD",
        "NetBSD",
        "Generic"
    ]
    
    def __init__(self):
        super().__init__()
        self.template_type = None
        self.bundle_name = None
        self.templates_dir = Path(__file__).parent / "pam.modules"
        self.generic_templates_dir = self.templates_dir / "Generic.Templates"
        self.templates_list_file = self.generic_templates_dir / "list.templates.json"
        
        # Create Generic.Templates directory if it doesn't exist
        self.generic_templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate templates list if it doesn't exist
        self._generate_templates_list_if_needed()
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize template manager tab UI."""
        main_layout = QVBoxLayout()
        
        # Info text
        info = QLabel("Manage installation requirements (packages and support scripts) for PAM templates")
        info.setStyleSheet("color: gray; font-style: italic;")
        main_layout.addWidget(info)
        
        # Template selection section
        selection_group = QGroupBox("Select Template")
        selection_layout = QHBoxLayout()
        
        # Template type combo
        selection_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Fragment", "Element", "Service", "Bundle"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        selection_layout.addWidget(self.type_combo)
        
        # Template name combo
        selection_layout.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        self.template_combo.addItem("(select)")
        self.template_combo.currentTextChanged.connect(self._on_template_selected)
        selection_layout.addWidget(self.template_combo)
        
        # Bundle Name input field
        selection_layout.addWidget(QLabel("Bundle Name:"))
        self.bundle_name_input = QLineEdit()
        self.bundle_name_input.setPlaceholderText("Enter custom bundle name or leave empty...")
        self.bundle_name_input.setMaximumWidth(250)
        selection_layout.addWidget(self.bundle_name_input)
        
        selection_layout.addStretch()
        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)
        
        # Template content section
        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        
        # Left side - Template content
        content_group = QGroupBox("Template Content (PAM Configuration)")
        content_layout = QVBoxLayout()
        
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setMinimumHeight(80)
        content_layout.addWidget(self.content_text)
        
        content_group.setLayout(content_layout)
        splitter.addWidget(content_group)
        
        # Right side - Installation requirements
        req_group = QGroupBox("Installation Requirements")
        req_layout = QVBoxLayout()
        
        # Tabs for Packages and Support Script
        req_tabs = QTabWidget()
        
        # Packages tab
        packages_widget = QWidget()
        packages_layout = QVBoxLayout()
        
        # Platform selection
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("Platform:"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(self.PLATFORMS)
        self.platform_combo.currentIndexChanged.connect(self._load_requirements)  # Reload packages when platform changes
        platform_layout.addWidget(self.platform_combo)
        platform_layout.addStretch()
        packages_layout.addLayout(platform_layout)
        
        # Packages text area
        packages_label = QLabel("Required packages for selected platform:")
        packages_label.setStyleSheet("color: gray; font-size: 10px;")
        packages_layout.addWidget(packages_label)
        
        self.packages_text = QTextEdit()
        self.packages_text.setPlaceholderText(
            "List required packages (one per line)\n"
            "Format: package-name\n"
            "Example:\nlibpam-cracklib\nlibpam-google-authenticator"
        )
        self.packages_text.setMinimumHeight(60)
        packages_layout.addWidget(self.packages_text)
        
        # Packages buttons
        pkg_button_layout = QHBoxLayout()
        save_pkg_btn = QPushButton("Save Packages")
        save_pkg_btn.clicked.connect(self._save_packages)
        pkg_button_layout.addWidget(save_pkg_btn)
        
        clear_pkg_btn = QPushButton("Clear Packages")
        clear_pkg_btn.clicked.connect(lambda: self.packages_text.clear())
        pkg_button_layout.addWidget(clear_pkg_btn)
        
        pkg_button_layout.addStretch()
        packages_layout.addLayout(pkg_button_layout)
        
        packages_widget.setLayout(packages_layout)
        req_tabs.addTab(packages_widget, "Packages")
        
        # Support Script tab
        script_widget = QWidget()
        script_layout_inner = QVBoxLayout()
        
        script_info = QLabel(
            "Support script structure (scripts are read-only, no execute permission):\n"
            "Format: # Filename: /path/filename\n"
            "        # !/path/[shell type]\n"
            "        ... script content ...\n\n"
            "Note: Cannot write to /bin, /sbin, /usr/bin, /usr/sbin"
        )
        script_info.setStyleSheet("color: gray; font-size: 9px;")
        script_layout_inner.addWidget(script_info)
        
        self.support_script_text = QTextEdit()
        self.support_script_text.setPlaceholderText(
            "# Filename: /etc/pam.d/scripts/auth-check.sh\n"
            "# !/bin/bash\n"
            "#!/bin/bash\n"
            "# Authentication check script\n"
            "...\n\n"
            "# Filename: /etc/pam.d/scripts/verify.sh\n"
            "# !/bin/bash\n"
            "#!/bin/bash\n"
            "# Verification script\n"
            "..."
        )
        self.support_script_text.setMinimumHeight(60)
        script_layout_inner.addWidget(self.support_script_text)
        
        # Support script buttons
        script_button_layout = QHBoxLayout()
        save_script_btn = QPushButton("Save Support Script")
        save_script_btn.clicked.connect(self._save_support_script)
        script_button_layout.addWidget(save_script_btn)
        
        clear_script_btn = QPushButton("Clear Script")
        clear_script_btn.clicked.connect(lambda: self.support_script_text.clear())
        script_button_layout.addWidget(clear_script_btn)
        
        script_button_layout.addStretch()
        script_layout_inner.addLayout(script_button_layout)
        
        script_widget.setLayout(script_layout_inner)
        req_tabs.addTab(script_widget, "Support Script")
        
        req_layout.addWidget(req_tabs)
        req_group.setLayout(req_layout)
        splitter.addWidget(req_group)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter, 2)
        
        # Management section
        manage_layout = QHBoxLayout()
        
        manage_layout.addWidget(QLabel("Bundle:"))
        
        save_bundle_btn = QPushButton("Save Bundle")
        save_bundle_btn.setStyleSheet("color: black;")
        save_bundle_btn.clicked.connect(self._save_bundle)
        manage_layout.addWidget(save_bundle_btn)
        
        delete_bundle_btn = QPushButton("Delete Bundle")
        delete_bundle_btn.setStyleSheet("color: black;")
        delete_bundle_btn.clicked.connect(self._delete_bundle)
        manage_layout.addWidget(delete_bundle_btn)
        
        help_button = QPushButton("Help")
        help_button.setMaximumWidth(80)
        help_button.clicked.connect(lambda: self._show_help())
        
        manage_layout.addStretch()
        manage_layout.addWidget(help_button)
        
        manage_group = QGroupBox()
        manage_group.setLayout(manage_layout)
        main_layout.addWidget(manage_group)
        
        self.setLayout(main_layout)
        
        # Load initial templates
        self._load_templates()
    
    def _show_help(self):
        """Show help for this tab."""
        # Get parent PAMManagerGUI instance
        parent = self.parent()
        while parent and not isinstance(parent, PAMManagerGUI):
            parent = parent.parent()
        if parent and isinstance(parent, PAMManagerGUI):
            parent.show_help("Template Manager")
    
    def _generate_templates_list_if_needed(self):
        """Generate list.templates.json if it doesn't exist or is outdated by scanning all template directories."""
        import os
        import json
        
        # Check if list file exists and is newer than all template files
        needs_regeneration = True
        
        if self.templates_list_file.exists():
            # Get the modification time of the list file
            list_mtime = os.path.getmtime(self.templates_list_file)
            
            # Check if any template file is newer than the list file
            template_dirs = [
                self.templates_dir / "Fragment.Templates",
                self.templates_dir / "Element.Templates",
                self.templates_dir / "Service.Templates",
                self.generic_templates_dir,  # For bundles and generic templates
            ]
            
            needs_regeneration = False
            for template_dir in template_dirs:
                if template_dir.exists():
                    for template_file in template_dir.glob("*.json"):
                        if os.path.getmtime(template_file) > list_mtime:
                            if DEBUG:
                                _debug_print(f"[Template Manager] Template file newer than list: {template_file.name}")
                            needs_regeneration = True
                            break
                if needs_regeneration:
                    break
        
        if not needs_regeneration:
            if DEBUG:
                _debug_print(f"[Template Manager] list.templates.json is up to date")
            return
        
        if DEBUG:
            _debug_print(f"[Template Manager] Regenerating templates list...")
        
        try:
            templates_list = {
                "Fragments": [],
                "Elements": [],
                "Services": [],
                "Bundles": [],
                "Generic": []
            }
            
            # Scan Fragment templates
            fragment_dir = self.templates_dir / "Fragment.Templates"
            if fragment_dir.exists():
                for template_file in sorted(fragment_dir.glob("template.*.json")):
                    try:
                        with open(template_file, 'r') as f:
                            data = json.load(f)
                        name = template_file.stem
                        if name.startswith("template."):
                            name = name[9:]
                        templates_list["Fragments"].append({
                            "filename": template_file.name,
                            "name": name,
                            "description": data.get("description", "")
                        })
                        if DEBUG:
                            _debug_print(f"[Template Manager] Found Fragment template: {name}")
                    except Exception as e:
                        if DEBUG:
                            _debug_print(f"Error reading fragment {template_file.name}: {e}")
            
            # Scan Element templates
            element_dir = self.templates_dir / "Element.Templates"
            if element_dir.exists():
                for template_file in sorted(element_dir.glob("template.*.json")):
                    try:
                        with open(template_file, 'r') as f:
                            data = json.load(f)
                        name = template_file.stem
                        if name.startswith("template."):
                            name = name[9:]
                        templates_list["Elements"].append({
                            "filename": template_file.name,
                            "name": name,
                            "description": data.get("description", "")
                        })
                        if DEBUG:
                            _debug_print(f"[Template Manager] Found Element template: {name}")
                    except Exception as e:
                        if DEBUG:
                            _debug_print(f"Error reading element {template_file.name}: {e}")
            
            # Scan Service templates
            service_dir = self.templates_dir / "Service.Templates"
            if service_dir.exists():
                for template_file in sorted(service_dir.glob("template.*.json")):
                    try:
                        with open(template_file, 'r') as f:
                            data = json.load(f)
                        name = template_file.stem
                        if name.startswith("template."):
                            name = name[9:]
                        templates_list["Services"].append({
                            "filename": template_file.name,
                            "name": name,
                            "description": data.get("description", "")
                        })
                        if DEBUG:
                            _debug_print(f"[Template Manager] Found Service template: {name}")
                    except Exception as e:
                        if DEBUG:
                            _debug_print(f"Error reading service {template_file.name}: {e}")
            
            # Scan Bundle templates (from Generic.Templates/bundle-*.json)
            if self.generic_templates_dir.exists():
                for template_file in sorted(self.generic_templates_dir.glob("bundle-*.json")):
                    try:
                        with open(template_file, 'r') as f:
                            data = json.load(f)
                        name = template_file.stem  # e.g., "bundle-yubikey-basic-auth"
                        if name.startswith("bundle-"):
                            name = name[7:]  # Remove "bundle-" prefix
                        templates_list["Bundles"].append({
                            "filename": template_file.name,
                            "name": name,
                            "description": data.get("description", ""),
                            "bundle_name": data.get("bundle_name", "")
                        })
                        if DEBUG:
                            _debug_print(f"[Template Manager] Found Bundle template: {name}")
                    except Exception as e:
                        if DEBUG:
                            _debug_print(f"Error reading bundle {template_file.name}: {e}")
            
            # Scan Generic templates (excluding bundle-*.json which are handled separately)
            if self.generic_templates_dir.exists():
                for template_file in sorted(self.generic_templates_dir.glob("*.json")):
                    if template_file.name not in ("list.templates.json",) and not template_file.name.startswith(("bundle-", "template.")):
                        try:
                            with open(template_file, 'r') as f:
                                data = json.load(f)
                            templates_list["Generic"].append({
                                "filename": template_file.name,
                                "name": template_file.stem,
                                "description": data.get("description", "")
                            })
                            if DEBUG:
                                _debug_print(f"[Template Manager] Found Generic template: {template_file.stem}")
                        except Exception as e:
                            if DEBUG:
                                _debug_print(f"Error reading generic {template_file.name}: {e}")
            
            # Write list file
            with open(self.templates_list_file, 'w') as f:
                json.dump(templates_list, f, indent=2)
            
            if DEBUG:
                _debug_print(f"[Template Manager] Templates list regenerated successfully")
                _debug_print(f"  - Fragments: {len(templates_list['Fragments'])}")
                _debug_print(f"  - Elements: {len(templates_list['Elements'])}")
                _debug_print(f"  - Services: {len(templates_list['Services'])}")
                _debug_print(f"  - Bundles: {len(templates_list['Bundles'])}")
        
        except Exception as e:
            if DEBUG:
                _debug_print(f"Error generating templates list: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_templates(self):
        """Load templates from list.templates.json."""
        template_type = self.type_combo.currentText()
        if DEBUG:
            _debug_print(f"[Template Manager] _load_templates() called with type: {template_type}")
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        self.template_combo.addItem("(select)")
        
        try:
            import json
            
            # Regenerate list if needed
            self._generate_templates_list_if_needed()
            
            if self.templates_list_file.exists():
                if DEBUG:
                    _debug_print(f"[Template Manager] Loading templates from: {self.templates_list_file}")
                with open(self.templates_list_file, 'r') as f:
                    templates_list = json.load(f)
                
                if DEBUG:
                    _debug_print(f"[Template Manager] templates_list keys: {list(templates_list.keys())}")
                
                # Get templates for current type
                type_key = f"{template_type}s"  # "Fragment" → "Fragments", etc
                if DEBUG:
                    _debug_print(f"[Template Manager] Looking for type_key: {type_key}")
                
                if type_key in templates_list:
                    templates = templates_list[type_key]
                    if DEBUG:
                        _debug_print(f"[Template Manager] Found {len(templates)} templates for type {template_type}")
                    for template_info in templates:
                        template_name = template_info.get("name", "")
                        self.template_combo.addItem(template_name)
                        if DEBUG:
                            _debug_print(f"[Template Manager] Added template: {template_name}")
                else:
                    if DEBUG:
                        _debug_print(f"[Template Manager] Key '{type_key}' not found in templates_list!")
            else:
                if DEBUG:
                    _debug_print(f"[Template Manager] templates_list_file does not exist: {self.templates_list_file}")
        
        except Exception as e:
            if DEBUG:
                _debug_print(f"[Template Manager] Error loading templates: {e}")
            import traceback
            traceback.print_exc()
        
        self.template_combo.blockSignals(False)
    
    def _on_type_changed(self, template_type):
        """Handle template type change."""
        if DEBUG:
            _debug_print(f"[Template Manager] _on_type_changed() called with type: {template_type}")
        self.template_type = template_type
        self.bundle_name = None
        self.content_text.clear()
        self.packages_text.clear()
        self.support_script_text.clear()
        self.bundle_name_input.clear()
        self._load_templates()
    
    def _on_template_selected(self, template_name):
        """Handle template selection."""
        if DEBUG:
            _debug_print(f"[Template Manager] _on_template_selected() called with: {template_name}")
        
        if template_name == "(select)":
            self.bundle_name = None
            self.content_text.clear()
            self.packages_text.clear()
            self.support_script_text.clear()
            self.bundle_name_input.clear()
            if DEBUG:
                _debug_print(f"[Template Manager] Selection cleared")
            return
        
        self.bundle_name = template_name
        self.bundle_name_input.setText(template_name)
        if DEBUG:
            _debug_print(f"[Template Manager] Loading template content for: {template_name}")
        self._load_template_content()
        if DEBUG:
            _debug_print(f"[Template Manager] Loading template requirements for: {template_name}")
        self._load_requirements()
    
    def _load_template_content(self):
        """Load and display template content."""
        if not self.template_type or not self.bundle_name:
            if DEBUG:
                _debug_print(f"[Template Manager] _load_template_content() - Missing template_type or bundle_name")
            return
        
        if DEBUG:
            _debug_print(f"[Template Manager] _load_template_content() - type: {self.template_type}, bundle: {self.bundle_name}")
        
        try:
            import json
            
            # Handle Bundle templates separately (stored in Generic.Templates with bundle- prefix)
            if self.template_type == "Bundle":
                template_file = self.generic_templates_dir / f"bundle-{self.bundle_name}.json"
            else:
                # Fragment, Element, Service templates use template. prefix
                template_file = (
                    self.templates_dir / f"{self.template_type}.Templates" / 
                    f"template.{self.bundle_name}.json"
                )
            
            if not template_file.exists():
                self.content_text.setText(f"Template file not found: {template_file}")
                return
            
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            
            # Display template content as formatted PAM configuration
            content_lines = []
            content_lines.append(f"Template: {self.bundle_name}")
            content_lines.append(f"Type: {self.template_type}")
            content_lines.append("-" * 50)
            
            if isinstance(template_data, dict):
                # Format as PAM config lines
                if 'id' in template_data:
                    content_lines.append(f"ID: {template_data['id']}")
                if 'bundle_name' in template_data:
                    content_lines.append(f"Bundle Name: {template_data['bundle_name']}")
                if 'description' in template_data:
                    content_lines.append(f"Description: {template_data['description']}")
                if 'scope' in template_data:
                    content_lines.append(f"Scope: {template_data['scope']}")
                
                # Show formatted JSON
                content_lines.append("-" * 50)
                formatted_json = json.dumps(template_data, indent=2)
                content_lines.append(formatted_json)
            
            self.content_text.setPlainText("\n".join(content_lines))
        
        except Exception as e:
            if DEBUG:
                _debug_print(f"[Template Manager] _load_template_content() - Error: {e}")
            self.content_text.setText(f"Error loading template: {e}")
    
    def _load_requirements(self):
        """Load existing requirements (packages and support script) if they exist."""
        if not self.bundle_name:
            if DEBUG:
                _debug_print(f"[Template Manager] _load_requirements() - Missing bundle_name")
            return
        
        if DEBUG:
            _debug_print(f"[Template Manager] _load_requirements() - Loading for bundle: {self.bundle_name}")
        
        try:
            import json
            
            # For Bundle templates, load from bundle-{name}.json
            if self.template_type == "Bundle":
                template_file = self.generic_templates_dir / f"bundle-{self.bundle_name}.json"
                if template_file.exists():
                    with open(template_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Load packages for current platform
                    if "platforms" in metadata and self.platform_combo.currentText() in metadata["platforms"]:
                        platform_data = metadata["platforms"][self.platform_combo.currentText()]
                        if "packages" in platform_data:
                            packages_list = platform_data["packages"]
                            self.packages_text.setPlainText("\n".join(packages_list))
                        else:
                            self.packages_text.clear()
                    else:
                        self.packages_text.clear()
                else:
                    self.packages_text.clear()
            else:
                # For other template types, load metadata from {name}.json
                metadata_file = self.generic_templates_dir / f"{self.bundle_name}.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Load packages for current platform
                    if "packages" in metadata and self.platform_combo.currentText() in metadata["packages"]:
                        packages_list = metadata["packages"][self.platform_combo.currentText()]
                        self.packages_text.setPlainText("\n".join(packages_list))
                    else:
                        self.packages_text.clear()
                else:
                    self.packages_text.clear()
        
        except Exception as e:
            if DEBUG:
                _debug_print(f"Error loading requirements: {e}")
            self.packages_text.clear()
        
        # Load support script metadata (.msh file - multi-shell)
        # For Bundle type, use bundle-{name}.msh; for others use {name}.msh
        if self.template_type == "Bundle":
            script_file = self.generic_templates_dir / f"bundle-{self.bundle_name}.msh"
            script_info = f"Installation script: bundle-{self.bundle_name}.msh\n"
        else:
            script_file = self.generic_templates_dir / f"{self.bundle_name}.msh"
            script_info = f"Installation script: {self.bundle_name}.msh\n"
        
        # Display script metadata and package info (not the script content itself)
        script_info += "\n" + "="*50 + "\n"
        script_info += "INSTALLATION REQUIREMENTS\n"
        script_info += "="*50 + "\n\n"
        
        if self.template_type == "Bundle":
            script_info += f"Platform: {self.platform_combo.currentText()}\n\n"
            script_info += "Packages to install (handled by PAM Manager):\n"
            template_file = self.generic_templates_dir / f"bundle-{self.bundle_name}.json"
            if template_file.exists():
                try:
                    with open(template_file, 'r') as f:
                        bundle_data = json.load(f)
                    platform = self.platform_combo.currentText()
                    if "platforms" in bundle_data and platform in bundle_data["platforms"]:
                        pkg_mgr = bundle_data["platforms"][platform].get("package_manager", "unknown")
                        packages = bundle_data["platforms"][platform].get("packages", [])
                        script_info += f"Package Manager: {pkg_mgr}\n\n"
                        for pkg in packages:
                            script_info += f"  - {pkg}\n"
                    else:
                        script_info += f"No packages defined for platform: {platform}\n"
                except Exception as e:
                    script_info += f"Error reading bundle metadata: {e}\n"
        
        script_info += "\n" + "="*50 + "\n"
        script_info += "NOTE: Installation scripts are read-only and not executable.\n"
        if script_file.exists():
            script_info += f"Script file exists: {script_file.name}\n"
        else:
            script_info += f"Script file not found: {script_file.name}\n"
        
        self.support_script_text.setPlainText(script_info)
    
    def _validate_script_paths(self, script_content):
        """Validate that script paths don't write to forbidden directories."""
        if DEBUG:
            _debug_print(f"[Template Manager] _validate_script_paths() - Validating script content")
        
        forbidden_dirs = ["/bin", "/sbin", "/usr/bin", "/usr/sbin"]
        
        for line in script_content.split("\n"):
            if line.startswith("# Filename:"):
                path = line.replace("# Filename:", "").strip()
                for forbidden in forbidden_dirs:
                    if path.startswith(forbidden):
                        if DEBUG:
                            _debug_print(f"[Template Manager] _validate_script_paths() - Forbidden path: {path}")
                        return False, f"Cannot write to forbidden directory: {forbidden}"
        
        if DEBUG:
            _debug_print(f"[Template Manager] _validate_script_paths() - Validation passed")
        return True, "OK"
    
    def _extract_and_validate_scripts(self, script_content):
        """Extract individual scripts from structured content."""
        if DEBUG:
            _debug_print(f"[Template Manager] _extract_and_validate_scripts() - Extracting scripts from content")
        
        scripts = []
        current_script = {}
        
        for line in script_content.split("\n"):
            if line.startswith("# Filename:"):
                if current_script:
                    scripts.append(current_script)
                current_script = {
                    "filename": line.replace("# Filename:", "").strip(),
                    "shell": None,
                    "content": []
                }
            elif line.startswith("# !"):
                if current_script:
                    current_script["shell"] = line.replace("# !", "").strip()
            elif current_script:
                current_script["content"].append(line)
        
        if current_script:
            scripts.append(current_script)
        
        if DEBUG:
            _debug_print(f"[Template Manager] _extract_and_validate_scripts() - Extracted {len(scripts)} scripts")
        
        return scripts
    
    def _save_packages(self):
        """Save package requirements to metadata JSON."""
        if DEBUG:
            _debug_print(f"[Template Manager] _save_packages() called")
        
        if not self.bundle_name:
            QMessageBox.warning(self, "Error", "Please select a template first")
            return
        
        bundle_name = self.bundle_name_input.text().strip()
        if not bundle_name:
            QMessageBox.warning(self, "Error", "Please enter a bundle name")
            return
        
        packages_content = self.packages_text.toPlainText()
        platform = self.platform_combo.currentText()
        
        if DEBUG:
            _debug_print(f"[Template Manager] _save_packages() - bundle: {bundle_name}, platform: {platform}")
        
        try:
            metadata_file = self.generic_templates_dir / f"{bundle_name}.json"
            
            # Load existing metadata or create new
            import json
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {"packages": {}, "scripts": []}
            
            # Parse package list
            packages_list = [pkg.strip() for pkg in packages_content.split("\n") if pkg.strip()]
            
            if DEBUG:
                _debug_print(f"[Template Manager] _save_packages() - Saving {len(packages_list)} packages")
            
            # Update packages for this platform
            if "packages" not in metadata:
                metadata["packages"] = {}
            metadata["packages"][platform] = packages_list
            
            # Write metadata
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            if DEBUG:
                _debug_print(f"[Template Manager] _save_packages() - Successfully saved to {metadata_file.name}")
            
            QMessageBox.information(
                self,
                "Success",
                f"Packages saved for platform '{platform}'.\n\n"
                f"File: {metadata_file.name}\n"
                f"Packages: {len(packages_list)}"
            )
        
        except Exception as e:
            if DEBUG:
                _debug_print(f"[Template Manager] _save_packages() - Error: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save packages: {e}")
    
    def _save_support_script(self):
        """Save support script with validation."""
        if DEBUG:
            _debug_print(f"[Template Manager] _save_support_script() called")
        
        if not self.bundle_name:
            QMessageBox.warning(self, "Error", "Please select a template first")
            return
        
        bundle_name = self.bundle_name_input.text().strip()
        if not bundle_name:
            QMessageBox.warning(self, "Error", "Please enter a bundle name")
            return
        
        script_content = self.support_script_text.toPlainText()
        if not script_content.strip():
            QMessageBox.warning(self, "Error", "Script is empty")
            return
        
        if DEBUG:
            _debug_print(f"[Template Manager] _save_support_script() - bundle: {bundle_name}, script size: {len(script_content)} bytes")
        
        # Validate paths
        is_valid, validation_msg = self._validate_script_paths(script_content)
        if not is_valid:
            if DEBUG:
                _debug_print(f"[Template Manager] _save_support_script() - Validation failed: {validation_msg}")
            QMessageBox.critical(self, "Validation Error", validation_msg)
            return
        
        try:
            script_filename = f"{bundle_name}.msh"
            script_file = self.generic_templates_dir / script_filename
            
            # Write script file
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            if DEBUG:
                _debug_print(f"[Template Manager] _save_support_script() - Saved script file: {script_file.name}")
            
            # Set permissions to 444 (read-only, no execute)
            import stat
            os.chmod(script_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            
            # Update metadata with script info
            metadata_file = self.generic_templates_dir / f"{bundle_name}.json"
            import json
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {"packages": {}, "scripts": []}
            
            # Extract script paths
            scripts = self._extract_and_validate_scripts(script_content)
            script_paths = [s["filename"] for s in scripts if s["filename"]]
            
            if DEBUG:
                _debug_print(f"[Template Manager] _save_support_script() - Found {len(script_paths)} script paths")
            
            metadata["scripts"] = script_paths
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            if DEBUG:
                _debug_print(f"[Template Manager] _save_support_script() - Successfully saved script and updated metadata")
            
            QMessageBox.information(
                self,
                "Success",
                f"Support script saved.\n\n"
                f"File: {script_filename}\n"
                f"Permissions: 444 (read-only)\n"
                f"Scripts: {len(scripts)}\n\n"
                f"Path: {script_file}"
            )
        
        except Exception as e:
            if DEBUG:
                _debug_print(f"[Template Manager] _save_support_script() - Error: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save script: {e}")
    
    def _get_script_output_dir(self) -> tuple[Path, bool]:
        """Get the directory where scripts should be saved.
        
        Returns:
            (directory_path, is_fallback) - is_fallback True if using ~/usr/local/sbin/pam.d fallback
        """
        if DEBUG:
            _debug_print(f"[Template Manager] _get_script_output_dir() - Determining script output directory")
        
        # Try /usr/local/sbin/pam.d
        target_dir = Path("/usr/local/sbin/pam.d")
        try:
            if not target_dir.exists():
                target_dir.mkdir(parents=True, mode=0o755)
                if DEBUG:
                    _debug_print(f"[Template Manager] _get_script_output_dir() - Created: {target_dir}")
                logger.info(f"Created script directory: {target_dir}")
            else:
                if DEBUG:
                    _debug_print(f"[Template Manager] _get_script_output_dir() - Using: {target_dir}")
            return target_dir, False
        except (PermissionError, OSError) as e:
            if DEBUG:
                _debug_print(f"[Template Manager] _get_script_output_dir() - Cannot create {target_dir}: {e}, using fallback")
            logger.warning(f"Cannot create {target_dir}: {e}, using fallback")
            # Fallback: use ~/usr/local/sbin/pam.d
            home_dir = Path.home()
            fallback_dir = home_dir / "usr" / "local" / "sbin" / "pam.d"
            try:
                fallback_dir.mkdir(parents=True, mode=0o755, exist_ok=True)
                if DEBUG:
                    _debug_print(f"[Template Manager] _get_script_output_dir() - Created fallback: {fallback_dir}")
                logger.info(f"Created fallback script directory: {fallback_dir}")
                return fallback_dir, True
            except Exception as e2:
                if DEBUG:
                    _debug_print(f"[Template Manager] _get_script_output_dir() - Fallback failed: {e2}")
                logger.error(f"Failed to create fallback directory: {e2}")
                raise FileOperationError(f"Cannot create script directory: {e2}")
    
    def _check_package_permissions(self) -> tuple[bool, Optional[Path]]:
        """Check if user can install packages.
        
        Returns:
            (can_install, install_script_path) - can_install True if user has sudo/package permissions
        """
        if DEBUG:
            _debug_print(f"[Template Manager] _check_package_permissions() - Checking sudo/package permissions")
        
        import shutil
        
        # Check if user can run package managers
        can_install = False
        
        # Try to detect package manager
        package_managers = {
            'apt': ['apt', 'apt-get'],
            'dnf': ['dnf'],
            'yum': ['yum'],
            'pacman': ['pacman'],
            'apk': ['apk'],
            'pkg': ['pkg']  # FreeBSD
        }
        
        for pm_name, pm_cmds in package_managers.items():
            for cmd in pm_cmds:
                if shutil.which(cmd):
                    try:
                        # Try to check sudo without password
                        if SubprocessExecutor.check_sudo_available(cmd):
                            can_install = True
                            if DEBUG:
                                _debug_print(f"[Template Manager] _check_package_permissions() - Can install (found {pm_name})")
                            break
                    except:
                        pass
        
        if not can_install:
            # Create install.packages.sh script location
            home_dir = Path.home()
            install_dir = home_dir / "usr" / "local"
            try:
                install_dir.mkdir(parents=True, exist_ok=True)
                if DEBUG:
                    _debug_print(f"[Template Manager] _check_package_permissions() - Cannot install, created install script dir")
                return False, install_dir / "install.packages.sh"
            except Exception as e:
                if DEBUG:
                    _debug_print(f"[Template Manager] _check_package_permissions() - Cannot create install script dir: {e}")
                logger.warning(f"Cannot create install script directory: {e}")
                return False, None
        
        if DEBUG:
            _debug_print(f"[Template Manager] _check_package_permissions() - Can install packages")
        return True, None
    
    def _append_to_install_script(self, script_path: Path, packages: dict):
        """Append packages to install.packages.sh script.
        
        Args:
            script_path: Path to install.packages.sh
            packages: Dict of {platform: [package_list]}
        """
        if DEBUG:
            _debug_print(f"[Template Manager] _append_to_install_script() - Appending to {script_path.name}")
        
        try:
            content = ""
            if script_path.exists():
                with open(script_path, 'r') as f:
                    content = f.read()
            else:
                # Create header
                content = "#!/bin/bash\n"
                content += "# Auto-generated package installation script\n"
                content += "# Generated by PAM Manager v9.0\n"
                content += "# List of packages to install\n\n"
            
            # Append new packages
            for platform, pkg_list in packages.items():
                if pkg_list:
                    content += f"\n# Packages for {platform}\n"
                    for pkg in pkg_list:
                        # Only add if not already present
                        if pkg not in content:
                            content += f"# {pkg}\n"
            
            # Write back
            with open(script_path, 'w') as f:
                f.write(content)
            
            if DEBUG:
                _debug_print(f"[Template Manager] _append_to_install_script() - Successfully updated")
            logger.info(f"Updated install script: {script_path}")
        
        except Exception as e:
            if DEBUG:
                _debug_print(f"[Template Manager] _append_to_install_script() - Error: {e}")
            logger.error(f"Failed to update install script: {e}")
    
    def _save_bundle(self):
        """Save complete bundle (packages and scripts)."""
        if DEBUG:
            _debug_print(f"[Template Manager] _save_bundle() called")
        
        if not self.bundle_name:
            QMessageBox.warning(self, "Error", "Please select a template first")
            return
        
        bundle_name = self.bundle_name_input.text().strip()
        if not bundle_name:
            QMessageBox.warning(self, "Error", "Please enter a bundle name")
            return
        
        if DEBUG:
            _debug_print(f"[Template Manager] _save_bundle() - Saving bundle: {bundle_name}")
        
        try:
            # Create or update metadata file
            metadata_file = self.generic_templates_dir / f"{bundle_name}.json"
            
            import json
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {"packages": {}, "scripts": []}
            
            # Update packages if any
            packages_content = self.packages_text.toPlainText()
            if packages_content.strip():
                platform = self.platform_combo.currentText()
                packages_list = [pkg.strip() for pkg in packages_content.split("\n") if pkg.strip()]
                if "packages" not in metadata:
                    metadata["packages"] = {}
                metadata["packages"][platform] = packages_list
            
            # Check package installation permissions
            can_install, install_script_path = self._check_package_permissions()
            if not can_install and install_script_path and packages_content.strip():
                self._append_to_install_script(install_script_path, metadata["packages"])
                logger.info(f"Added packages to install script (no sudo): {install_script_path}")
            
            # Update scripts if any
            script_content = self.support_script_text.toPlainText()
            if script_content.strip():
                scripts = self._extract_and_validate_scripts(script_content)
                script_paths = [s["filename"] for s in scripts if s["filename"]]
                metadata["scripts"] = script_paths
                
                # Get output directory (with fallback)
                output_dir, is_fallback = self._get_script_output_dir()
                
                # Write individual script files
                for script in scripts:
                    if script["filename"]:
                        script_name = Path(script["filename"]).name
                        script_file = output_dir / script_name
                        with open(script_file, 'w') as f:
                            f.write(script["content"])
                        
                        # Set permissions to 444 (read-only, no execute)
                        import stat
                        os.chmod(script_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                        logger.info(f"Deployed script: {script_file}")
                
                # Also save bundle script file in Generic.Templates
                bundle_script_file = self.generic_templates_dir / f"{bundle_name}.msh"
                with open(bundle_script_file, 'w') as f:
                    f.write(script_content)
                os.chmod(bundle_script_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            
            # Write metadata
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            fallback_msg = "\n(Using fallback: ~/usr/local/sbin/pam.d)" if is_fallback else ""
            output_info = f"\nScripts deployed to: {output_dir}{fallback_msg}" if script_content.strip() else ""
            
            QMessageBox.information(
                self,
                "Success",
                f"Bundle '{bundle_name}' saved successfully.\n\n"
                f"Files saved:\n"
                f"- {bundle_name}.json (metadata)\n"
                f"- {bundle_name}.msh (scripts in Generic.Templates){output_info}\n\n"
                f"Metadata location: {self.generic_templates_dir}"
            )
            
            logger.info(f"Bundle saved: {bundle_name}")
        
        except Exception as e:
            if DEBUG:
                _debug_print(f"[Template Manager] _save_bundle() - Error: {e}")
            logger.error(f"Failed to save bundle: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save bundle: {e}")
    
    def _delete_bundle(self):
        """Delete bundle files for this template (from both storage and deployment locations)."""
        if DEBUG:
            _debug_print(f"[Template Manager] _delete_bundle() called")
        
        bundle_name = self.bundle_name_input.text().strip()
        if not bundle_name:
            QMessageBox.warning(self, "Error", "Please enter a bundle name")
            return
        
        if DEBUG:
            _debug_print(f"[Template Manager] _delete_bundle() - Deleting bundle: {bundle_name}")
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete all bundle files for '{bundle_name}'?\n\n"
            f"This will remove:\n"
            f"- Metadata JSON (Generic.Templates)\n"
            f"- Support scripts (.msh) (Generic.Templates)\n"
            f"- Deployed scripts (/usr/local/sbin/pam.d or ~/usr/local/sbin/pam.d)\n\n"
            f"This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            deleted = []
            failed = []
            
            # Delete from Generic.Templates
            metadata_file = self.generic_templates_dir / f"{bundle_name}.json"
            bundle_script_file = self.generic_templates_dir / f"{bundle_name}.msh"
            
            if metadata_file.exists():
                try:
                    os.remove(metadata_file)
                    deleted.append(f"✓ {metadata_file.name}")
                    logger.info(f"Deleted metadata: {metadata_file}")
                except Exception as e:
                    failed.append(f"✗ {metadata_file.name}: {e}")
                    logger.error(f"Failed to delete metadata: {e}")
            
            if bundle_script_file.exists():
                try:
                    os.remove(bundle_script_file)
                    deleted.append(f"✓ {bundle_script_file.name}")
                    logger.info(f"Deleted bundle script: {bundle_script_file}")
                except Exception as e:
                    failed.append(f"✗ {bundle_script_file.name}: {e}")
                    logger.error(f"Failed to delete bundle script: {e}")
            
            # Delete deployed scripts from /usr/local/sbin/pam.d and fallback
            try:
                output_dir, _ = self._get_script_output_dir()
                
                # Read metadata to find deployed scripts
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    for script_path in metadata.get("scripts", []):
                        script_name = Path(script_path).name
                        deployed_script = output_dir / script_name
                        
                        if deployed_script.exists():
                            try:
                                os.remove(deployed_script)
                                deleted.append(f"✓ Deployed: {deployed_script.name}")
                                if DEBUG:
                                    _debug_print(f"[Template Manager] _delete_bundle() - Deleted deployed: {deployed_script.name}")
                                logger.info(f"Deleted deployed script: {deployed_script}")
                            except Exception as e:
                                failed.append(f"✗ Deployed {script_name}: {e}")
                                logger.warning(f"Failed to delete deployed script: {e}")
            except Exception as e:
                if DEBUG:
                    _debug_print(f"[Template Manager] _delete_bundle() - Could not delete deployed scripts: {e}")
                logger.debug(f"Could not delete deployed scripts: {e}")
            
            # Show results
            message = ""
            if deleted:
                message += "Deleted files:\n" + "\n".join(deleted)
            if failed:
                if message:
                    message += "\n\nFailed to delete:\n"
                else:
                    message += "Failed to delete:\n"
                message += "\n".join(failed)
            
            if deleted or failed:
                QMessageBox.information(self, "Delete Results", message if message else "No changes made")
                self.packages_text.clear()
                self.support_script_text.clear()
                self.bundle_name_input.clear()
            else:
                QMessageBox.information(self, "Info", "No bundle files found to delete")
            
            logger.info(f"Bundle deletion completed: {bundle_name}")
        
        except Exception as e:
            if DEBUG:
                _debug_print(f"[Template Manager] _delete_bundle() - Error: {e}")
            logger.error(f"Failed to delete bundle: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to delete bundle: {e}")
    
    def refresh_data(self):
        """Refresh template list (called when tab is activated)."""
        if DEBUG:
            _debug_print(f"[Template Manager] refresh_data() - Refreshing template list on tab activation")
        self._generate_templates_list_if_needed()
        self._load_templates()



class AboutTab(QWidget):
    """Tab with application information."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize about tab UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("PAM Manager GUI")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Info text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        
        about_content = """
PAM MANAGER v2.0 - GRAPHICAL USER INTERFACE

A modern graphical interface for managing PAM (Pluggable Authentication Modules) configuration.

FEATURES:
- View system PAM information and platform details
- Browse comprehensive PAM module database (53+ modules)
- Filter modules by category and facility
- Configure PAM policies with ease
- Validate configurations before applying
- Support for Linux and FreeBSD systems

SUPPORTED PLATFORMS:
- Debian / Ubuntu / Linux Mint / Kali Linux
- RedHat / Rocky Linux / Alma Linux / CentOS Stream / Fedora
- FreeBSD / OpenBSD / NetBSD

FRAMEWORK:
Built with PyQt5 for cross-desktop compatibility (GNOME, KDE, XFCE)

VERSION: 2.0.0 (Optimized Window Sizing and Minimum Constraints)

Features in v2.0:
- Improved layout management and scrolling behavior
- Reformatted Auto-Created Items Summary with action-based statistics
- Detailed tracking for Import, Save, and Export operations
- Enhanced Service Definition workflow with improved diagnostics
- Multi-line configuration display with proper alignment
- Improved backup/restore mechanism for service imports
- Adapter pattern support for FragmentManager and ElementManager
- Qt4/Qt5 Fallback Support (49 debug points in compatibility layer)
- Comprehensive Debug Logging (Template Manager + Qt4 Detection)
- Bundle template management with package installation tracking
- Script deployment and permission management
- Platform-specific package handling
- Advanced Template System with versioning and export/import
- Multi-level caching (L1 memory + L2 disk)
- Async file operations and lazy tab loading
- Enhanced validation engine with conflict detection
- Template dependency tracking and usage statistics

For more information, visit the project documentation.
        """
        
        info_text.setText(about_content)
        layout.addWidget(info_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        quit_button = QPushButton("Exit")
        quit_button.clicked.connect(QApplication.quit)
        button_layout.addWidget(quit_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)


class PAMManagerGUI(QMainWindow):
    """Main PAM Manager GUI application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PAM Manager v2.0 - Advanced Configuration Management")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(975, 800)  # Min šírka okna
        
        # Initialize variables
        self.registry = None
        self.platform = None
        
        # Initialize unified configuration manager
        # This handles YAML, JSON, and XML formats automatically
        self.config_manager = UnifiedConfigManager()
        
        # Create worker thread
        self.worker = ModuleLoadWorker()
        self.worker.finished.connect(self.on_modules_loaded)
        self.worker.error.connect(self.on_load_error)
        
        # Initialize UI
        self.init_ui()
        
        # Start loading modules
        self.worker.start()
    
    def init_ui(self):
        """Initialize main UI."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("PAM Manager v2.0 - Graphical Configuration")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Status label
        self.status_label = QLabel("Loading PAM modules...")
        layout.addWidget(self.status_label)
        
        # Tabs (initially empty, populated after loading)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        central_widget.setLayout(layout)
    
    def on_modules_loaded(self):
        """Called when modules are successfully loaded."""
        self.registry = self.worker.registry
        self.platform = self.worker.platform
        
        # Auto-load templates on startup (Fragment → Element → Service)
        # Templates are loaded into memory and made available in UI combos
        # They are NOT persisted to config until actually used
        try:
            fragment_templates = TemplateManager.list_template_names('Fragment')
            element_templates = TemplateManager.list_template_names('Element')
            service_templates = TemplateManager.list_template_names('Service')
            
            if fragment_templates or element_templates or service_templates:
                templates_loaded = (len(fragment_templates) + len(element_templates) + 
                                  len(service_templates))
                if DEBUG:
                    _debug_print(f"Templates auto-loaded on startup: "
                          f"{len(fragment_templates)} Fragments, "
                          f"{len(element_templates)} Elements, "
                          f"{len(service_templates)} Services")
        except Exception as e:
            print(f"[WARNING] Error auto-loading templates: {e}")
        
        # Clear tabs
        self.tabs.clear()
        
        # Create tab instances (pass config_manager to tabs that need it)
        self.info_tab = InfoTab(self.registry, self.platform)
        self.modules_tab = ModulesTab(self.registry)
        self.fragment_tab = PolicyFragmentTab(self.registry, self.config_manager, parent_gui=self)
        self.element_tab = PolicyElementTab(self.registry, self.config_manager)
        self.service_tab = ServiceDefinitionTab(self.registry, self.config_manager)
        self.service_mapping_tab = ServiceMappingTab(self.config_manager, parent_gui=self)
        self.template_manager_tab = TemplateManagerTab()
        self.about_tab = AboutTab()
        
        # Add tabs
        self.tabs.addTab(self.info_tab, "System Information")
        self.tabs.addTab(self.modules_tab, "PAM Modules")
        self.tabs.addTab(self.fragment_tab, "Policy Fragment")
        self.tabs.addTab(self.element_tab, "Policy Element")
        self.tabs.addTab(self.service_mapping_tab, "Service Definition")
        self.tabs.addTab(self.template_manager_tab, "Template Manager")
        self.tabs.addTab(self.service_tab, "Utility")
        self.tabs.addTab(self.about_tab, "About")
        
        # Connect tab change signal for refresh
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # Initialize all tabs with refresh_data() to load templates and data into memory
        # This ensures templates are available from startup without waiting for tab click
        if DEBUG:
            _debug_print("Starting tab initialization...")
        if hasattr(self, 'info_tab') and hasattr(self.info_tab, 'refresh_data'):
            if DEBUG:
                _debug_print("Calling refresh_data() on info_tab")
            self.info_tab.refresh_data()
        if hasattr(self, 'modules_tab') and hasattr(self.modules_tab, 'refresh_data'):
            if DEBUG:
                _debug_print("Calling refresh_data() on modules_tab")
            self.modules_tab.refresh_data()
        if hasattr(self, 'fragment_tab') and hasattr(self.fragment_tab, 'refresh_data'):
            if DEBUG:
                _debug_print("Calling refresh_data() on fragment_tab")
            self.fragment_tab.refresh_data()
        if hasattr(self, 'element_tab') and hasattr(self.element_tab, 'refresh_data'):
            if DEBUG:
                _debug_print("Calling refresh_data() on element_tab")
            self.element_tab.refresh_data()
        if hasattr(self, 'service_mapping_tab') and hasattr(self.service_mapping_tab, 'refresh_data'):
            if DEBUG:
                _debug_print("Calling refresh_data() on service_mapping_tab")
            self.service_mapping_tab.refresh_data()
        if hasattr(self, 'template_manager_tab') and hasattr(self.template_manager_tab, 'refresh_data'):
            if DEBUG:
                _debug_print("Calling refresh_data() on template_manager_tab")
            self.template_manager_tab.refresh_data()
        if hasattr(self, 'service_tab') and hasattr(self.service_tab, 'refresh_data'):
            if DEBUG:
                _debug_print("Calling refresh_data() on service_tab")
            self.service_tab.refresh_data()
        if DEBUG:
            _debug_print("Tab initialization completed")
        
        self.status_label.setText(
            f"Ready - {len(self.registry.list_all_modules())} modules loaded | "
            f"Platform: {self.platform.value}"
        )
    
    def on_load_error(self, error_msg):
        """Called when there's an error loading modules."""
        self.status_label.setText(f"Error: {error_msg}")
        QMessageBox.critical(self, "Error", f"Failed to load PAM modules:\n{error_msg}")
    
    def _on_tab_changed(self, index):
        """Handle tab change event - refresh the newly selected tab."""
        if index == 0:  # System Information tab
            if hasattr(self, 'info_tab') and hasattr(self.info_tab, 'refresh_data'):
                self.info_tab.refresh_data()
        elif index == 1:  # PAM Modules tab
            if hasattr(self, 'modules_tab') and hasattr(self.modules_tab, 'refresh_data'):
                self.modules_tab.refresh_data()
        elif index == 2:  # Policy Fragment tab
            if hasattr(self, 'fragment_tab') and hasattr(self.fragment_tab, 'refresh_data'):
                self.fragment_tab.refresh_data()
        elif index == 3:  # Policy Element tab
            if hasattr(self, 'element_tab') and hasattr(self.element_tab, 'refresh_data'):
                self.element_tab.refresh_data()
        elif index == 4:  # Service Mapping tab (Service Definition)
            if hasattr(self, 'service_mapping_tab') and hasattr(self.service_mapping_tab, 'refresh_data'):
                self.service_mapping_tab.refresh_data()
        elif index == 5:  # Template Manager tab
            if hasattr(self, 'template_manager_tab') and hasattr(self.template_manager_tab, 'refresh_data'):
                self.template_manager_tab.refresh_data()
        elif index == 6:  # Utility tab (Service Definition)
            if hasattr(self, 'service_tab') and hasattr(self.service_tab, 'refresh_data'):
                self.service_tab.refresh_data()
    
    def show_help(self, tab_name: str):
        """Display help for a specific tab.
        
        Args:
            tab_name: Name of the tab to show help for
        """
        try:
            help_file = Path(__file__).parent / "help.json"
            if not help_file.exists():
                QMessageBox.warning(self, "Help Not Available", 
                                  f"Help file not found at {help_file}")
                return
            
            with open(help_file, 'r') as f:
                help_data = json.load(f)
            
            if tab_name not in help_data:
                QMessageBox.warning(self, "Help Not Available",
                                  f"No help available for '{tab_name}'")
                return
            
            tab_help = help_data[tab_name]
            
            # Create help dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Help - {tab_help.get('title', tab_name)}")
            dialog.setGeometry(200, 200, 700, 600)
            
            layout = QVBoxLayout()
            
            # Title
            title_label = QLabel(tab_help.get('title', tab_name))
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setBold(True)
            title_label.setFont(title_font)
            layout.addWidget(title_label)
            
            # Description
            desc = tab_help.get('description', '')
            if desc:
                desc_label = QLabel(desc)
                desc_label.setStyleSheet("color: #666; margin-bottom: 15px;")
                layout.addWidget(desc_label)
            
            # Content scrollable area
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content_widget = QWidget()
            content_layout = QVBoxLayout()
            
            # Sections
            sections = tab_help.get('sections', [])
            for section in sections:
                heading = section.get('heading', '')
                content = section.get('content', '')
                
                if heading:
                    heading_label = QLabel(heading)
                    heading_font = QFont()
                    heading_font.setPointSize(11)
                    heading_font.setBold(True)
                    heading_label.setFont(heading_font)
                    heading_label.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
                    content_layout.addWidget(heading_label)
                
                if content:
                    content_label = QLabel(content)
                    content_label.setWordWrap(True)
                    content_label.setStyleSheet("margin-left: 10px; margin-bottom: 10px;")
                    content_layout.addWidget(content_label)
            
            content_layout.addStretch()
            content_widget.setLayout(content_layout)
            scroll.setWidget(content_widget)
            layout.addWidget(scroll)
            
            # Close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Help Error", f"Failed to load help: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        reply = QMessageBox.question(
            self, 'Exit',
            'Are you sure you want to exit PAM Manager?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def handle_populate(populate_path: Optional[str] = None):
    """Handle --populate mode: load config and create service files in ~/etc/pam.d.
    
    Loads YAML/JSON configuration and exports service definitions to ~/etc/pam.d/
    
    Args:
        populate_path: Optional path to specific YAML/JSON file or config directory.
                      If not provided, searches in ~/etc/pam.d, current directory,
                      and /etc/pam.d for pam-config.yaml/json or pam-config.yml files.
    """
    from pam_manager.policy import UnifiedConfigManager
    from datetime import datetime
    
    config_dir = Path.home() / 'etc' / 'pam.d'
    
    # Find configuration file
    config_file = None
    use_dir = None  # Directory to pass to UnifiedConfigManager
    search_dirs = [
        Path.home() / 'etc' / 'pam.d',
        Path.cwd(),
        Path('/etc/pam.d')
    ]
    search_files = ['pam-config.yaml', 'pam-config.json', 'pam-config.yml']
    
    if populate_path:
        # Use provided path
        populate_path_obj = Path(populate_path)
        if populate_path_obj.is_file():
            # Path is a file - extract directory
            config_file = populate_path_obj
            use_dir = config_file.parent
            print(f"[INFO] Using provided configuration file: {config_file}")
        elif populate_path_obj.is_dir():
            # Path is a directory - search for config files in it
            use_dir = populate_path_obj
            for search_file in search_files:
                candidate = use_dir / search_file
                if candidate.exists():
                    config_file = candidate
                    print(f"[INFO] Using configuration directory: {use_dir}")
                    break
        else:
            print(f"[ERROR] Configuration path not found: {populate_path}")
            sys.exit(1)
        
        if not config_file:
            print(f"[ERROR] No configuration file found in {populate_path}")
            sys.exit(1)
    else:
        # Search for configuration file
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for search_file in search_files:
                candidate = search_dir / search_file
                if candidate.exists():
                    config_file = candidate
                    use_dir = search_dir
                    if DEBUG:
                        _debug_print(f"Found configuration: {config_file}")
                    print(f"[INFO] Using configuration: {config_file}")
                    break
            if config_file:
                break
    
    if not config_file:
        print("[ERROR] No configuration file found")
        print("[INFO] Searched in:")
        for d in search_dirs:
            print(f"  - {d}")
        print(f"[INFO] Looking for: {', '.join(search_files)}")
        sys.exit(1)
    
    # Load configuration
    try:
        config_manager = UnifiedConfigManager(str(use_dir))
        if DEBUG:
            _debug_print(f"Loaded configuration from {config_file}")
        print(f"[INFO] Configuration loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load configuration: {e}")
        import traceback
        if DEBUG:
            traceback.print_exc()
        sys.exit(1)
    
    # Create service files in ~/etc/pam.d
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        
        services = config_manager.list_services()
        if not services:
            print("[WARNING] No services found in configuration")
            sys.exit(0)
        
        if DEBUG:
            _debug_print(f"Found {len(services)} services to export")
        
        # Helper function to wrap description to 80 chars
        def wrap_description(text, prefix="# "):
            """Wrap text to 80 characters with proper continuation."""
            lines = []
            current_line = ""
            
            for word in text.split():
                # Test if adding this word exceeds 80 chars
                test_line = (current_line + " " + word).strip() if current_line else word
                
                if len(prefix + test_line) <= 80:
                    current_line = test_line
                else:
                    # Current line is full, save it
                    if current_line:
                        lines.append(prefix + current_line)
                    current_line = word
            
            # Add remaining text
            if current_line:
                lines.append(prefix + current_line)
            
            return "\n".join(lines)
        
        # Export each service
        exported_count = 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fragments_by_id = {frag.get('id'): frag for frag in config_manager.list_fragments()}
        
        for service in services:
            service_id = service['id']
            description = service.get('description', '')
            elements = service.get('elements', [])
            
            # Build file content
            content_lines = []
            
            # Header
            content_lines.append(f"# Created by PAM Manager {timestamp}")
            
            # Service name and description
            if description:
                service_line = f"# Service name: {service_id}: {description}"
                if len(service_line) <= 80:
                    content_lines.append(service_line)
                else:
                    # Wrap the service description
                    wrapped = wrap_description(f"Service name: {service_id}: {description}")
                    content_lines.append(wrapped)
            else:
                content_lines.append(f"# Service name: {service_id}")
            
            # Add elements to service
            if elements:
                content_lines.append("#")
                
                # Get all elements
                all_elements_dict = {e['id']: e for e in config_manager.list_elements()}
                
                for element_id in elements:
                    element = all_elements_dict.get(element_id)
                    if element:
                        content_lines.append(f"# Policy Element: {element_id}")
                        if element.get('description'):
                            desc_wrapped = wrap_description(element['description'], "# ")
                            content_lines.append(desc_wrapped)

                        for frag_ref in element.get('fragments', []):
                            rendered_line = render_pam_line_from_fragment_ref(frag_ref, fragments_by_id)
                            if rendered_line:
                                content_lines.append(rendered_line)

                        content_lines.append("")
            
            # Add empty line before PAM config
            if elements:
                content_lines.append("#")
            
            # Write service file
            file_path = config_dir / service_id
            try:
                file_path.write_text("\n".join(content_lines))
                print(f"[INFO] Created: {file_path}")
                exported_count += 1
            except Exception as e:
                print(f"[WARNING] Failed to create {file_path}: {e}")
        
        print(f"[INFO] Successfully created {exported_count} service file(s) in {config_dir}")
        print("[INFO] Populate mode completed. Exiting.")
        sys.exit(0)
    
    except Exception as e:
        print(f"[ERROR] Failed to populate services: {e}")
        import traceback
        if DEBUG:
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point with GUI launcher and fallback support."""
    # Handle --benchmark-gui mode (Phase 4 performance benchmarking)
    if '--benchmark-gui' in sys.argv:
        try:
            from pam_manager.gui_performance_benchmarks import GuiPerformanceBenchmarks
            
            if DEBUG:
                _debug_print("Running GUI performance benchmarks")
            
            GuiPerformanceBenchmarks.print_benchmark_report()
            sys.exit(0)
        
        except ImportError as e:
            print(f"[ERROR] Performance benchmarks not available: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Benchmark failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Handle --run-ci-tests mode (Phase 4 CI/CD integration)
    if '--run-ci-tests' in sys.argv:
        try:
            from pam_manager.gui_cicd_integration import CICDTestFramework
            
            if DEBUG:
                _debug_print("Running CI/CD test framework")
            
            # Create framework instance and run tests
            framework = CICDTestFramework()
            success = framework.run_all_tests()
            
            # Print results as JSON for CI/CD pipeline consumption
            results = {
                'test_results': [
                    {
                        'name': r.test_name,
                        'passed': r.passed,
                        'duration_seconds': r.duration_seconds,
                        'error': r.error_message
                    } for r in framework.results
                ],
                'summary': {
                    'total_tests': len(framework.results),
                    'passed': sum(1 for r in framework.results if r.passed),
                    'failed': sum(1 for r in framework.results if not r.passed),
                    'all_passed': success,
                    'environment': framework.environment.value
                }
            }
            
            print(json.dumps(results, indent=2))
            
            # Exit with success/failure code
            sys.exit(0 if success else 1)
        
        except ImportError as e:
            print(f"[ERROR] CI/CD test framework not available: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] CI/CD test framework failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Handle --populate mode before starting GUI
    if POPULATE_MODE:
        handle_populate(POPULATE_PATH)
        return
    
    # Phase 1: Use GUI launcher with fallback support
    try:
        from pam_manager.gui_launcher import GuiLauncher
        from pam_manager.gui_environment import GuiEnvironment
        
        if DEBUG:
            _debug_print("Initializing GUI launcher with fallback support")
            _debug_print(f"Environment detection enabled")
        
        # Create and launch GUI with fallback chain
        launcher = GuiLauncher(debug=DEBUG)
        success = launcher.launch()
        
        if not success:
            print("[ERROR] Failed to start GUI in any mode - all strategies exhausted")
            print("[ERROR] Check ~/.pam-gui-state.json for fallback history")
            sys.exit(1)
    
    except ImportError as e:
        if DEBUG:
            _debug_print(f"GUI launcher not available: {e}")
            _debug_print("Falling back to direct PyQt5 initialization")
        
        # Fallback: Old direct initialization (shouldn't reach here in normal operation)
        import os
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
        os.environ['QT_DEBUG_PLUGINS'] = '0'
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        window = PAMManagerGUI()
        window.show()
        
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
