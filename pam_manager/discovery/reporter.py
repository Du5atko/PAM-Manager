"""PAM discovery reporting functionality."""

from datetime import datetime
from typing import Dict, List

from pam_manager.discovery.detector import DiscoveryDetector
from pam_manager.discovery.parser import DiscoveryReport


class DiscoveryReporter:
    """Generate formatted reports from discovery data."""

    def __init__(self, detector: DiscoveryDetector) -> None:
        """Initialize reporter with detector.

        Args:
            detector: DiscoveryDetector instance with discovered data
        """
        self.detector = detector
        self.report = detector.discover_modules()

    def generate_text_report(self) -> str:
        """Generate human-readable text report.

        Returns:
            Formatted text report
        """
        lines = []

        lines.append("=" * 80)
        lines.append("PAM MODULE DISCOVERY REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Platform: {self.report.platform.name}")
        lines.append("")

        # Summary section
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total modules discovered: {self.report.total_modules_discovered}")
        lines.append(f"Unique modules: {self.report.unique_modules}")
        lines.append(f"PAM configuration files: {len(self.report.installed_pam_files)}")
        lines.append("")

        # Modules by facility
        lines.append("MODULES BY FACILITY")
        lines.append("-" * 80)
        for facility, count in sorted(self.report.modules_by_facility.items()):
            lines.append(f"  {facility:15} {count:3} modules")
        lines.append("")

        # Modules by service
        lines.append("MODULES BY SERVICE (Top 10)")
        lines.append("-" * 80)
        sorted_services = sorted(
            self.report.modules_by_service.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]
        for service, count in sorted_services:
            lines.append(f"  {service:30} {count:3} modules")
        lines.append("")

        # Database comparison
        comparison = self.detector.compare_with_database()
        lines.append("DATABASE COMPARISON")
        lines.append("-" * 80)
        lines.append(f"Modules in database: {comparison['database_count']}")
        lines.append(f"Modules installed: {comparison['installed_count']}")
        lines.append(f"Coverage: {comparison['coverage']:.1f}%")
        lines.append("")

        # Security recommendations
        lines.append("SECURITY RECOMMENDATIONS")
        lines.append("-" * 80)
        recommendations = self.detector.get_security_recommendations()
        for rec in recommendations["recommendations"]:
            lines.append(f"  • {rec}")
        lines.append("")

        # Deprecated modules
        if self.report.deprecated_modules:
            lines.append("DEPRECATED MODULES IN USE")
            lines.append("-" * 80)
            for mod in self.report.deprecated_modules:
                lines.append(f"  ✗ {mod}")
            lines.append("")

        # Missing modules
        if self.report.missing_modules:
            lines.append("UNKNOWN MODULES (NOT IN DATABASE)")
            lines.append("-" * 80)
            for mod in sorted(self.report.missing_modules)[:20]:
                instances = self.detector.get_module_by_name(mod)
                lines.append(f"  • {mod} (used in {len(instances)} places)")
            if len(self.report.missing_modules) > 20:
                lines.append(
                    f"  ... and {len(self.report.missing_modules) - 20} more"
                )
            lines.append("")

        # Configuration files
        lines.append("PAM CONFIGURATION FILES")
        lines.append("-" * 80)
        for pam_file in sorted(self.report.installed_pam_files):
            lines.append(f"  • {pam_file}")
        lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_csv_report(self) -> str:
        """Generate CSV report of all discovered modules.

        Returns:
            CSV formatted data
        """
        lines = [
            "Service,Facility,Control,Module,Arguments,Path,Is_Installed,Config_File,Line_Number"
        ]

        for module in sorted(
            self.report.all_discovered,
            key=lambda m: (m.service, m.facility, m.name),
        ):
            args_str = " ".join(module.arguments) if module.arguments else ""
            installed = "Yes" if module.is_installed else "No"

            line = (
                f'"{module.service}",'
                f'"{module.facility}",'
                f'"{module.control}",'
                f'"{module.name}",'
                f'"{args_str}",'
                f'"{module.path or ""}",'
                f'"{installed}",'
                f'"{module.config_file}",'
                f'"{module.line_number}"'
            )
            lines.append(line)

        return "\n".join(lines)

    def generate_json_report(self) -> Dict:
        """Generate JSON-compatible dictionary report.

        Returns:
            Dictionary suitable for JSON serialization
        """
        comparison = self.detector.compare_with_database()
        recommendations = self.detector.get_security_recommendations()

        return {
            "generated": datetime.now().isoformat(),
            "platform": self.report.platform.name,
            "summary": {
                "total_discovered": self.report.total_modules_discovered,
                "unique_modules": self.report.unique_modules,
                "config_files": len(self.report.installed_pam_files),
            },
            "by_facility": self.report.modules_by_facility,
            "by_service": self.report.modules_by_service,
            "database_comparison": {
                "installed_count": comparison["installed_count"],
                "database_count": comparison["database_count"],
                "coverage_percent": comparison["coverage"],
            },
            "installed_modules": comparison["installed"],
            "unknown_modules": self.report.missing_modules,
            "unused_modules": comparison["not_in_use"][:20],
            "deprecated_in_use": self.report.deprecated_modules,
            "recommendations": recommendations["recommendations"],
            "discovered_modules": [
                {
                    "name": m.name,
                    "service": m.service,
                    "facility": m.facility,
                    "control": m.control,
                    "path": m.path,
                    "installed": m.is_installed,
                    "arguments": m.arguments,
                }
                for m in self.report.all_discovered
            ],
        }

    def generate_summary_report(self) -> str:
        """Generate brief summary report.

        Returns:
            Short text summary
        """
        comparison = self.detector.compare_with_database()
        recommendations = self.detector.get_security_recommendations()

        summary = []
        summary.append("PAM DISCOVERY SUMMARY")
        summary.append(f"Platform: {self.report.platform.name}")
        summary.append(f"Discovered: {self.report.total_modules_discovered} modules")
        summary.append(f"Database Coverage: {comparison['coverage']:.1f}%")
        summary.append("")
        summary.append("Top Issues:")
        for i, rec in enumerate(recommendations["recommendations"][:5], 1):
            summary.append(f"  {i}. {rec[:70]}")

        return "\n".join(summary)


__all__ = ["DiscoveryReporter"]
