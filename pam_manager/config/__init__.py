"""Configuration management system for PAM Manager."""

from pam_manager.config.models import (
    Metadata, PolicyFragment, Service, ServiceFragment, Dependency, Renderer,
    DependencyGraph, ValidationReport, CustomPAMConfig,
    PAMInterface, ControlFlag, Platform, SecurityLevel,
    RendererType, ValidationErrorType, ErrorSeverity,
)
from pam_manager.config.validator import ConfigurationValidator
from pam_manager.config.migration import MigrationEngine
from pam_manager.config.api import RepositoryAPI
from pam_manager.config.schemas import (
    SCHEMA_CUSTOM_PAM, SCHEMA_POLICY_FRAGMENTS, SCHEMA_SERVICES,
    SCHEMA_DEPENDENCY_GRAPH, SCHEMA_METADATA, SCHEMA_VALIDATION,
)

__all__ = [
    # Models
    'Metadata',
    'PolicyFragment',
    'Service',
    'ServiceFragment',
    'Dependency',
    'Renderer',
    'DependencyGraph',
    'ValidationReport',
    'CustomPAMConfig',
    
    # Enums
    'PAMInterface',
    'ControlFlag',
    'Platform',
    'SecurityLevel',
    'RendererType',
    'ValidationErrorType',
    'ErrorSeverity',
    
    # Validators and engines
    'ConfigurationValidator',
    'MigrationEngine',
    'RepositoryAPI',
    
    # Schemas
    'SCHEMA_CUSTOM_PAM',
    'SCHEMA_POLICY_FRAGMENTS',
    'SCHEMA_SERVICES',
    'SCHEMA_DEPENDENCY_GRAPH',
    'SCHEMA_METADATA',
    'SCHEMA_VALIDATION',
]
