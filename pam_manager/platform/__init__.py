"""Platform module exports - Phase 3 Platform Support."""

from pam_manager.platform.detector import PlatformDetector
from pam_manager.platform.metadata import (
    Platform,
    PAMFacility,
    PlatformParameter,
    PlatformModuleConfig,
    PlatformPackageManager,
    PlatformMetadata,
    COMMON_PLATFORM_CONFIGS,
)
from pam_manager.platform.config_generator import (
    PlatformConfigGenerator,
    PlatformCompatibilityChecker,
)
from pam_manager.platform.detection_enhanced import (
    PlatformDetector as EnhancedPlatformDetector,
    PlatformCapabilities,
    PlatformCompatibilityMatrix,
)

__all__ = [
    # Existing exports
    "PlatformDetector",
    # Metadata exports (Phase 3)
    "Platform",
    "PAMFacility",
    "PlatformParameter",
    "PlatformModuleConfig",
    "PlatformPackageManager",
    "PlatformMetadata",
    "COMMON_PLATFORM_CONFIGS",
    # Config generator exports (Phase 3)
    "PlatformConfigGenerator",
    "PlatformCompatibilityChecker",
    # Enhanced detection exports (Phase 3)
    "EnhancedPlatformDetector",
    "PlatformCapabilities",
    "PlatformCompatibilityMatrix",
]
