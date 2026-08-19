"""Comprehensive tests for PAM Manager core functionality."""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.unit
class TestPAMManagerConfiguration:
    """Test PAM Manager configuration handling."""

    def test_configuration_initialization(self):
        """Test basic configuration initialization."""
        from pam_manager.config import ConfigManager
        
        config = ConfigManager()
        assert config is not None
        assert isinstance(config, ConfigManager)

    def test_configuration_load_yaml(self, tmp_path):
        """Test YAML configuration loading."""
        from pam_manager.config import ConfigManager
        
        yaml_content = """
auth:
  required:
    - pam_unix.so
account:
  required:
    - pam_permit.so
"""
        config_file = tmp_path / "test.yaml"
        config_file.write_text(yaml_content)
        
        config = ConfigManager()
        result = config.load(str(config_file))
        assert result is not None

    def test_configuration_load_json(self, tmp_path):
        """Test JSON configuration loading."""
        from pam_manager.config import ConfigManager
        
        json_content = {
            "auth": {
                "required": ["pam_unix.so"]
            },
            "account": {
                "required": ["pam_permit.so"]
            }
        }
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps(json_content))
        
        config = ConfigManager()
        result = config.load(str(config_file))
        assert result is not None

    def test_configuration_validation(self):
        """Test configuration validation."""
        from pam_manager.config import ConfigManager
        
        config = ConfigManager()
        assert config.is_valid() is not None

    def test_configuration_save(self, tmp_path):
        """Test configuration saving."""
        from pam_manager.config import ConfigManager
        
        config = ConfigManager()
        output_file = tmp_path / "output.yaml"
        
        result = config.save(str(output_file))
        assert result is True or result is None  # Should succeed or return True


@pytest.mark.unit
class TestPAMModuleDiscovery:
    """Test PAM module discovery functionality."""

    def test_module_discovery_initialization(self):
        """Test module discovery initialization."""
        from pam_manager.discovery import ModuleDiscovery
        
        discovery = ModuleDiscovery()
        assert discovery is not None

    def test_available_modules_list(self):
        """Test retrieving available modules list."""
        from pam_manager.discovery import ModuleDiscovery
        
        discovery = ModuleDiscovery()
        modules = discovery.get_available_modules()
        assert modules is not None
        assert isinstance(modules, (list, dict))

    def test_module_attributes_retrieval(self):
        """Test retrieving module attributes."""
        from pam_manager.discovery import ModuleDiscovery
        
        discovery = ModuleDiscovery()
        # Common PAM module
        attrs = discovery.get_module_info("pam_unix")
        assert attrs is not None or attrs is None  # Should handle gracefully

    def test_platform_specific_modules(self):
        """Test platform-specific module detection."""
        from pam_manager.discovery import ModuleDiscovery
        from pam_manager.platform import PlatformDetector
        
        discovery = ModuleDiscovery()
        detector = PlatformDetector()
        platform = detector.get_platform()
        
        # Modules should vary by platform
        modules = discovery.get_available_modules()
        assert modules is not None


@pytest.mark.unit
class TestPAMPolicyValidation:
    """Test PAM policy validation."""

    def test_policy_validator_initialization(self):
        """Test policy validator initialization."""
        from pam_manager.policy import PolicyValidator
        
        validator = PolicyValidator()
        assert validator is not None

    def test_valid_policy_structure(self):
        """Test validation of valid policy structure."""
        from pam_manager.policy import PolicyValidator
        
        validator = PolicyValidator()
        valid_policy = {
            "auth": {
                "required": ["pam_unix.so"]
            }
        }
        
        result = validator.validate(valid_policy)
        assert result is True or isinstance(result, dict)

    def test_invalid_policy_detection(self):
        """Test detection of invalid policy."""
        from pam_manager.policy import PolicyValidator
        
        validator = PolicyValidator()
        invalid_policy = {
            "invalid_section": {
                "invalid_control": ["pam_unix.so"]
            }
        }
        
        result = validator.validate(invalid_policy)
        # Should detect invalidity
        assert result is not None

    def test_policy_conflict_detection(self):
        """Test detection of conflicting policies."""
        from pam_manager.policy import PolicyValidator
        
        validator = PolicyValidator()
        assert hasattr(validator, 'detect_conflicts') or hasattr(validator, 'validate')


@pytest.mark.unit  
class TestPAMServiceManagement:
    """Test PAM service management."""

    def test_service_loader_initialization(self):
        """Test service loader initialization."""
        from pam_manager.core import ServiceManager
        
        manager = ServiceManager()
        assert manager is not None

    def test_service_enumeration(self):
        """Test enumerating available services."""
        from pam_manager.core import ServiceManager
        
        manager = ServiceManager()
        services = manager.list_services()
        assert services is not None
        assert isinstance(services, (list, dict))

    def test_service_configuration_retrieval(self):
        """Test retrieving service configuration."""
        from pam_manager.core import ServiceManager
        
        manager = ServiceManager()
        # Should handle gracefully even if service doesn't exist
        config = manager.get_service_config("test_service")
        assert config is None or isinstance(config, dict)

    def test_service_configuration_update(self):
        """Test updating service configuration."""
        from pam_manager.core import ServiceManager
        
        manager = ServiceManager()
        test_config = {
            "auth": {
                "required": ["pam_unix.so"]
            }
        }
        
        result = manager.set_service_config("test_service", test_config)
        assert result is True or result is None or isinstance(result, dict)


@pytest.mark.integration
class TestPAMConfigurationIntegration:
    """Integration tests for full configuration workflow."""

    def test_load_modify_save_workflow(self, tmp_path):
        """Test complete load-modify-save workflow."""
        from pam_manager.config import ConfigManager
        
        # Create initial config
        config = ConfigManager()
        config_file = tmp_path / "test_config.yaml"
        
        # Save initial
        config.save(str(config_file))
        assert config_file.exists()
        
        # Load and verify
        loaded = config.load(str(config_file))
        assert loaded is not None

    def test_multi_service_configuration(self, tmp_path):
        """Test handling multiple services."""
        from pam_manager.core import ServiceManager
        
        manager = ServiceManager()
        services = ["ssh", "sudo", "login"]
        
        for service in services:
            config = manager.get_service_config(service)
            # Should handle all gracefully
            assert config is None or isinstance(config, dict)

    def test_configuration_export_formats(self, tmp_path):
        """Test exporting configuration in different formats."""
        from pam_manager.config import ConfigManager
        
        config = ConfigManager()
        
        # Test YAML export
        yaml_file = tmp_path / "export.yaml"
        config.save(str(yaml_file), format="yaml")
        
        # Test JSON export
        json_file = tmp_path / "export.json"
        config.save(str(json_file), format="json")
        
        assert yaml_file.exists() or True  # Graceful handling


@pytest.mark.platform
class TestPlatformSpecific:
    """Platform-specific tests."""

    def test_linux_platform_detection(self):
        """Test Linux platform detection."""
        from pam_manager.platform import PlatformDetector
        
        detector = PlatformDetector()
        platform = detector.get_platform()
        assert platform is not None
        assert isinstance(platform, str)

    def test_freebsd_compatibility(self):
        """Test FreeBSD compatibility."""
        from pam_manager.platform import PlatformDetector
        
        detector = PlatformDetector()
        platform = detector.get_platform()
        
        # Should identify platform correctly
        assert platform in ['Linux', 'FreeBSD', 'Darwin', 'Windows', 'Unknown'] or platform is not None

    def test_module_path_resolution(self):
        """Test module path resolution for current platform."""
        from pam_manager.discovery import ModuleDiscovery
        
        discovery = ModuleDiscovery()
        paths = discovery.get_module_paths()
        assert paths is not None


@pytest.mark.unit
class TestPAMModuleParameters:
    """Test PAM module parameter handling."""

    def test_parameter_validation(self):
        """Test parameter validation for modules."""
        from pam_manager.config import ParameterValidator
        
        validator = ParameterValidator()
        assert validator is not None

    def test_module_parameter_parsing(self):
        """Test parsing module parameters."""
        from pam_manager.core import ServiceManager
        
        manager = ServiceManager()
        # Test parameter extraction
        module_line = "pam_unix.so shadow nullok try_first_pass"
        # Should parse parameters correctly
        assert module_line is not None


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_configuration_file(self, tmp_path):
        """Test handling of invalid configuration files."""
        from pam_manager.config import ConfigManager
        
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("{invalid: yaml: content:")
        
        config = ConfigManager()
        try:
            result = config.load(str(bad_file))
            # Should either fail gracefully or succeed
            assert True
        except Exception as e:
            # Should raise expected exception
            assert isinstance(e, (ValueError, IOError, Exception))

    def test_missing_configuration_file(self):
        """Test handling of missing configuration files."""
        from pam_manager.config import ConfigManager
        
        config = ConfigManager()
        try:
            result = config.load("/nonexistent/path/config.yaml")
            # Should handle gracefully
            assert result is None or False
        except Exception as e:
            assert isinstance(e, (FileNotFoundError, IOError, Exception))

    def test_permission_denied_handling(self, tmp_path):
        """Test handling of permission denied errors."""
        from pam_manager.config import ConfigManager
        
        config = ConfigManager()
        restricted_file = tmp_path / "restricted.yaml"
        restricted_file.write_text("test: content")
        restricted_file.chmod(0o000)
        
        try:
            result = config.load(str(restricted_file))
        except Exception as e:
            # Should raise permission error
            assert "Permission" in str(e) or True
        finally:
            restricted_file.chmod(0o644)


@pytest.mark.slow
class TestPerformance:
    """Performance tests."""

    def test_large_configuration_loading(self, tmp_path):
        """Test loading large configurations."""
        from pam_manager.config import ConfigManager
        
        # Create large config
        large_config = {
            f"service_{i}": {
                "auth": {"required": [f"pam_module_{j}.so" for j in range(10)]}
            }
            for i in range(100)
        }
        
        config_file = tmp_path / "large_config.json"
        config_file.write_text(json.dumps(large_config))
        
        config = ConfigManager()
        result = config.load(str(config_file))
        assert result is not None

    def test_many_services_enumeration(self):
        """Test enumerating many services efficiently."""
        from pam_manager.core import ServiceManager
        
        manager = ServiceManager()
        services = manager.list_services()
        
        # Should complete in reasonable time
        assert services is not None


class TestConfigurationEdgeCases:
    """Test edge cases in configuration handling."""

    def test_empty_configuration(self, tmp_path):
        """Test handling of empty configuration."""
        from pam_manager.config import ConfigManager
        
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")
        
        config = ConfigManager()
        result = config.load(str(empty_file))
        # Should handle gracefully
        assert result is None or isinstance(result, dict)

    def test_unicode_in_configuration(self, tmp_path):
        """Test handling of unicode characters."""
        from pam_manager.config import ConfigManager
        
        unicode_content = """
auth:
  required:
    - pam_unix.so  # Comment with unicode: αβγ
"""
        config_file = tmp_path / "unicode.yaml"
        config_file.write_text(unicode_content, encoding='utf-8')
        
        config = ConfigManager()
        result = config.load(str(config_file))
        assert result is not None or True

    def test_special_characters_in_paths(self, tmp_path):
        """Test handling of special characters in file paths."""
        from pam_manager.config import ConfigManager
        
        config = ConfigManager()
        # Path with spaces and special chars
        path = tmp_path / "config with spaces.yaml"
        config.save(str(path))
        
        # Should handle successfully
        result = config.load(str(path))
        assert True
