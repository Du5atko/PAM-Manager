"""PAM Monitoring and Logging - System health checks and activity logging."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set
from datetime import datetime
from pathlib import Path
import logging
import json

from pam_manager.core import Platform
from pam_manager.discovery import DiscoveryDetector
from pam_manager.engine import PolicyEngine
from pam_manager.modules import ModuleRegistry


class HealthCheckStatus(Enum):
    """Health check status enumeration."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class HealthCheckResult:
    """Result of a health check."""

    check_name: str
    status: HealthCheckStatus
    timestamp: datetime
    message: str
    details: Dict = None
    recommendations: List[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "check_name": self.check_name,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "details": self.details or {},
            "recommendations": self.recommendations or [],
        }


@dataclass(frozen=True)
class Alert:
    """System alert."""

    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolution_timestamp": self.resolution_timestamp.isoformat()
            if self.resolution_timestamp
            else None,
        }


@dataclass(frozen=True)
class LogEntry:
    """System log entry."""

    timestamp: datetime
    level: str  # INFO, WARNING, ERROR, CRITICAL
    component: str
    message: str
    details: Dict = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "component": self.component,
            "message": self.message,
            "details": self.details or {},
        }


class PamSystemMonitor:
    """Monitors PAM system health and activity."""

    def __init__(self, platform: Platform = None) -> None:
        """Initialize monitor.

        Args:
            platform: Target platform
        """
        self.platform = platform or Platform.UBUNTU
        self.engine = PolicyEngine(platform)
        self.discovery = DiscoveryDetector(platform)
        self.registry = ModuleRegistry()
        self.health_checks: List[HealthCheckResult] = []
        self.alerts: List[Alert] = []
        self.logs: List[LogEntry] = []
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("pam_monitor")

    def run_health_checks(self) -> Dict[str, HealthCheckStatus]:
        """Run all health checks.

        Returns:
            Dictionary mapping check names to statuses
        """
        results = {}

        # Check 1: PAM files exist and readable
        result = self._check_pam_files_accessible()
        results["pam_files_accessible"] = result.status
        self.health_checks.append(result)

        # Check 2: Required modules installed
        result = self._check_required_modules()
        results["required_modules"] = result.status
        self.health_checks.append(result)

        # Check 3: Module dependencies resolved
        result = self._check_dependencies()
        results["dependencies_resolved"] = result.status
        self.health_checks.append(result)

        # Check 4: No deprecated modules in use
        result = self._check_deprecated_modules()
        results["deprecated_modules"] = result.status
        self.health_checks.append(result)

        # Check 5: Facility coverage
        result = self._check_facility_coverage()
        results["facility_coverage"] = result.status
        self.health_checks.append(result)

        # Check 6: Security configuration
        result = self._check_security_config()
        results["security_configuration"] = result.status
        self.health_checks.append(result)

        return results

    def _check_pam_files_accessible(self) -> HealthCheckResult:
        """Check if PAM files are accessible."""
        try:
            report = self.discovery.discover_modules()

            if not report.installed_pam_files:
                return HealthCheckResult(
                    check_name="pam_files_accessible",
                    status=HealthCheckStatus.CRITICAL,
                    timestamp=datetime.now(),
                    message="No PAM files found",
                    recommendations=["Check PAM installation"],
                )

            accessible_count = len(report.installed_pam_files)

            return HealthCheckResult(
                check_name="pam_files_accessible",
                status=HealthCheckStatus.HEALTHY,
                timestamp=datetime.now(),
                message=f"All {accessible_count} PAM files accessible",
                details={"files_found": accessible_count},
            )
        except Exception as e:
            self._add_alert(
                AlertSeverity.CRITICAL,
                "PAM Files Check Failed",
                f"Error checking PAM files: {e}",
            )
            return HealthCheckResult(
                check_name="pam_files_accessible",
                status=HealthCheckStatus.CRITICAL,
                timestamp=datetime.now(),
                message=f"Error: {e}",
            )

    def _check_required_modules(self) -> HealthCheckResult:
        """Check if required modules are installed."""
        try:
            report = self.discovery.discover_modules()
            discovered_modules = set(m.name for m in report.all_discovered)

            # Check for minimum required modules
            required = {"pam_unix"}
            missing = required - discovered_modules

            if missing:
                status = HealthCheckStatus.CRITICAL
                message = f"Missing required modules: {missing}"
                severity = AlertSeverity.CRITICAL
            else:
                status = HealthCheckStatus.HEALTHY
                message = f"All required modules present"
                severity = AlertSeverity.INFO

            return HealthCheckResult(
                check_name="required_modules",
                status=status,
                timestamp=datetime.now(),
                message=message,
                details={
                    "discovered_modules": len(discovered_modules),
                    "missing_modules": list(missing),
                },
                recommendations=["Install missing modules"] if missing else [],
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="required_modules",
                status=HealthCheckStatus.UNKNOWN,
                timestamp=datetime.now(),
                message=f"Error checking modules: {e}",
            )

    def _check_dependencies(self) -> HealthCheckResult:
        """Check if module dependencies are resolved."""
        try:
            report = self.discovery.discover_modules()
            discovered_names = set(m.name for m in report.all_discovered)

            unresolved = []
            for module_name in discovered_names:
                module_info = self.registry.get_module(module_name)
                if module_info and module_info.dependencies:
                    for dep in module_info.dependencies:
                        if dep not in discovered_names:
                            unresolved.append((module_name, dep))

            if unresolved:
                status = HealthCheckStatus.WARNING
                message = f"Unresolved dependencies: {len(unresolved)}"
            else:
                status = HealthCheckStatus.HEALTHY
                message = "All dependencies resolved"

            return HealthCheckResult(
                check_name="dependencies_resolved",
                status=status,
                timestamp=datetime.now(),
                message=message,
                details={"unresolved_count": len(unresolved)},
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="dependencies_resolved",
                status=HealthCheckStatus.UNKNOWN,
                timestamp=datetime.now(),
                message=f"Error checking dependencies: {e}",
            )

    def _check_deprecated_modules(self) -> HealthCheckResult:
        """Check if deprecated modules are in use."""
        try:
            report = self.discovery.discover_modules()
            deprecated_in_use = []

            for module in report.all_discovered:
                module_info = self.registry.get_module(module.name)
                if module_info and module_info.deprecated:
                    deprecated_in_use.append(module.name)

            if deprecated_in_use:
                status = HealthCheckStatus.WARNING
                message = f"Deprecated modules in use: {len(deprecated_in_use)}"
                self._add_alert(
                    AlertSeverity.WARNING,
                    "Deprecated Modules",
                    f"Deprecated modules found: {deprecated_in_use}",
                )
            else:
                status = HealthCheckStatus.HEALTHY
                message = "No deprecated modules in use"

            return HealthCheckResult(
                check_name="deprecated_modules",
                status=status,
                timestamp=datetime.now(),
                message=message,
                details={"deprecated_count": len(deprecated_in_use)},
                recommendations=[
                    f"Consider replacing {m}" for m in deprecated_in_use
                ],
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="deprecated_modules",
                status=HealthCheckStatus.UNKNOWN,
                timestamp=datetime.now(),
                message=f"Error checking deprecated modules: {e}",
            )

    def _check_facility_coverage(self) -> HealthCheckResult:
        """Check PAM facility coverage."""
        try:
            report = self.discovery.discover_modules()

            # Check for required facilities
            required_facilities = {"auth", "account", "password", "session"}
            covered_facilities = set(report.modules_by_facility.keys())

            missing_facilities = required_facilities - covered_facilities

            if missing_facilities:
                status = HealthCheckStatus.WARNING
                message = f"Missing facility coverage: {missing_facilities}"
            else:
                status = HealthCheckStatus.HEALTHY
                message = "All facilities covered"

            return HealthCheckResult(
                check_name="facility_coverage",
                status=status,
                timestamp=datetime.now(),
                message=message,
                details={
                    "covered_facilities": len(covered_facilities),
                    "missing_facilities": list(missing_facilities),
                },
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="facility_coverage",
                status=HealthCheckStatus.UNKNOWN,
                timestamp=datetime.now(),
                message=f"Error checking facility coverage: {e}",
            )

    def _check_security_config(self) -> HealthCheckResult:
        """Check security configuration."""
        try:
            report = self.discovery.discover_modules()
            recommendations = self.discovery.get_security_recommendations()

            security_issues = []
            if recommendations.get("deprecated_modules"):
                security_issues.extend(recommendations["deprecated_modules"])

            if security_issues:
                status = HealthCheckStatus.WARNING
                message = f"Security issues found: {len(security_issues)}"
            else:
                status = HealthCheckStatus.HEALTHY
                message = "Security configuration looks good"

            return HealthCheckResult(
                check_name="security_configuration",
                status=status,
                timestamp=datetime.now(),
                message=message,
                details={"security_issues": len(security_issues)},
                recommendations=recommendations.get("recommendations", []),
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="security_configuration",
                status=HealthCheckStatus.UNKNOWN,
                timestamp=datetime.now(),
                message=f"Error checking security: {e}",
            )

    def _add_alert(
        self,
        severity: AlertSeverity,
        title: str,
        description: str,
    ) -> None:
        """Add an alert.

        Args:
            severity: Alert severity
            title: Alert title
            description: Alert description
        """
        alert_id = f"alert-{datetime.now().timestamp()}"
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            title=title,
            description=description,
            timestamp=datetime.now(),
        )
        self.alerts.append(alert)
        self.logger.log(
            level=50 if severity == AlertSeverity.CRITICAL else 30,
            msg=f"{title}: {description}",
        )

    def _add_log_entry(
        self,
        level: str,
        component: str,
        message: str,
        details: Dict = None,
    ) -> None:
        """Add log entry.

        Args:
            level: Log level
            component: Component name
            message: Log message
            details: Optional details
        """
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            component=component,
            message=message,
            details=details or {},
        )
        self.logs.append(entry)

    def get_health_status(self) -> str:
        """Get overall health status.

        Returns:
            Overall status string
        """
        if not self.health_checks:
            return HealthCheckStatus.UNKNOWN.value

        statuses = [h.status for h in self.health_checks]
        critical_count = sum(1 for s in statuses if s == HealthCheckStatus.CRITICAL)
        warning_count = sum(1 for s in statuses if s == HealthCheckStatus.WARNING)

        if critical_count > 0:
            return HealthCheckStatus.CRITICAL.value
        if warning_count > 0:
            return HealthCheckStatus.WARNING.value
        return HealthCheckStatus.HEALTHY.value

    def get_health_report(self) -> str:
        """Get comprehensive health report.

        Returns:
            Formatted health report
        """
        report_lines = [
            "=" * 60,
            "PAM SYSTEM HEALTH REPORT",
            "=" * 60,
            f"Platform: {self.platform.name}",
            f"Generated: {datetime.now().isoformat()}",
            f"Overall Status: {self.get_health_status().upper()}",
            "",
            "HEALTH CHECKS:",
            "-" * 60,
        ]

        for check in self.health_checks:
            status_symbol = (
                "✓"
                if check.status == HealthCheckStatus.HEALTHY
                else "⚠" if check.status == HealthCheckStatus.WARNING
                else "✗"
            )
            report_lines.append(f"{status_symbol} {check.check_name}: {check.status.value}")
            report_lines.append(f"   {check.message}")
            if check.recommendations:
                for rec in check.recommendations:
                    report_lines.append(f"   → {rec}")

        if self.alerts:
            report_lines.extend(
                [
                    "",
                    "ALERTS:",
                    "-" * 60,
                ]
            )
            for alert in self.alerts[-10:]:  # Last 10 alerts
                symbol = "⚠" if alert.severity != AlertSeverity.CRITICAL else "✗"
                report_lines.append(f"{symbol} [{alert.severity.value}] {alert.title}")
                report_lines.append(f"   {alert.description}")

        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def get_alerts_as_json(self) -> str:
        """Get alerts as JSON.

        Returns:
            JSON string
        """
        alerts_data = [a.to_dict() for a in self.alerts]
        return json.dumps(alerts_data, indent=2)

    def get_health_checks_as_json(self) -> str:
        """Get health checks as JSON.

        Returns:
            JSON string
        """
        checks_data = [c.to_dict() for c in self.health_checks]
        return json.dumps(checks_data, indent=2)

    def save_health_report(self, filepath: str) -> bool:
        """Save health report to file.

        Args:
            filepath: Path to save report

        Returns:
            True if successful
        """
        try:
            Path(filepath).write_text(self.get_health_report())
            return True
        except Exception:
            return False

    def save_logs(self, filepath: str) -> bool:
        """Save logs to file.

        Args:
            filepath: Path to save logs

        Returns:
            True if successful
        """
        try:
            logs_data = [entry.to_dict() for entry in self.logs]
            Path(filepath).write_text(json.dumps(logs_data, indent=2))
            return True
        except Exception:
            return False

    def get_critical_alerts(self) -> List[Alert]:
        """Get unresolved critical alerts.

        Returns:
            List of critical alerts
        """
        return [
            a
            for a in self.alerts
            if a.severity == AlertSeverity.CRITICAL and not a.resolved
        ]

    def clear_old_logs(self, max_entries: int = 1000) -> None:
        """Clear old log entries keeping only recent ones.

        Args:
            max_entries: Maximum log entries to keep
        """
        if len(self.logs) > max_entries:
            self.logs = self.logs[-max_entries:]


__all__ = [
    "PamSystemMonitor",
    "HealthCheckStatus",
    "AlertSeverity",
    "HealthCheckResult",
    "Alert",
    "LogEntry",
]
