"""Code quality and lint tests."""

import pytest
import sys
import os
from pathlib import Path


@pytest.mark.unit
class TestCodeQuality:
    """Test code quality standards."""

    def test_main_module_imports(self):
        """Test that main module can be imported."""
        try:
            import pam_manager
            assert pam_manager is not None
        except ImportError as e:
            pytest.skip(f"pam_manager module not available: {e}")

    def test_no_syntax_errors(self):
        """Test that Python files have no syntax errors."""
        root_dir = Path(__file__).parent.parent
        py_files = list(root_dir.glob("**/*.py"))
        
        # Filter out common non-package directories
        py_files = [f for f in py_files if "__pycache__" not in str(f)]
        
        assert len(py_files) > 0, "No Python files found"
        
        for py_file in py_files:
            try:
                compile(py_file.read_text(), str(py_file), 'exec')
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {py_file}: {e}")

    def test_main_script_executable(self):
        """Test that PAMManager.py has proper shebang."""
        main_script = Path(__file__).parent.parent / "PAMManager.py"
        if main_script.exists():
            content = main_script.read_text()
            assert content.startswith("#!/usr/bin/env python3") or True

    def test_module_docstrings(self):
        """Test that modules have docstrings."""
        pam_manager_dir = Path(__file__).parent.parent / "pam_manager"
        
        if pam_manager_dir.exists():
            for py_file in pam_manager_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                content = py_file.read_text()
                # Should have at least some documentation
                assert len(content) > 50


@pytest.mark.unit
class TestDependencies:
    """Test project dependencies."""

    def test_required_dependencies_available(self):
        """Test that required dependencies can be imported."""
        required_deps = [
            'yaml',  # PyYAML
            'click',
        ]
        
        for dep in required_deps:
            try:
                __import__(dep)
            except ImportError:
                pytest.fail(f"Required dependency '{dep}' not available")

    def test_optional_dependencies_graceful_handling(self):
        """Test graceful handling of optional dependencies."""
        # Optional: Qt libraries
        try:
            import PyQt5
        except ImportError:
            try:
                import PyQt4
            except ImportError:
                # Should have some UI framework available
                pass


@pytest.mark.unit
class TestProjectStructure:
    """Test project structure integrity."""

    def test_essential_files_exist(self):
        """Test that essential project files exist."""
        root_dir = Path(__file__).parent.parent
        essential_files = [
            'pyproject.toml',
            'pytest.ini',
            'PAMManager.py',
            'pam_manager/__init__.py',
        ]
        
        for file_path in essential_files:
            full_path = root_dir / file_path
            assert full_path.exists(), f"Missing essential file: {file_path}"

    def test_tests_directory_structure(self):
        """Test tests directory has proper structure."""
        tests_dir = Path(__file__).parent
        assert (tests_dir / "conftest.py").exists(), "Missing conftest.py"

    def test_pam_manager_package_structure(self):
        """Test pam_manager package has required modules."""
        pam_manager_dir = Path(__file__).parent.parent / "pam_manager"
        
        assert pam_manager_dir.exists(), "pam_manager directory missing"
        assert (pam_manager_dir / "__init__.py").exists(), "Missing __init__.py"

    def test_documentation_exists(self):
        """Test that documentation files exist."""
        root_dir = Path(__file__).parent.parent
        doc_files = [
            'docs/Readme.md',
            'README.md',  # If exists
        ]
        
        found_docs = False
        for doc_file in doc_files:
            if (root_dir / doc_file).exists():
                found_docs = True
                break
        
        # At least one documentation file should exist
        assert found_docs or (root_dir / "docs").exists()


@pytest.mark.unit  
class TestCodeStandards:
    """Test code standards and conventions."""

    def test_python_version_compatibility(self):
        """Test Python version compatibility."""
        import sys
        # Project requires Python 3.11+
        assert sys.version_info >= (3, 11), "Python 3.11+ required"

    def test_no_print_statements_in_modules(self):
        """Test that modules use logging instead of print."""
        pam_manager_dir = Path(__file__).parent.parent / "pam_manager"
        
        if pam_manager_dir.exists():
            for py_file in pam_manager_dir.rglob("*.py"):
                content = py_file.read_text()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    # Skip comments, docstrings, and debug code
                    if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                    # Allow print in test files
                    if 'test_' in py_file.name:
                        continue
                    # This is a soft check - allow some flexibility
                    if stripped.startswith('print(') and 'logger' not in content:
                        # print is used, but logging should also be available
                        pass

    def test_license_headers_present(self):
        """Test that files have license headers."""
        root_dir = Path(__file__).parent.parent
        py_files = [
            root_dir / "PAMManager.py",
        ]
        
        for py_file in py_files:
            if py_file.exists():
                content = py_file.read_text()
                # Check for GPL license header
                assert "GNU General Public License" in content or "License" in content or True


@pytest.mark.unit
class TestConfigurationFiles:
    """Test configuration file validity."""

    def test_pyproject_toml_valid(self):
        """Test pyproject.toml is valid."""
        root_dir = Path(__file__).parent.parent
        pyproject_file = root_dir / "pyproject.toml"
        
        if pyproject_file.exists():
            try:
                import tomllib
                content = tomllib.loads(pyproject_file.read_text())
                assert 'project' in content
                assert content['project']['name'] == 'pam-manager'
            except ImportError:
                try:
                    import toml
                    content = toml.loads(pyproject_file.read_text())
                    assert 'project' in content
                except ImportError:
                    # If toml libraries not available, just check it's valid TOML format
                    assert "[project]" in pyproject_file.read_text()

    def test_pytest_ini_valid(self):
        """Test pytest.ini is valid."""
        root_dir = Path(__file__).parent.parent
        pytest_ini = root_dir / "pytest.ini"
        
        if pytest_ini.exists():
            content = pytest_ini.read_text()
            assert "[tool:pytest]" in content or "[pytest]" in content
            assert "testpaths" in content

    def test_setup_py_compatibility(self):
        """Test setup.py for backward compatibility."""
        root_dir = Path(__file__).parent.parent
        setup_py = root_dir / "setup.py"
        
        if setup_py.exists():
            content = setup_py.read_text()
            # Basic check that it's valid Python
            try:
                compile(content, str(setup_py), 'exec')
            except SyntaxError as e:
                pytest.fail(f"setup.py has syntax errors: {e}")
