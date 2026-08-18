"""PAM Module Discovery - Detect installed PAM modules on system."""

from pam_manager.discovery.detector import DiscoveryDetector
from pam_manager.discovery.parser import (
    DiscoveredModule,
    DiscoveryReport,
    PamFileParser,
)
from pam_manager.discovery.reporter import DiscoveryReporter

__all__ = [
    "DiscoveredModule",
    "DiscoveryReport",
    "PamFileParser",
    "DiscoveryDetector",
    "DiscoveryReporter",
]
