"""Pydantic models for configuration validation."""

from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import json


class SchemaVersion(str):
    """Schema version string (semantic versioning)."""
    
    def __init__(self, version: str):
        if not isinstance(version, str) or not self._is_valid(version):
            raise ValueError(f"Invalid schema version: {version}")
        super().__init__()
    
    @staticmethod
    def _is_valid(version: str) -> bool:
        """Validate semantic versioning."""
        parts = version.split('.')
        return len(parts) == 2 and all(p.isdigit() for p in parts)


class PAMInterface(str, Enum):
    """PAM interface types."""
    AUTH = "auth"
    ACCOUNT = "account"
    PASSWORD = "password"
    SESSION = "session"


class ControlFlag(str, Enum):
    """PAM control flags."""
    REQUIRED = "required"
    REQUISITE = "requisite"
    SUFFICIENT = "sufficient"
    OPTIONAL = "optional"


class Platform(str, Enum):
    """Supported operating systems."""
    DEBIAN = "DEBIAN"
    UBUNTU = "UBUNTU"
    LINUX_MINT = "LINUX_MINT"
    KALI_LINUX = "KALI_LINUX"
    REDHAT = "REDHAT"
    ROCKY_LINUX = "ROCKY_LINUX"
    ALMA_LINUX = "ALMA_LINUX"
    CENTOS_STREAM = "CENTOS_STREAM"
    FEDORA = "FEDORA"
    FREEBSD = "FREEBSD"


class SecurityLevel(str, Enum):
    """Security levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


class RendererType(str, Enum):
    """Renderer output types."""
    PAM_D = "pam.d"
    PAM_CONF = "pam.conf"
    OTHER = "other"


class ValidationErrorType(str, Enum):
    """Validation error types."""
    SCHEMA = "schema"
    REFERENCE = "reference"
    SEMANTIC = "semantic"
    COMPATIBILITY = "compatibility"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Metadata(BaseModel):
    """Repository metadata."""
    name: str = Field(..., description="Repository name")
    description: Optional[str] = None
    author: Optional[str] = None
    created: Optional[datetime] = Field(default_factory=datetime.now)
    modified: Optional[datetime] = Field(default_factory=datetime.now)
    tags: List[str] = []


class PolicyFragment(BaseModel):
    """Reusable PAM policy fragment."""
    id: str = Field(..., description="Fragment identifier")
    description: Optional[str] = None
    control: ControlFlag
    module: str
    parameters: Dict[str, str] = {}
    dependencies: List[str] = []
    conflicts: List[str] = []
    platforms: List[Platform] = []
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    category: PAMInterface = PAMInterface.AUTH
    
    @validator('id')
    def validate_id(cls, v):
        """Validate fragment ID format."""
        if not v or len(v) == 0:
            raise ValueError("Fragment ID cannot be empty")
        if not all(c.isalnum() or c == '_' or c == '-' for c in v):
            raise ValueError("Fragment ID must contain only alphanumeric, dash, or underscore")
        return v


class ServiceFragment(BaseModel):
    """Fragment reference in service."""
    ref: str = Field(..., description="Fragment reference")
    interface: PAMInterface
    order: int = 0


class Service(BaseModel):
    """PAM service configuration."""
    name: str = Field(..., description="Service name")
    description: Optional[str] = None
    platforms: List[Platform]
    fragments: List[ServiceFragment]
    
    @validator('fragments')
    def validate_fragments_unique(cls, v):
        """Ensure no duplicate fragment references."""
        refs = [f.ref for f in v]
        if len(refs) != len(set(refs)):
            raise ValueError("Duplicate fragment references in service")
        return v


class Dependency(BaseModel):
    """Package dependency by platform."""
    package: str
    platforms: Dict[Platform, str]  # {Platform: version_spec}


class Renderer(BaseModel):
    """Rendering configuration."""
    name: str
    type: RendererType
    target_path: str
    format: str = "standard"
    backup: bool = True


class DependencyNode(BaseModel):
    """Node in dependency graph."""
    id: str
    node_type: str = Field(..., alias="type")  # fragment, service, renderer
    version: Optional[str] = None


class DependencyEdge(BaseModel):
    """Edge in dependency graph."""
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    edge_type: str = Field(..., alias="type")  # depends_on, conflicts_with, references
    required: bool = True


class DependencyGraph(BaseModel):
    """Complete dependency graph."""
    schema_version: str
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]
    
    def has_cycles(self) -> bool:
        """Detect circular dependencies."""
        visited = set()
        rec_stack = set()
        
        def visit(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for edge in self.edges:
                if edge.from_node == node_id:
                    if edge.to_node not in visited:
                        if visit(edge.to_node):
                            return True
                    elif edge.to_node in rec_stack:
                        return True
            
            rec_stack.remove(node_id)
            return False
        
        for node in self.nodes:
            if node.id not in visited:
                if visit(node.id):
                    return True
        return False


class ValidationError(BaseModel):
    """Validation error with context."""
    error_type: ValidationErrorType
    severity: ErrorSeverity
    message: str
    location: Optional[str] = None
    context: Dict = {}


class ValidationReport(BaseModel):
    """Configuration validation report."""
    schema_version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    valid: bool
    errors: List[ValidationError] = []
    warnings: List[str] = []
    statistics: Dict = {}
    
    def add_error(self, error: ValidationError) -> None:
        """Add validation error."""
        self.errors.append(error)
        if error.severity == ErrorSeverity.ERROR:
            self.valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add warning."""
        self.warnings.append(warning)
    
    def summary(self) -> str:
        """Generate validation summary."""
        return (
            f"Validation Report:\n"
            f"  Valid: {self.valid}\n"
            f"  Errors: {len(self.errors)}\n"
            f"  Warnings: {len(self.warnings)}\n"
            f"  Timestamp: {self.timestamp.isoformat()}"
        )


class CustomPAMConfig(BaseModel):
    """Top-level custom PAM configuration document."""
    schema_version: str = "1.0"
    application_version: str
    repository_version: str
    metadata: Metadata
    services: List[Service]
    policy_fragments: List[PolicyFragment]
    dependencies: List[Dependency] = []
    renderers: List[Renderer] = []
    
    @validator('schema_version')
    def validate_schema_version(cls, v):
        """Validate schema version format."""
        try:
            SchemaVersion(v)
            return v
        except ValueError as e:
            raise ValueError(str(e))
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = False
        validate_assignment = True


class RepositoryMetadata(BaseModel):
    """Repository metadata and compatibility."""
    schema_version: str
    application_version: str
    supported_schemas: List[str] = []
    platforms: List[Dict] = []
    features: List[Dict] = []


# Export all models
__all__ = [
    'Metadata',
    'PolicyFragment',
    'Service',
    'ServiceFragment',
    'Dependency',
    'Renderer',
    'DependencyGraph',
    'DependencyNode',
    'DependencyEdge',
    'ValidationError',
    'ValidationReport',
    'CustomPAMConfig',
    'RepositoryMetadata',
    'PAMInterface',
    'ControlFlag',
    'Platform',
    'SecurityLevel',
    'RendererType',
    'ValidationErrorType',
    'ErrorSeverity',
]
