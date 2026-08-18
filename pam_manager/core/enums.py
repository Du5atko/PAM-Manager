"""Core enumerations for PAM Manager."""

from enum import Enum, auto


class Platform(Enum):
    """Supported operating system platforms."""

    DEBIAN = auto()
    UBUNTU = auto()
    LINUX_MINT = auto()
    KALI_LINUX = auto()
    REDHAT = auto()
    ROCKY_LINUX = auto()
    ALMA_LINUX = auto()
    CENTOS_STREAM = auto()
    FEDORA = auto()
    FREEBSD = auto()
    OPENBSD = auto()
    NETBSD = auto()
    UNKNOWN = auto()

    def __str__(self) -> str:
        """Return human-readable platform name."""
        names = {
            Platform.DEBIAN: "Debian",
            Platform.UBUNTU: "Ubuntu",
            Platform.LINUX_MINT: "Linux Mint",
            Platform.KALI_LINUX: "Kali Linux",
            Platform.REDHAT: "RedHat Enterprise Linux",
            Platform.ROCKY_LINUX: "Rocky Linux",
            Platform.ALMA_LINUX: "AlmaLinux",
            Platform.CENTOS_STREAM: "CentOS Stream",
            Platform.FEDORA: "Fedora",
            Platform.FREEBSD: "FreeBSD",
            Platform.OPENBSD: "OpenBSD",
            Platform.NETBSD: "NetBSD",
            Platform.UNKNOWN: "Unknown",
        }
        return names.get(self, "Unknown")


class PackageManager(Enum):
    """Supported package managers."""

    APT = auto()
    DNF = auto()
    YUM = auto()
    PKG = auto()
    UNKNOWN = auto()

    def __str__(self) -> str:
        """Return human-readable package manager name."""
        names = {
            PackageManager.APT: "APT",
            PackageManager.DNF: "DNF",
            PackageManager.YUM: "YUM",
            PackageManager.PKG: "PKG",
            PackageManager.UNKNOWN: "Unknown",
        }
        return names.get(self, "Unknown")


class PAMFacility(Enum):
    """PAM facility types (service groups)."""

    AUTH = "auth"
    ACCOUNT = "account"
    SESSION = "session"
    PASSWORD = "password"

    def __str__(self) -> str:
        """Return string representation."""
        return self.value


class PAMControlFlag(Enum):
    """PAM control flags for module success/failure handling."""

    REQUIRED = "required"
    REQUISITE = "requisite"
    SUFFICIENT = "sufficient"
    OPTIONAL = "optional"

    def __str__(self) -> str:
        """Return string representation."""
        return self.value


class PAMService(Enum):
    """PAM services (policy names) supported by the system."""

    LOGIN = "login"
    SSHD = "sshd"
    SUDO = "sudo"
    SU = "su"
    PASSWD = "passwd"
    CRON = "cron"
    COMMON_AUTH = "common-auth"
    COMMON_ACCOUNT = "common-account"
    COMMON_PASSWORD = "common-password"
    COMMON_SESSION = "common-session"
    SYSTEM_AUTH = "system-auth"
    PASSWORD_AUTH = "password-auth"
    GDM = "gdm"
    LIGHTDM = "lightdm"
    XDM = "xdm"
    LOCAL_LOGIN = "local_login"
    REMOTE_LOGIN = "remote_login"

    def __str__(self) -> str:
        """Return string representation."""
        return self.value


class SecurityCategory(Enum):
    """High-level security policy categories."""

    AUTHENTICATION = "authentication"
    IDENTITY_SOURCES = "identity_sources"
    MULTIFACTOR = "multifactor"
    POLICYING = "policying"
    AUTHORIZATION = "authorization"
    SESSION_MANAGEMENT = "session_management"
    AUDITING = "auditing"
    COMPATIBILITY = "compatibility"
    RECOVERY = "recovery"

    def __str__(self) -> str:
        """Return human-readable category name."""
        names = {
            SecurityCategory.AUTHENTICATION: "Authentication",
            SecurityCategory.IDENTITY_SOURCES: "Identity Sources",
            SecurityCategory.MULTIFACTOR: "Multifactor Authentication",
            SecurityCategory.POLICYING: "Policying",
            SecurityCategory.AUTHORIZATION: "Authorization",
            SecurityCategory.SESSION_MANAGEMENT: "Session Management",
            SecurityCategory.AUDITING: "Auditing",
            SecurityCategory.COMPATIBILITY: "Compatibility",
            SecurityCategory.RECOVERY: "Recovery",
        }
        return names.get(self, "Unknown")


class AuthenticationMethod(Enum):
    """Supported authentication methods."""

    LOCAL = "local"
    LDAP = "ldap"
    ACTIVE_DIRECTORY = "active_directory"
    KERBEROS = "kerberos"
    RADIUS = "radius"
    SQL = "sql"
    REST_API = "rest_api"
    SSH_KEYS = "ssh_keys"
    CERTIFICATES = "certificates"

    def __str__(self) -> str:
        """Return human-readable method name."""
        names = {
            AuthenticationMethod.LOCAL: "Local Authentication",
            AuthenticationMethod.LDAP: "LDAP",
            AuthenticationMethod.ACTIVE_DIRECTORY: "Active Directory",
            AuthenticationMethod.KERBEROS: "Kerberos",
            AuthenticationMethod.RADIUS: "RADIUS",
            AuthenticationMethod.SQL: "SQL",
            AuthenticationMethod.REST_API: "REST API",
            AuthenticationMethod.SSH_KEYS: "SSH Keys",
            AuthenticationMethod.CERTIFICATES: "Certificates",
        }
        return names.get(self, "Unknown")


class ComplianceLevel(Enum):
    """Configuration compliance levels."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        """Return string representation."""
        return self.value


class ValidationStatus(Enum):
    """Configuration validation status."""

    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    ERROR = "error"

    def __str__(self) -> str:
        """Return string representation."""
        return self.value


__all__ = [
    "Platform",
    "PackageManager",
    "PAMFacility",
    "PAMControlFlag",
    "PAMService",
    "SecurityCategory",
    "AuthenticationMethod",
    "ComplianceLevel",
    "ValidationStatus",
]
