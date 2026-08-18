"""
Hardware Testing and Validation Module
Framework for validating GUI detection and rendering on various hardware configurations.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List, Callable
from enum import Enum


class HardwareCategory(Enum):
    """Hardware configuration categories."""
    GPU_NVIDIA = "nvidia"  # NVIDIA GPU
    GPU_AMD = "amd"  # AMD/Radeon GPU
    GPU_INTEL = "intel"  # Intel integrated GPU
    GPU_HYBRID = "hybrid"  # Multiple GPUs
    GPU_NONE = "none"  # No GPU / Software only
    DISPLAY_X11_LOCAL = "x11_local"  # Local X11
    DISPLAY_X11_REMOTE = "x11_remote"  # Remote X11
    DISPLAY_WAYLAND = "wayland"  # Wayland
    DISPLAY_HEADLESS = "headless"  # Headless/offscreen


@dataclass
class HardwareProfile:
    """Hardware profile for testing."""
    name: str  # Profile identifier
    category: HardwareCategory  # Hardware category
    description: str  # Human-readable description
    gpu_vendor: Optional[str] = None  # GPU vendor
    display_type: Optional[str] = None  # Display type
    expected_capabilities: Dict[str, bool] = None  # Expected capability flags


@dataclass
class ValidationResult:
    """Result of a single validation test."""
    test_name: str
    passed: bool
    expected: str
    actual: str
    duration_ms: float
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class HardwareValidator:
    """
    Validates GUI detection and rendering on various hardware.
    Tests actual detection against expected capabilities.
    """
    
    KNOWN_PROFILES = {
        'nvidia-gpu': HardwareProfile(
            name='nvidia-gpu',
            category=HardwareCategory.GPU_NVIDIA,
            description='NVIDIA GPU with GLX support',
            gpu_vendor='nvidia',
            display_type='x11',
            expected_capabilities={
                'gpu_acceleration': True,
                'glx': True,
                'egl': True,
                'vulkan': True,
                'nvidia_vendor': True,
            }
        ),
        'amd-gpu': HardwareProfile(
            name='amd-gpu',
            category=HardwareCategory.GPU_AMD,
            description='AMD/Radeon GPU with GLX support',
            gpu_vendor='amd',
            display_type='x11',
            expected_capabilities={
                'gpu_acceleration': True,
                'glx': True,
                'egl': True,
                'amd_vendor': True,
            }
        ),
        'intel-gpu': HardwareProfile(
            name='intel-gpu',
            category=HardwareCategory.GPU_INTEL,
            description='Intel integrated GPU with GLX support',
            gpu_vendor='intel',
            display_type='x11',
            expected_capabilities={
                'gpu_acceleration': True,
                'glx': True,
                'egl': True,
                'intel_vendor': True,
            }
        ),
        'hybrid-gpu': HardwareProfile(
            name='hybrid-gpu',
            category=HardwareCategory.GPU_HYBRID,
            description='Hybrid GPU configuration (integrated + discrete)',
            gpu_vendor='hybrid',
            display_type='x11',
            expected_capabilities={
                'gpu_acceleration': True,
                'glx': True,
                'multiple_gpus': True,
            }
        ),
        'cpu-only': HardwareProfile(
            name='cpu-only',
            category=HardwareCategory.GPU_NONE,
            description='CPU-only rendering (no GPU)',
            gpu_vendor=None,
            display_type='x11',
            expected_capabilities={
                'gpu_acceleration': False,
                'software_rendering': True,
            }
        ),
        'wayland': HardwareProfile(
            name='wayland',
            category=HardwareCategory.DISPLAY_WAYLAND,
            description='Wayland display server',
            display_type='wayland',
            expected_capabilities={
                'wayland_native': True,
                'gpu_acceleration': False,  # Conservative for Wayland
            }
        ),
        'x11-remote': HardwareProfile(
            name='x11-remote',
            category=HardwareCategory.DISPLAY_X11_REMOTE,
            description='Remote X11 display',
            display_type='x11-remote',
            expected_capabilities={
                'gpu_acceleration': False,  # No GPU over network
                'software_rendering': True,
            }
        ),
        'headless': HardwareProfile(
            name='headless',
            category=HardwareCategory.DISPLAY_HEADLESS,
            description='Headless/offscreen rendering',
            display_type='headless',
            expected_capabilities={
                'offscreen': True,
                'gpu_acceleration': False,
            }
        ),
    }
    
    def __init__(self):
        """Initialize validator."""
        self.results: List[ValidationResult] = []
        self.profiles_tested: List[str] = []
    
    def validate_profile(self, profile: HardwareProfile) -> List[ValidationResult]:
        """
        Validate hardware profile against actual detection.
        
        Args:
            profile: HardwareProfile to validate
            
        Returns:
            List of ValidationResult for each capability
        """
        import time
        
        profile_results = []
        
        # Import detection here to avoid circular imports
        try:
            from pam_manager.gui_environment import GuiEnvironment
        except ImportError:
            return profile_results
        
        # Get detected capabilities
        start = time.time()
        try:
            detected = GuiEnvironment.detect_all()
            detected_dict = detected.to_dict()
        except Exception as e:
            return [ValidationResult(
                test_name=f'detect_all/{profile.name}',
                passed=False,
                expected='detection success',
                actual='detection failed',
                duration_ms=(time.time() - start) * 1000,
                error=str(e)
            )]
        
        # Validate each expected capability
        for capability, expected_value in (profile.expected_capabilities or {}).items():
            actual_value = self._get_capability_value(detected_dict, capability)
            
            passed = actual_value == expected_value
            
            result = ValidationResult(
                test_name=f'{capability}/{profile.name}',
                passed=passed,
                expected=str(expected_value),
                actual=str(actual_value),
                duration_ms=(time.time() - start) * 1000,
            )
            
            profile_results.append(result)
        
        self.profiles_tested.append(profile.name)
        self.results.extend(profile_results)
        
        return profile_results
    
    @staticmethod
    def _get_capability_value(caps_dict: dict, capability: str) -> bool:
        """Extract capability value from capabilities dictionary."""
        parts = capability.split('_')
        
        # Handle nested lookups like 'gpu_acceleration.glx'
        value = caps_dict
        for part in capability.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return False
        
        return bool(value)
    
    def validate_all_profiles(self) -> Dict[str, List[ValidationResult]]:
        """
        Validate all known hardware profiles.
        
        Returns:
            Dict mapping profile names to validation results
        """
        results_by_profile = {}
        
        for profile_name, profile in self.KNOWN_PROFILES.items():
            results = self.validate_profile(profile)
            results_by_profile[profile_name] = results
        
        return results_by_profile
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get validation summary.
        
        Returns:
            Summary dict with statistics
        """
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total if total > 0 else 0.0,
            'profiles_tested': self.profiles_tested,
            'failed_tests': [r.to_dict() for r in self.results if not r.passed],
        }
    
    def print_report(self):
        """Print validation report."""
        summary = self.get_summary()
        
        print("\n" + "=" * 70)
        print("HARDWARE VALIDATION REPORT")
        print("=" * 70)
        
        print(f"\nProfiles Tested: {', '.join(summary['profiles_tested'])}")
        print(f"\nResults:")
        print(f"  Total tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']} ✓")
        print(f"  Failed: {summary['failed']} ✗")
        print(f"  Pass rate: {summary['pass_rate']*100:.1f}%")
        
        if summary['failed_tests']:
            print(f"\nFailed Tests:")
            for test in summary['failed_tests']:
                print(f"  ✗ {test['test_name']}")
                print(f"    Expected: {test['expected']}")
                print(f"    Actual: {test['actual']}")
                if test['error']:
                    print(f"    Error: {test['error']}")
        
        print("\n" + "=" * 70 + "\n")
    
    def save_report(self, filepath: Optional[Path] = None) -> Path:
        """
        Save validation report to file.
        
        Args:
            filepath: Path to save report
            
        Returns:
            Path to saved report
        """
        if filepath is None:
            filepath = Path.home() / '.cache/pam-gui-validation-report.json'
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'summary': self.get_summary(),
            'detailed_results': [r.to_dict() for r in self.results],
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filepath


def run_validation_tests():
    """Run all hardware validation tests."""
    validator = HardwareValidator()
    validator.validate_all_profiles()
    validator.print_report()
    filepath = validator.save_report()
    print(f"Report saved to: {filepath}")
    return validator
