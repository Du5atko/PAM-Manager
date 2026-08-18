"""PAM Manager - Production-quality PAM configuration management."""

__version__ = "0.2.0"
__author__ = "PAM Manager Contributors"
__description__ = (
    "Production-quality PAM configuration management for FreeBSD and Linux"
)

# Phase 4 - Advanced Optimization (GUI enhancements)
try:
    from .gui_parallel_detection import ParallelDetector, ParallelEnvironmentDetector
    from .gui_advanced_cache import AdvancedCache, cached_operation
    from .gui_config_optimizer import ConfigurationOptimizer, OptimizationLevel
    from .gui_cicd_integration import CICDTestFramework, TestEnvironment
    from .gui_wayland_gpu import WaylandGPUDetector
except ImportError:
    # Phase 4 modules may not be available in all environments
    pass

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    # Phase 4 exports
    "ParallelDetector",
    "ParallelEnvironmentDetector",
    "AdvancedCache",
    "cached_operation",
    "ConfigurationOptimizer",
    "OptimizationLevel",
    "CICDTestFramework",
    "TestEnvironment",
    "WaylandGPUDetector",
]
