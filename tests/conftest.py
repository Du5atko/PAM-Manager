"""Tests conftest for pytest configuration."""

import pytest
import sys
import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "platform: mark test as platform-specific"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security-related"
    )
    
    # Setup logging for tests
    logging.basicConfig(
        level=logging.DEBUG if config.getoption('-v') else logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_file(temp_dir):
    """Provide a temporary YAML config file."""
    config_file = temp_dir / "test_config.yaml"
    config_file.write_text("""
auth:
  required:
    - pam_unix.so
account:
  required:
    - pam_permit.so
session:
  required:
    - pam_permit.so
""")
    return config_file


@pytest.fixture
def temp_json_config(temp_dir):
    """Provide a temporary JSON config file."""
    import json
    config_file = temp_dir / "test_config.json"
    config_data = {
        "auth": {
            "required": ["pam_unix.so"]
        },
        "account": {
            "required": ["pam_permit.so"]
        }
    }
    config_file.write_text(json.dumps(config_data, indent=2))
    return config_file


@pytest.fixture
def mock_pam_modules():
    """Provide mock PAM modules."""
    return {
        'pam_unix.so': {
            'name': 'pam_unix',
            'version': '1.0',
            'description': 'Unix authentication module',
            'options': ['shadow', 'nullok', 'try_first_pass']
        },
        'pam_permit.so': {
            'name': 'pam_permit',
            'version': '1.0',
            'description': 'Permit module',
            'options': []
        },
        'pam_deny.so': {
            'name': 'pam_deny',
            'version': '1.0',
            'description': 'Deny module',
            'options': []
        }
    }


@pytest.fixture
def mock_pam_services():
    """Provide mock PAM service definitions."""
    return {
        'login': {
            'auth': [
                'requisite pam_nologin.so',
                'required pam_env.so',
                'required pam_unix.so try_first_pass',
                'optional pam_permit.so'
            ],
            'account': [
                'required pam_unix.so'
            ],
            'password': [
                'optional pam_permit.so'
            ],
            'session': [
                'required pam_limits.so',
                'required pam_unix.so'
            ]
        },
        'sudo': {
            'auth': [
                'auth requisite pam_deny.so',
                'auth required pam_permit.so',
                'auth required pam_unix.so try_first_pass likeauth nullok'
            ],
            'account': [
                'account required pam_unix.so'
            ],
            'session': [
                'session required pam_limits.so'
            ]
        },
        'ssh': {
            'auth': [
                'auth required pam_unix.so nullok try_first_pass'
            ],
            'account': [
                'account required pam_unix.so'
            ],
            'session': [
                'session required pam_unix.so'
            ]
        }
    }


@pytest.fixture
def mock_platform_detector(monkeypatch):
    """Mock platform detection."""
    def mock_get_platform():
        return 'Linux'
    
    return mock_get_platform


@pytest.fixture
def caplog_fixture(caplog):
    """Enhanced caplog fixture with convenience methods."""
    class EnhancedCaplog:
        def __init__(self, caplog_obj):
            self._caplog = caplog_obj
        
        def has_message(self, message, level=None):
            """Check if message exists in logs."""
            for record in self._caplog.records:
                if message in record.message:
                    if level is None or record.levelno == level:
                        return True
            return False
        
        def get_messages(self, level=None):
            """Get all log messages."""
            messages = []
            for record in self._caplog.records:
                if level is None or record.levelno == level:
                    messages.append(record.message)
            return messages
    
    return EnhancedCaplog(caplog)


# Hooks for enhanced output
def pytest_runtest_logreport(report):
    """Enhance test reporting."""
    if report.when == "call":
        if report.outcome == "failed":
            # Could send notifications, update dashboards, etc.
            pass


# Markers for CI/CD
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers."""
    if config.getoption("-m") is None:
        # If no marker specified, mark slow tests for last
        slow_marker = pytest.mark.slow
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(slow_marker)
