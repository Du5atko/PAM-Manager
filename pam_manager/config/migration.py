"""Configuration migration engine for schema version upgrades."""

from typing import Dict, List, Any, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

from pam_manager.config.models import CustomPAMConfig, ValidationReport, ValidationError
from pam_manager.config.models import ValidationErrorType, ErrorSeverity


class Migration(ABC):
    """Base class for schema migrations."""
    
    from_version: str
    to_version: str
    
    @abstractmethod
    def migrate(self, data: Dict) -> Dict:
        """Migrate data from old schema to new schema.
        
        Args:
            data: Data in old schema format
            
        Returns:
            Data in new schema format
        """
        pass
    
    @abstractmethod
    def validate(self, data: Dict) -> Tuple[bool, List[str]]:
        """Validate data can be migrated.
        
        Args:
            data: Data to validate
            
        Returns:
            (is_valid, errors)
        """
        pass


class Migration1_0To1_1(Migration):
    """Migration from schema 1.0 to 1.1.
    
    Changes:
    - Added 'category' field to policy fragments
    - Added 'security_level' field to policy fragments
    - Renamed 'module_arguments' to 'parameters'
    """
    
    from_version = "1.0"
    to_version = "1.1"
    
    def validate(self, data: Dict) -> Tuple[bool, List[str]]:
        """Validate 1.0 format."""
        errors = []
        
        if 'policy_fragments' not in data:
            errors.append("Missing 'policy_fragments' section")
        else:
            for i, frag in enumerate(data['policy_fragments']):
                if 'id' not in frag:
                    errors.append(f"Fragment {i} missing 'id'")
                if 'control' not in frag:
                    errors.append(f"Fragment {i} missing 'control'")
                if 'module' not in frag:
                    errors.append(f"Fragment {i} missing 'module'")
        
        return len(errors) == 0, errors
    
    def migrate(self, data: Dict) -> Dict:
        """Migrate 1.0 to 1.1."""
        data = dict(data)  # Copy
        
        # Update schema version
        data['schema_version'] = self.to_version
        
        # Migrate policy_fragments
        if 'policy_fragments' in data:
            for fragment in data['policy_fragments']:
                # Add category if missing
                if 'category' not in fragment:
                    fragment['category'] = 'authentication'
                
                # Add security_level if missing
                if 'security_level' not in fragment:
                    fragment['security_level'] = 'medium'
                
                # Rename module_arguments to parameters
                if 'module_arguments' in fragment:
                    fragment['parameters'] = fragment.pop('module_arguments')
                elif 'parameters' not in fragment:
                    fragment['parameters'] = {}
        
        return data


class Migration1_1To2_0(Migration):
    """Migration from schema 1.1 to 2.0.
    
    Changes:
    - Restructured dependency system (now uses DependencyGraph)
    - Added renderer configuration section
    - Added validation report section
    """
    
    from_version = "1.1"
    to_version = "2.0"
    
    def validate(self, data: Dict) -> Tuple[bool, List[str]]:
        """Validate 1.1 format."""
        return True, []
    
    def migrate(self, data: Dict) -> Dict:
        """Migrate 1.1 to 2.0."""
        data = dict(data)
        
        # Update schema version
        data['schema_version'] = self.to_version
        
        # Add renderers section if missing
        if 'renderers' not in data:
            data['renderers'] = [
                {
                    "name": "default-pam.d",
                    "type": "pam.d",
                    "target_path": "/etc/pam.d/",
                    "format": "standard",
                    "backup": True
                }
            ]
        
        # Dependencies restructuring handled separately
        
        return data


class MigrationEngine:
    """Engine for managing configuration schema migrations."""
    
    def __init__(self):
        """Initialize migration engine."""
        self.migrations: Dict[Tuple[str, str], Migration] = {}
        self._register_migrations()
    
    def _register_migrations(self) -> None:
        """Register available migrations."""
        migrations = [
            Migration1_0To1_1(),
            Migration1_1To2_0(),
        ]
        
        for migration in migrations:
            key = (migration.from_version, migration.to_version)
            self.migrations[key] = migration
    
    def get_migration_path(self, from_version: str, 
                          to_version: str) -> List[Migration]:
        """Find migration path from one version to another.
        
        Args:
            from_version: Starting schema version
            to_version: Target schema version
            
        Returns:
            List of migrations to apply (ordered)
        """
        if from_version == to_version:
            return []
        
        # BFS to find shortest path
        from collections import deque
        
        queue = deque([(from_version, [])])
        visited = {from_version}
        
        while queue:
            current_version, path = queue.popleft()
            
            if current_version == to_version:
                return path
            
            # Find migrations from current version
            for (src, dst), migration in self.migrations.items():
                if src == current_version and dst not in visited:
                    visited.add(dst)
                    queue.append((dst, path + [migration]))
        
        return []  # No path found
    
    def migrate(self, data: Dict, target_version: str) -> Tuple[Dict, ValidationReport]:
        """Migrate configuration to target schema version.
        
        Args:
            data: Configuration data
            target_version: Target schema version
            
        Returns:
            (migrated_data, report)
        """
        report = ValidationReport(
            schema_version="1.0",
            valid=True
        )
        
        current_version = data.get('schema_version', '1.0')
        
        if current_version == target_version:
            report.add_warning(f"Already at version {target_version}")
            return data, report
        
        # Get migration path
        migrations = self.get_migration_path(current_version, target_version)
        
        if not migrations:
            report.add_error(ValidationError(
                error_type=ValidationErrorType.SEMANTIC,
                severity=ErrorSeverity.ERROR,
                message=f"No migration path from {current_version} to {target_version}",
                location=f"migration:{current_version}->{target_version}"
            ))
            return data, report
        
        # Apply migrations
        result = data
        
        for migration in migrations:
            # Validate before migration
            is_valid, errors = migration.validate(result)
            
            if not is_valid:
                for error in errors:
                    report.add_error(ValidationError(
                        error_type=ValidationErrorType.SEMANTIC,
                        severity=ErrorSeverity.ERROR,
                        message=f"Migration validation failed: {error}",
                        location=f"migration:{migration.from_version}->{migration.to_version}"
                    ))
                return result, report
            
            # Perform migration
            try:
                result = migration.migrate(result)
                report.add_warning(
                    f"Migrated from {migration.from_version} to {migration.to_version}"
                )
            except Exception as e:
                report.add_error(ValidationError(
                    error_type=ValidationErrorType.SEMANTIC,
                    severity=ErrorSeverity.ERROR,
                    message=f"Migration failed: {str(e)}",
                    location=f"migration:{migration.from_version}->{migration.to_version}",
                    context={"exception": str(e)}
                ))
                return result, report
        
        return result, report
    
    def get_supported_versions(self) -> List[str]:
        """Get all supported schema versions."""
        versions = set()
        
        for (src, dst) in self.migrations.keys():
            versions.add(src)
            versions.add(dst)
        
        return sorted(list(versions))
    
    def can_migrate(self, from_version: str, to_version: str) -> bool:
        """Check if migration is possible."""
        path = self.get_migration_path(from_version, to_version)
        return len(path) > 0 or from_version == to_version
