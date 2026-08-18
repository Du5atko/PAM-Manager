"""Configuration API - strongly typed access to configuration objects."""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import yaml
import json

from pam_manager.config.models import (
    CustomPAMConfig, Service, PolicyFragment, Dependency, Renderer,
    ValidationReport, ValidationError, Platform, PAMInterface
)
from pam_manager.config.validator import ConfigurationValidator
from pam_manager.config.migration import MigrationEngine


class RepositoryAPI:
    """Main API for accessing configuration repository."""
    
    def __init__(self, config: CustomPAMConfig):
        """Initialize repository API.
        
        Args:
            config: Validated configuration object
        """
        self.config = config
        self.validator = ConfigurationValidator()
        self.migration_engine = MigrationEngine()
        
        # Build indexes for fast access
        self._build_indexes()
    
    def _build_indexes(self) -> None:
        """Build internal indexes for fast lookup."""
        self.fragments_by_id = {f.id: f for f in self.config.policy_fragments}
        self.services_by_name = {s.name: s for s in self.config.services}
        self.renderers_by_name = {r.name: r for r in self.config.renderers}
        self.deps_by_package = {d.package: d for d in self.config.dependencies}
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> Tuple['RepositoryAPI', ValidationReport]:
        """Load configuration from YAML file.
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            (RepositoryAPI instance, ValidationReport)
        """
        report = ValidationReport(
            schema_version="1.0",
            valid=True
        )
        
        try:
            with open(yaml_path, 'r') as f:
                raw_data = yaml.safe_load(f)
        except Exception as e:
            report.add_error(ValidationError(
                error_type=ValidationErrorType.SCHEMA,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to load YAML: {str(e)}",
                location=yaml_path
            ))
            return None, report
        
        # Validate against schema
        validator = ConfigurationValidator()
        schema_report = validator.validate_schema(raw_data, 'custom-pam')
        report.errors.extend(schema_report.errors)
        
        if not schema_report.valid:
            return None, report
        
        # Parse into Pydantic model
        try:
            config = CustomPAMConfig(**raw_data)
        except Exception as e:
            report.add_error(ValidationError(
                error_type=ValidationErrorType.SCHEMA,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to parse configuration: {str(e)}",
                location=yaml_path
            ))
            return None, report
        
        # Run full validation
        full_report = validator.validate_all(config, raw_data)
        report.errors.extend(full_report.errors)
        report.warnings.extend(full_report.warnings)
        report.valid = full_report.valid
        
        # Create API instance
        return cls(config), report
    
    @classmethod
    def from_json(cls, json_path: str) -> Tuple['RepositoryAPI', ValidationReport]:
        """Load configuration from JSON file.
        
        Args:
            json_path: Path to JSON configuration file
            
        Returns:
            (RepositoryAPI instance, ValidationReport)
        """
        report = ValidationReport(
            schema_version="1.0",
            valid=True
        )
        
        try:
            with open(json_path, 'r') as f:
                raw_data = json.load(f)
        except Exception as e:
            report.add_error(ValidationError(
                error_type=ValidationErrorType.SCHEMA,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to load JSON: {str(e)}",
                location=json_path
            ))
            return None, report
        
        # Validate and parse (same as YAML)
        validator = ConfigurationValidator()
        schema_report = validator.validate_schema(raw_data, 'custom-pam')
        report.errors.extend(schema_report.errors)
        
        try:
            config = CustomPAMConfig(**raw_data)
        except Exception as e:
            report.add_error(ValidationError(
                error_type=ValidationErrorType.SCHEMA,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to parse configuration: {str(e)}",
                location=json_path
            ))
            return None, report
        
        full_report = validator.validate_all(config, raw_data)
        report.errors.extend(full_report.errors)
        report.warnings.extend(full_report.warnings)
        report.valid = full_report.valid
        
        return cls(config), report
    
    def get_fragment(self, fragment_id: str) -> Optional[PolicyFragment]:
        """Get policy fragment by ID.
        
        Args:
            fragment_id: Fragment identifier
            
        Returns:
            PolicyFragment or None if not found
        """
        return self.fragments_by_id.get(fragment_id)
    
    def get_service(self, service_name: str) -> Optional[Service]:
        """Get service by name.
        
        Args:
            service_name: Service name
            
        Returns:
            Service or None if not found
        """
        return self.services_by_name.get(service_name)
    
    def get_renderer(self, renderer_name: str) -> Optional[Renderer]:
        """Get renderer by name.
        
        Args:
            renderer_name: Renderer name
            
        Returns:
            Renderer or None if not found
        """
        return self.renderers_by_name.get(renderer_name)
    
    def get_dependency(self, package: str) -> Optional[Dependency]:
        """Get dependency by package name.
        
        Args:
            package: Package name
            
        Returns:
            Dependency or None if not found
        """
        return self.deps_by_package.get(package)
    
    def list_fragments(self, 
                       interface: Optional[PAMInterface] = None,
                       platform: Optional[Platform] = None) -> List[PolicyFragment]:
        """List policy fragments with optional filtering.
        
        Args:
            interface: Filter by PAM interface (optional)
            platform: Filter by platform (optional)
            
        Returns:
            List of matching fragments
        """
        result = self.config.policy_fragments
        
        if interface:
            result = [f for f in result if f.category == interface]
        
        if platform:
            result = [f for f in result if platform in f.platforms]
        
        return result
    
    def list_services(self, platform: Optional[Platform] = None) -> List[Service]:
        """List services with optional platform filtering.
        
        Args:
            platform: Filter by platform (optional)
            
        Returns:
            List of matching services
        """
        if not platform:
            return self.config.services
        
        return [s for s in self.config.services if platform in s.platforms]
    
    def validate(self) -> ValidationReport:
        """Validate entire configuration.
        
        Returns:
            ValidationReport with results
        """
        return self.validator.validate_all(self.config)
    
    def get_fragment_dependencies(self, fragment_id: str) -> List[PolicyFragment]:
        """Get all fragments that a fragment depends on.
        
        Args:
            fragment_id: Fragment ID
            
        Returns:
            List of dependent fragments
        """
        fragment = self.get_fragment(fragment_id)
        if not fragment:
            return []
        
        result = []
        for dep_id in fragment.dependencies:
            dep_fragment = self.get_fragment(dep_id)
            if dep_fragment:
                result.append(dep_fragment)
        
        return result
    
    def get_fragment_dependents(self, fragment_id: str) -> List[PolicyFragment]:
        """Get all fragments that depend on a fragment.
        
        Args:
            fragment_id: Fragment ID
            
        Returns:
            List of fragments that depend on this one
        """
        result = []
        for fragment in self.config.policy_fragments:
            if fragment_id in fragment.dependencies:
                result.append(fragment)
        
        return result
    
    def export_yaml(self, output_path: str) -> bool:
        """Export configuration to YAML file.
        
        Args:
            output_path: Path to write YAML file
            
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w') as f:
                yaml.dump(self.config.dict(), f, default_flow_style=False)
            return True
        except Exception:
            return False
    
    def export_json(self, output_path: str) -> bool:
        """Export configuration to JSON file.
        
        Args:
            output_path: Path to write JSON file
            
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(self.config.dict(), f, indent=2)
            return True
        except Exception:
            return False
    
    def get_schema_version(self) -> str:
        """Get schema version of this configuration."""
        return self.config.schema_version
    
    def get_metadata(self) -> Dict:
        """Get repository metadata.
        
        Returns:
            Metadata dictionary
        """
        return self.config.metadata.dict()
    
    def statistics(self) -> Dict:
        """Get configuration statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'schema_version': self.config.schema_version,
            'total_services': len(self.config.services),
            'total_fragments': len(self.config.policy_fragments),
            'total_dependencies': len(self.config.dependencies),
            'total_renderers': len(self.config.renderers),
            'fragments_by_interface': {
                'auth': len([f for f in self.config.policy_fragments if f.category.value == 'auth']),
                'account': len([f for f in self.config.policy_fragments if f.category.value == 'account']),
                'password': len([f for f in self.config.policy_fragments if f.category.value == 'password']),
                'session': len([f for f in self.config.policy_fragments if f.category.value == 'session']),
            }
        }


# Import ValidationErrorType and ErrorSeverity
from pam_manager.config.models import ValidationErrorType, ErrorSeverity
