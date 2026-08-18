"""
CI/CD Integration Module
Framework for automated hardware testing and validation in CI/CD pipelines.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class TestEnvironment(Enum):
    """CI/CD test environment types."""
    LOCAL = "local"  # Local development machine
    DOCKER = "docker"  # Docker container
    VM = "vm"  # Virtual machine
    CI_CD = "ci_cd"  # CI/CD pipeline (GitHub Actions, etc.)
    HARDWARE_LAB = "hardware_lab"  # Physical hardware lab


@dataclass
class TestResult:
    """Result of a CI/CD test run."""
    test_name: str  # Test identifier
    environment: str  # Environment where test ran
    passed: bool  # Whether test passed
    duration_seconds: float  # Test duration
    error_message: Optional[str] = None  # Error if failed
    hardware_profile: Optional[str] = None  # Hardware profile tested
    metrics: Dict = None  # Additional metrics


class CICDTestFramework:
    """
    Framework for automated GUI testing in CI/CD environments.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize CI/CD test framework.
        
        Args:
            output_dir: Directory for test results and artifacts
        """
        self.output_dir = output_dir or Path.cwd() / '.pam-ci-results'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TestResult] = []
        self.environment = self._detect_environment()
    
    @staticmethod
    def _detect_environment() -> TestEnvironment:
        """Detect which CI/CD environment we're running in."""
        # GitHub Actions
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            return TestEnvironment.CI_CD
        
        # GitLab CI
        if os.environ.get('GITLAB_CI') == 'true':
            return TestEnvironment.CI_CD
        
        # Generic CI detection
        ci_env_vars = ['CI', 'CONTINUOUS_INTEGRATION', 'BUILD_ID', 'BUILD_NUMBER']
        if any(os.environ.get(var) for var in ci_env_vars):
            return TestEnvironment.CI_CD
        
        # Docker detection
        if Path('/.dockerenv').exists():
            return TestEnvironment.DOCKER
        
        # Default to local
        return TestEnvironment.LOCAL
    
    def run_environment_detection_test(self) -> Tuple[bool, str]:
        """
        Test environment detection module.
        
        Returns:
            (success, error_message)
        """
        import time
        start = time.time()
        
        try:
            from pam_manager.gui_environment import GuiEnvironment
            
            caps = GuiEnvironment.detect_all()
            
            # Verify basic fields are populated
            assert caps.display_server is not None
            assert caps.x11_server is not None
            assert caps.qt_version in (5, 6, 0)
            
            duration = time.time() - start
            result = TestResult(
                test_name='environment_detection',
                environment=self.environment.value,
                passed=True,
                duration_seconds=duration
            )
            self.results.append(result)
            return True, ""
        
        except Exception as e:
            duration = time.time() - start
            result = TestResult(
                test_name='environment_detection',
                environment=self.environment.value,
                passed=False,
                duration_seconds=duration,
                error_message=str(e)
            )
            self.results.append(result)
            return False, str(e)
    
    def run_adapter_factory_test(self) -> Tuple[bool, str]:
        """
        Test adapter factory module.
        
        Returns:
            (success, error_message)
        """
        import time
        start = time.time()
        
        try:
            from pam_manager.gui_adapters import AdapterFactory
            from pam_manager.gui_environment import GuiEnvironment
            
            caps = GuiEnvironment.detect_all()
            
            # Test adapter selection
            adapter = AdapterFactory.get_adapter_for_environment(caps)
            assert adapter is not None
            
            # Test fallback chain
            chain = AdapterFactory.get_fallback_chain()
            assert len(chain) >= 6
            
            duration = time.time() - start
            result = TestResult(
                test_name='adapter_factory',
                environment=self.environment.value,
                passed=True,
                duration_seconds=duration
            )
            self.results.append(result)
            return True, ""
        
        except Exception as e:
            duration = time.time() - start
            result = TestResult(
                test_name='adapter_factory',
                environment=self.environment.value,
                passed=False,
                duration_seconds=duration,
                error_message=str(e)
            )
            self.results.append(result)
            return False, str(e)
    
    def run_hardware_validation_test(self) -> Tuple[bool, str]:
        """
        Test hardware validation module.
        
        Returns:
            (success, error_message)
        """
        import time
        start = time.time()
        
        try:
            from pam_manager.gui_validation import HardwareValidator
            
            validator = HardwareValidator()
            
            # Validate current profile
            profiles = list(validator.KNOWN_PROFILES.keys())
            assert len(profiles) >= 8
            
            duration = time.time() - start
            result = TestResult(
                test_name='hardware_validation',
                environment=self.environment.value,
                passed=True,
                duration_seconds=duration,
                metrics={'profiles_defined': len(profiles)}
            )
            self.results.append(result)
            return True, ""
        
        except Exception as e:
            duration = time.time() - start
            result = TestResult(
                test_name='hardware_validation',
                environment=self.environment.value,
                passed=False,
                duration_seconds=duration,
                error_message=str(e)
            )
            self.results.append(result)
            return False, str(e)
    
    def run_remote_display_test(self) -> Tuple[bool, str]:
        """
        Test remote display detection module.
        
        Returns:
            (success, error_message)
        """
        import time
        start = time.time()
        
        try:
            from pam_manager.gui_remote_display import RemoteDisplayDetector
            
            # Test local display
            os.environ['DISPLAY'] = ':0'
            local_info = RemoteDisplayDetector.detect_remote_display()
            assert local_info.is_remote is False
            
            # Test remote display
            os.environ['DISPLAY'] = 'remote.host:10'
            remote_info = RemoteDisplayDetector.detect_remote_display()
            assert remote_info.is_remote is True
            
            duration = time.time() - start
            result = TestResult(
                test_name='remote_display',
                environment=self.environment.value,
                passed=True,
                duration_seconds=duration
            )
            self.results.append(result)
            return True, ""
        
        except Exception as e:
            duration = time.time() - start
            result = TestResult(
                test_name='remote_display',
                environment=self.environment.value,
                passed=False,
                duration_seconds=duration,
                error_message=str(e)
            )
            self.results.append(result)
            return False, str(e)
    
    def run_all_tests(self) -> bool:
        """
        Run all CI/CD tests.
        
        Returns:
            True if all tests passed
        """
        tests = [
            ('Environment Detection', self.run_environment_detection_test),
            ('Adapter Factory', self.run_adapter_factory_test),
            ('Hardware Validation', self.run_hardware_validation_test),
            ('Remote Display', self.run_remote_display_test),
        ]
        
        print(f"\n{'='*70}")
        print(f"CI/CD TEST FRAMEWORK - {self.environment.value.upper()}")
        print(f"{'='*70}\n")
        
        all_passed = True
        for test_name, test_func in tests:
            passed, error = test_func()
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {test_name}")
            if error:
                print(f"       Error: {error[:60]}...")
            all_passed = all_passed and passed
        
        print(f"\n{'='*70}")
        passed_count = sum(1 for r in self.results if r.passed)
        total_count = len(self.results)
        print(f"Results: {passed_count}/{total_count} tests passed")
        print(f"{'='*70}\n")
        
        return all_passed
    
    def save_results(self, filepath: Optional[Path] = None) -> Path:
        """
        Save test results to JSON file.
        
        Args:
            filepath: Path to save results
            
        Returns:
            Path to saved results
        """
        if filepath is None:
            filepath = self.output_dir / f"test-results-{self.environment.value}.json"
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        results_data = {
            'environment': self.environment.value,
            'total_tests': len(self.results),
            'passed': sum(1 for r in self.results if r.passed),
            'failed': sum(1 for r in self.results if not r.passed),
            'results': [asdict(r) for r in self.results],
        }
        
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        return filepath
    
    def generate_report(self) -> str:
        """
        Generate test report in human-readable format.
        
        Returns:
            Report as string
        """
        report = []
        report.append("=" * 70)
        report.append("PAM MANAGER GUI TEST REPORT")
        report.append("=" * 70)
        report.append(f"\nEnvironment: {self.environment.value}")
        report.append(f"Total Tests: {len(self.results)}")
        report.append(f"Passed: {sum(1 for r in self.results if r.passed)}")
        report.append(f"Failed: {sum(1 for r in self.results if not r.passed)}")
        
        report.append("\nTest Details:")
        for result in self.results:
            status = "✓" if result.passed else "✗"
            report.append(f"\n{status} {result.test_name}")
            report.append(f"  Duration: {result.duration_seconds:.2f}s")
            if result.error_message:
                report.append(f"  Error: {result.error_message}")
            if result.metrics:
                for key, value in result.metrics.items():
                    report.append(f"  {key}: {value}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)


def run_ci_cd_tests(output_dir: Optional[Path] = None) -> bool:
    """
    Convenience function to run all CI/CD tests.
    
    Args:
        output_dir: Directory for test results
        
    Returns:
        True if all tests passed
    """
    framework = CICDTestFramework(output_dir)
    all_passed = framework.run_all_tests()
    
    # Save results
    framework.save_results()
    
    # Print report
    report = framework.generate_report()
    print(report)
    
    return all_passed
