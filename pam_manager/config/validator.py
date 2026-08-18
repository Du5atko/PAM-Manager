"""Configuration validation engine."""

from typing import Dict, List, Set, Tuple
from datetime import datetime
import json
from pathlib import Path

try:
    import jsonschema
    from jsonschema import validate, ValidationError as JSONSchemaError
except ImportError:
    jsonschema = None

from pam_manager.config.models import (
    ValidationReport, ValidationError, ValidationErrorType, ErrorSeverity,
    CustomPAMConfig, DependencyGraph, PolicyFragment, Service
)
from pam_manager.config.schemas import (
    SCHEMA_CUSTOM_PAM, SCHEMA_POLICY_FRAGMENTS, SCHEMA_SERVICES,
    SCHEMA_DEPENDENCY_GRAPH, SCHEMA_METADATA, SCHEMA_VALIDATION
)


class ConfigurationValidator:
    """Validates configuration against schemas and semantics."""
    
    def __init__(self):
        """Initialize validator."""
        self.schemas = {
            'custom-pam': SCHEMA_CUSTOM_PAM,
            'policy-fragments': SCHEMA_POLICY_FRAGMENTS,
            'services': SCHEMA_SERVICES,
            'dependency-graph': SCHEMA_DEPENDENCY_GRAPH,
            'metadata': SCHEMA_METADATA,
            'validation': SCHEMA_VALIDATION,
        }
    
    def validate_schema(self, data: Dict, schema_name: str) -> ValidationReport:
        """Validate data against JSON schema.
        
        Args:
            data: Data to validate
            schema_name: Schema name to validate against
            
        Returns:
            ValidationReport with results
        """
        report = ValidationReport(
            schema_version="1.0",
            valid=True
        )
        
        if schema_name not in self.schemas:
            report.add_error(ValidationError(
                error_type=ValidationErrorType.SCHEMA,
                severity=ErrorSeverity.ERROR,
                message=f"Unknown schema: {schema_name}",
                location=f"schema:{schema_name}"
            ))
            return report
        
        schema = self.schemas[schema_name]
        
        if not jsonschema:
            report.add_warning("jsonschema not installed - skipping JSON schema validation")
            return report
        
        try:
            validate(instance=data, schema=schema)
        except JSONSchemaError as e:
            report.add_error(ValidationError(
                error_type=ValidationErrorType.SCHEMA,
                severity=ErrorSeverity.ERROR,
                message=f"Schema validation failed: {e.message}",
                location=f"{e.path}",
                context={
                    "validator": e.validator,
                    "validator_value": str(e.validator_value),
                    "path": list(e.path)
                }
            ))
        
        return report
    
    def validate_references(self, config: CustomPAMConfig) -> ValidationReport:
        """Validate all cross-references in configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationReport with reference errors
        """
        report = ValidationReport(
            schema_version="1.0",
            valid=True
        )
        
        # Build fragment ID set
        fragment_ids = {f.id for f in config.policy_fragments}
        
        # Validate fragment references in services
        for service in config.services:
            for fragment_ref in service.fragments:
                if fragment_ref.ref not in fragment_ids:
                    report.add_error(ValidationError(
                        error_type=ValidationErrorType.REFERENCE,
                        severity=ErrorSeverity.ERROR,
                        message=f"Service '{service.name}' references missing fragment '{fragment_ref.ref}'",
                        location=f"service:{service.name}",
                        context={"missing_fragment": fragment_ref.ref}
                    ))
        
        # Validate fragment dependencies
        for fragment in config.policy_fragments:
            for dep_id in fragment.dependencies:
                if dep_id not in fragment_ids:
                    report.add_error(ValidationError(
                        error_type=ValidationErrorType.REFERENCE,
                        severity=ErrorSeverity.ERROR,
                        message=f"Fragment '{fragment.id}' depends on missing fragment '{dep_id}'",
                        location=f"fragment:{fragment.id}",
                        context={"missing_dependency": dep_id}
                    ))
        
        # Validate fragment conflicts
        for fragment in config.policy_fragments:
            for conflict_id in fragment.conflicts:
                if conflict_id not in fragment_ids:
                    report.add_warning(
                        f"Fragment '{fragment.id}' references unknown conflicting fragment '{conflict_id}'"
                    )
        
        return report
    
    def validate_semantics(self, config: CustomPAMConfig) -> ValidationReport:
        """Validate configuration semantics.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationReport with semantic errors
        """
        report = ValidationReport(
            schema_version="1.0",
            valid=True
        )
        
        # Check for duplicate fragment IDs
        fragment_ids = [f.id for f in config.policy_fragments]
        duplicates = [fid for fid in set(fragment_ids) if fragment_ids.count(fid) > 1]
        
        if duplicates:
            report.add_error(ValidationError(
                error_type=ValidationErrorType.SEMANTIC,
                severity=ErrorSeverity.ERROR,
                message=f"Duplicate fragment IDs found: {', '.join(duplicates)}",
                location="policy_fragments"
            ))
        
        # Check for duplicate service names
        service_names = [s.name for s in config.services]
        dup_services = [sn for sn in set(service_names) if service_names.count(sn) > 1]
        
        if dup_services:
            report.add_error(ValidationError(
                error_type=ValidationErrorType.SEMANTIC,
                severity=ErrorSeverity.ERROR,
                message=f"Duplicate service names: {', '.join(dup_services)}",
                location="services"
            ))
        
        # Check for circular dependencies
        self._check_circular_dependencies(config, report)
        
        # Check for conflicting fragments in same service
        self._check_service_conflicts(config, report)
        
        # Check for unsupported PAM interfaces
        self._check_unsupported_interfaces(config, report)
        
        # Check for unused fragments
        self._check_unused_fragments(config, report)
        
        return report
    
    def _check_circular_dependencies(self, config: CustomPAMConfig, 
                                     report: ValidationReport) -> None:
        """Check for circular dependencies in fragments."""
        visited = set()
        rec_stack = set()
        
        def has_cycle(fid: str, fragments_dict: Dict) -> bool:
            visited.add(fid)
            rec_stack.add(fid)
            
            fragment = fragments_dict[fid]
            for dep_id in fragment.dependencies:
                if dep_id not in fragments_dict:
                    continue
                
                if dep_id not in visited:
                    if has_cycle(dep_id, fragments_dict):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.remove(fid)
            return False
        
        fragments_dict = {f.id: f for f in config.policy_fragments}
        
        for fragment in config.policy_fragments:
            if fragment.id not in visited:
                if has_cycle(fragment.id, fragments_dict):
                    report.add_error(ValidationError(
                        error_type=ValidationErrorType.SEMANTIC,
                        severity=ErrorSeverity.ERROR,
                        message=f"Circular dependency detected involving fragment '{fragment.id}'",
                        location=f"fragment:{fragment.id}"
                    ))
    
    def _check_service_conflicts(self, config: CustomPAMConfig, 
                                  report: ValidationReport) -> None:
        """Check for conflicting fragments in same service."""
        fragments_dict = {f.id: f for f in config.policy_fragments}
        
        for service in config.services:
            fragment_refs = [f.ref for f in service.fragments]
            
            # Check if any fragments conflict
            for i, ref1 in enumerate(fragment_refs):
                if ref1 not in fragments_dict:
                    continue
                    
                frag1 = fragments_dict[ref1]
                for ref2 in fragment_refs[i+1:]:
                    if ref2 not in fragments_dict:
                        continue
                    
                    if ref2 in frag1.conflicts or ref1 in fragments_dict[ref2].conflicts:
                        report.add_error(ValidationError(
                            error_type=ValidationErrorType.SEMANTIC,
                            severity=ErrorSeverity.ERROR,
                            message=f"Service '{service.name}' has conflicting fragments: '{ref1}' and '{ref2}'",
                            location=f"service:{service.name}",
                            context={"conflict": [ref1, ref2]}
                        ))
    
    def _check_unsupported_interfaces(self, config: CustomPAMConfig, 
                                       report: ValidationReport) -> None:
        """Check for unsupported PAM interfaces."""
        valid_interfaces = {'auth', 'account', 'password', 'session'}
        
        for fragment in config.policy_fragments:
            if fragment.category.value not in valid_interfaces:
                report.add_error(ValidationError(
                    error_type=ValidationErrorType.SEMANTIC,
                    severity=ErrorSeverity.ERROR,
                    message=f"Unsupported PAM interface in fragment '{fragment.id}': {fragment.category}",
                    location=f"fragment:{fragment.id}"
                ))
    
    def _check_unused_fragments(self, config: CustomPAMConfig, 
                                 report: ValidationReport) -> None:
        """Check for unused policy fragments."""
        used_fragment_ids = set()
        
        for service in config.services:
            for frag_ref in service.fragments:
                used_fragment_ids.add(frag_ref.ref)
        
        for fragment in config.policy_fragments:
            if fragment.id not in used_fragment_ids:
                report.add_warning(
                    f"Fragment '{fragment.id}' is not used by any service"
                )
    
    def validate_all(self, config: CustomPAMConfig, 
                    schema_data: Dict = None) -> ValidationReport:
        """Run all validations.
        
        Args:
            config: Configuration to validate
            schema_data: Raw schema data to validate against JSON schema
            
        Returns:
            Combined ValidationReport
        """
        report = ValidationReport(
            schema_version="1.0",
            valid=True
        )
        
        # Schema validation
        if schema_data:
            schema_report = self.validate_schema(schema_data, 'custom-pam')
            report.errors.extend(schema_report.errors)
            report.warnings.extend(schema_report.warnings)
            if not schema_report.valid:
                report.valid = False
        
        # Reference validation
        ref_report = self.validate_references(config)
        report.errors.extend(ref_report.errors)
        report.warnings.extend(ref_report.warnings)
        if not ref_report.valid:
            report.valid = False
        
        # Semantic validation
        sem_report = self.validate_semantics(config)
        report.errors.extend(sem_report.errors)
        report.warnings.extend(sem_report.warnings)
        if not sem_report.valid:
            report.valid = False
        
        # Update statistics
        report.statistics = {
            'services': len(config.services),
            'fragments': len(config.policy_fragments),
            'dependencies': len(config.dependencies),
            'errors': len([e for e in report.errors if e.severity == ErrorSeverity.ERROR]),
            'warnings': len(report.warnings)
        }
        
        return report
