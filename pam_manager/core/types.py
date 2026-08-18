"""Core type definitions for PAM Manager."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from pam_manager.core.enums import (
    AuthenticationMethod,
    ComplianceLevel,
    PackageManager,
    PAMControlFlag,
    PAMFacility,
    PAMService,
    Platform,
    SecurityCategory,
    ValidationStatus,
)


@dataclass(frozen=True)
class SystemInfo:
    """Immutable representation of system information."""

    platform: Platform
    distribution_name: str
    distribution_version: str
    kernel_version: str
    architecture: str
    package_manager: PackageManager
    pam_config_path: Path
    pam_d_path: Path
    system_lib_path: Path

    def __str__(self) -> str:
        """Return human-readable system information."""
        return (
            f"{self.distribution_name} {self.distribution_version} "
            f"({self.platform})"
        )


@dataclass(frozen=True)
class PAMModuleParameter:
    """Parameter for a PAM module."""

    name: str
    description: str
    data_type: str
    required: bool
    default_value: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    validation_regex: Optional[str] = None


@dataclass(frozen=True)
class PAMModuleMetadata:
    """Metadata for a PAM module."""

    name: str
    description: str
    supported_facilities: Set[PAMFacility]
    supported_platforms: Set[Platform]
    parameters: Dict[str, PAMModuleParameter]
    dependencies: Set[str]
    conflicts: Set[str]
    package_names: Dict[Platform, str]
    preferred_control_flag: PAMControlFlag
    recommended_ordering: int
    deprecated: bool
    maintenance_status: str
    security_impact: str
    documentation_url: str

    def supports_facility(self, facility: PAMFacility) -> bool:
        """Check if module supports facility."""
        return facility in self.supported_facilities

    def supports_platform(self, platform: Platform) -> bool:
        """Check if module supports platform."""
        return platform in self.supported_platforms

    def get_package_name(self, platform: Platform) -> Optional[str]:
        """Get package name for platform."""
        return self.package_names.get(platform)


@dataclass(frozen=True)
class PAMConfigLine:
    """Single line of PAM configuration."""

    service: str
    facility: PAMFacility
    control_flag: PAMControlFlag
    module_name: str
    module_args: Dict[str, Optional[str]] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return PAM configuration format."""
        args_str = " ".join(
            f"{key}={value}" if value else key
            for key, value in self.module_args.items()
        )
        if args_str:
            return (
                f"{self.service} {self.facility} {self.control_flag} "
                f"{self.module_name} {args_str}"
            )
        return (
            f"{self.service} {self.facility} {self.control_flag} {self.module_name}"
        )


@dataclass(frozen=True)
class AuthenticationPolicy:
    """Authentication configuration section."""

    enabled: bool = True
    primary_method: Optional[AuthenticationMethod] = None
    fallback_methods: List[AuthenticationMethod] = field(default_factory=list)
    local_authentication_enabled: bool = True
    cache_credentials: bool = False


@dataclass(frozen=True)
class IdentitySourcesPolicy:
    """Identity sources configuration section."""

    local_users_enabled: bool = True
    ldap_enabled: bool = False
    ldap_uri: Optional[str] = None
    ldap_base_dn: Optional[str] = None
    active_directory_enabled: bool = False
    kerberos_enabled: bool = False
    nss_sources: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class MultifactorPolicy:
    """Multifactor authentication configuration section."""

    enabled: bool = False
    require_mfa_for_all: bool = False
    methods: List[str] = field(default_factory=list)
    grace_period_seconds: int = 0
    challenge_timeout_seconds: int = 300


@dataclass(frozen=True)
class PasswordPolicy:
    """Password policy configuration."""

    minimum_length: int = 8
    require_uppercase: bool = False
    require_lowercase: bool = False
    require_digits: bool = False
    require_special: bool = False
    history_count: int = 0
    expiration_days: int = 0
    minimum_age_days: int = 0
    warning_days: int = 7
    max_repeat_characters: int = 0


@dataclass(frozen=True)
class AccountLockoutPolicy:
    """Account lockout configuration."""

    enabled: bool = False
    attempts_threshold: int = 5
    lockout_duration_minutes: int = 15
    reset_counter_minutes: int = 60


@dataclass(frozen=True)
class TimeRestrictionPolicy:
    """Time-based access restrictions."""

    enabled: bool = False
    allowed_hours: Optional[str] = None
    denied_days: Optional[List[str]] = None


@dataclass(frozen=True)
class PoliciyingPolicy:
    """Access control and restriction policies."""

    password: PasswordPolicy = field(default_factory=PasswordPolicy)
    account_lockout: AccountLockoutPolicy = field(
        default_factory=AccountLockoutPolicy
    )
    time_restrictions: TimeRestrictionPolicy = field(
        default_factory=TimeRestrictionPolicy
    )
    login_delay_seconds: int = 0


@dataclass(frozen=True)
class AuthorizationPolicy:
    """Authorization configuration section."""

    enforce_via_pam: bool = False
    allowed_users: Optional[List[str]] = None
    denied_users: Optional[List[str]] = None
    allowed_groups: Optional[List[str]] = None
    denied_groups: Optional[List[str]] = None


@dataclass(frozen=True)
class SessionPolicy:
    """Session management configuration section."""

    use_systemd: bool = False
    create_keyring: bool = False
    session_timeout_minutes: Optional[int] = None
    max_sessions_per_user: Optional[int] = None


@dataclass(frozen=True)
class AuditingPolicy:
    """Auditing and logging configuration section."""

    log_successful_login: bool = True
    log_failed_login: bool = True
    log_password_changes: bool = True
    log_to_syslog: bool = True
    syslog_facility: str = "auth"
    verbosity_level: int = 1


@dataclass(frozen=True)
class SecurityPolicy:
    """Complete security policy model."""

    name: str
    version: str
    created_timestamp: str
    last_modified_timestamp: str
    description: str = ""

    authentication: AuthenticationPolicy = field(default_factory=AuthenticationPolicy)
    identity_sources: IdentitySourcesPolicy = field(
        default_factory=IdentitySourcesPolicy
    )
    multifactor: MultifactorPolicy = field(default_factory=MultifactorPolicy)
    policying: PoliciyingPolicy = field(default_factory=PoliciyingPolicy)
    authorization: AuthorizationPolicy = field(default_factory=AuthorizationPolicy)
    session: SessionPolicy = field(default_factory=SessionPolicy)
    auditing: AuditingPolicy = field(default_factory=AuditingPolicy)

    def to_dict(self) -> Dict:
        """Convert policy to dictionary for serialization."""
        from dataclasses import asdict

        return asdict(self)


@dataclass(frozen=True)
class ValidationResult:
    """Result of configuration validation."""

    status: ValidationStatus
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Return human-readable validation result."""
        lines = [f"Status: {self.status}"]
        if self.errors:
            lines.append(f"Errors: {len(self.errors)}")
            for error in self.errors[:3]:
                lines.append(f"  - {error}")
            if len(self.errors) > 3:
                lines.append(f"  ... and {len(self.errors) - 3} more")
        if self.warnings:
            lines.append(f"Warnings: {len(self.warnings)}")
            for warning in self.warnings[:3]:
                lines.append(f"  - {warning}")
            if len(self.warnings) > 3:
                lines.append(f"  ... and {len(self.warnings) - 3} more")
        return "\n".join(lines)


@dataclass(frozen=True)
class ConfigurationSummary:
    """Summary of PAM configuration."""

    system_info: SystemInfo
    policy: SecurityPolicy
    enabled_modules: Set[str]
    disabled_modules: Set[str]
    conflicting_modules: Set[str]
    missing_dependencies: Set[str]
    validation_result: ValidationResult
    created_timestamp: str
    backup_location: Optional[Path] = None


__all__ = [
    "SystemInfo",
    "PAMModuleParameter",
    "PAMModuleMetadata",
    "PAMConfigLine",
    "AuthenticationPolicy",
    "IdentitySourcesPolicy",
    "MultifactorPolicy",
    "PasswordPolicy",
    "AccountLockoutPolicy",
    "TimeRestrictionPolicy",
    "PoliciyingPolicy",
    "AuthorizationPolicy",
    "SessionPolicy",
    "AuditingPolicy",
    "SecurityPolicy",
    "ValidationResult",
    "ConfigurationSummary",
]
