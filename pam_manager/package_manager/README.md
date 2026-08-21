"""
PHASE 3 - PACKAGE MANAGEMENT DOCUMENTATION
===========================================

This module provides platform-independent package manager abstraction for
installing PAM modules across different Linux distributions and FreeBSD.

PROJECT STRUCTURE:
==================

pam_manager/package_manager/
├── __init__.py                 # Module exports
├── base.py                     # Abstract PackageManager interface
├── apt.py                      # APT package manager (Debian/Ubuntu)
├── dnf.py                      # DNF package manager (Fedora/RHEL 8+)
├── yum.py                      # YUM package manager (RHEL 7 and older)
├── pkg.py                      # PKG package manager (FreeBSD)
└── factory.py                  # PackageManagerFactory

tests/
└── test_package_managers.py    # 29 unit tests for all components

ABSTRACT INTERFACE - PackageManager:
====================================

class PackageManager(ABC):
    def get_installed_packages() -> List[str]
    def get_package_info(name: str) -> Optional[PackageInfo]
    def search_package(query: str) -> List[str]
    def search_available(name: str) -> List[PackageInfo]
    def is_installed(name: str) -> bool
    def install_package(name: str, dry_run: bool) -> InstallationResult
    def install_packages(names: List[str], dry_run: bool) -> List[InstallationResult]
    def get_package_version(name: str) -> Optional[str]
    def update_package_cache() -> bool

DATACLASSES:
============

1. PackageInfo (frozen - immutable)
   - name: str                    # Package name
   - version: Optional[str]       # Version string
   - description: Optional[str]   # Human-readable description
   - installed: bool              # True if installed on system
   - available_in_repo: bool      # True if available for installation

2. InstallationResult (frozen - immutable)
   - success: bool                # True if operation succeeded
   - package_name: str            # Package name
   - version: Optional[str]       # Installed version
   - error_message: Optional[str] # Error details if failed
   - already_installed: bool      # True if was already installed

PLATFORM MANAGERS:
==================

APT (pam_manager/package_manager/apt.py)
├─ Platform: Debian, Ubuntu, Linux Mint, Kali Linux
├─ Commands: dpkg, apt-cache, apt-get
├─ Timeouts: 300s install, 60s update, 10s query
├─ Version Source: dpkg -l format parsing
└─ Cache: Installed packages list cached after first query

DNF (pam_manager/package_manager/dnf.py)
├─ Platform: Fedora 30+, RedHat 8+, CentOS Stream, Rocky, AlmaLinux
├─ Commands: dnf (all operations)
├─ Special: Return codes 0 and 100 treated as success
├─ Timeouts: 300s install, 120s update, 30s query
└─ Cache: Installed packages list cached after first query

YUM (pam_manager/package_manager/yum.py)
├─ Platform: RHEL 7 and older, older CentOS
├─ Commands: rpm (queries), yum (install/search)
├─ Format: name-version-release.arch parsing
├─ Timeouts: 300s install, 120s update, 30s query
└─ Cache: Installed packages list cached after first query

PKG (pam_manager/package_manager/pkg.py)
├─ Platform: FreeBSD 12+
├─ Commands: pkg (all operations)
├─ Format: name-version (no .arch suffix like Linux)
├─ Timeouts: 300s install, 120s update, 10s query
└─ Cache: Installed packages list cached after first query

FACTORY - PackageManagerFactory:
================================

Provides two factory methods:

1. create(package_manager: PackageManager) -> PackageManager instance
   Usage: mgr = PackageManagerFactory.create(PackageManager.APT)
   Returns: APTPackageManager() instance
   Raises: ValueError if manager type is UNKNOWN or unsupported

2. create_for_platform(platform: Platform) -> PackageManager instance
   Usage: mgr = PackageManagerFactory.create_for_platform(Platform.FEDORA)
   Process:
     a) Call platform_detector.detect_package_manager(platform)
     b) Get PackageManager enum value (APT/DNF/YUM/PKG)
     c) Call create() with that value
   Returns: Appropriate manager instance for platform

USAGE EXAMPLES:
===============

Example 1: Get installed packages
──────────────────────────────────
from pam_manager.package_manager import PackageManagerFactory, PackageManager
from pam_manager.core import Platform

# Create manager for specific platform
mgr = PackageManagerFactory.create_for_platform(Platform.UBUNTU)

# Get installed packages
packages = mgr.get_installed_packages()
print(f"Installed: {len(packages)} packages")

# Check if specific package installed
if mgr.is_installed("libpam-pwquality"):
    print("PAM password quality module is installed")


Example 2: Search and install package
──────────────────────────────────────
# Search for packages matching query
results = mgr.search_package("pam")
print(f"Found {len(results)} packages matching 'pam'")

# Install single package (dry-run)
result = mgr.install_package("libpam-google-authenticator", dry_run=True)
print(f"Installation would {'succeed' if result.success else 'fail'}")

# Actually install
result = mgr.install_package("libpam-google-authenticator", dry_run=False)
if result.success:
    print(f"Installed version {result.version}")
elif result.already_installed:
    print("Package was already installed")
else:
    print(f"Installation failed: {result.error_message}")


Example 3: Batch install multiple packages
───────────────────────────────────────────
packages_to_install = [
    "libpam-unix",
    "libpam-pwquality",
    "libpam-faillock",
]

# Dry-run to validate
results = mgr.install_packages(packages_to_install, dry_run=True)
if all(r.success for r in results):
    print("All packages would install successfully")
    
    # Real installation
    results = mgr.install_packages(packages_to_install, dry_run=False)
    for result in results:
        if result.success:
            print(f"✓ {result.package_name} ({result.version})")
        else:
            print(f"✗ {result.package_name}: {result.error_message}")


Example 4: Integration with module registry
────────────────────────────────────────────
from pam_manager.modules import ModuleRegistry

# Get required packages for specific modules
registry = ModuleRegistry()
modules = ["pam_unix", "pam_pwquality"]
platform = Platform.FEDORA

# Get package names from registry
pkg_mgr = PackageManagerFactory.create_for_platform(platform)
package_names = registry.get_package_names(modules, platform)

# Install all required packages
results = pkg_mgr.install_packages(package_names, dry_run=True)
print(f"Would install {len([r for r in results if r.success])} packages")


SUBPROCESS INTEGRATION DETAILS:
===============================

All package managers follow consistent subprocess pattern:

1. Command Execution:
   - subprocess.run([...], capture_output=True, text=True, check=False, timeout=X)
   - capture_output=True: Capture both stdout and stderr
   - text=True: Return strings instead of bytes
   - check=False: Don't raise CalledProcessError; handle return codes manually
   - timeout=X: Timeout after X seconds (prevents hanging)

2. Timeouts:
   - Installation: 300 seconds (5 minutes)
   - Cache update: 120 seconds (2 minutes) for dnf/yum, 60s for apt
   - Queries (search, info): 10-30 seconds depending on operation
   - No subprocess call without timeout

3. Error Handling:
   - All exceptions caught and converted to InstallationResult
   - subprocess.TimeoutExpired → "Installation timed out" error
   - FileNotFoundError → Package manager not found → [empty list]
   - CalledProcessError → Error message preserved in result

4. Caching:
   - get_installed_packages() cached in self._installed_cache
   - Cache invalidated by update_package_cache()
   - Cache survives individual queries (is_installed, get_version)
   - Each manager instance has its own cache

DRY-RUN MODE:
=============

When dry_run=True:
- No actual subprocess calls to install packages
- No sudo elevation required
- Returns success with version="(simulated)"
- Useful for validation and testing

Workflow:
1. User/test calls install_package(..., dry_run=True)
2. Manager checks if package already installed (may use subprocess)
3. If not installed and dry_run=True: returns success immediately
4. If not installed and dry_run=False: calls subprocess with sudo


TESTING STRATEGY:
=================

All tests use subprocess mocking (unittest.mock.patch):
- No real package managers called during tests
- No network access required
- Tests run in milliseconds
- Predictable and reproducible

Test Structure:
1. Mock subprocess.run() to return controlled output
2. Create package manager instance
3. Call method and verify result
4. Assert correct subprocess call parameters
5. Verify caching behavior

Example Test Pattern:
────────────────────
@patch("subprocess.run")
def test_apt_get_installed_packages(mock_run):
    mock_run.return_value = MagicMock(
        stdout="ii  libpam-modules  1.4.0  amd64  ...\n",
        returncode=0,
    )
    
    apt = APTPackageManager()
    packages = apt.get_installed_packages()
    
    assert "libpam-modules" in packages
    mock_run.assert_called_with(
        ["dpkg", "-l"],
        capture_output=True,
        text=True,
        check=False,
    )


THREAD SAFETY:
==============

✓ All dataclasses are frozen (immutable)
✓ Each manager instance independent (no shared state)
✓ Cache is write-once (set after first query, invalidated on update)
✓ Subprocess calls are atomic
✓ InstallationResult objects immutable after creation

Safe for concurrent use in multi-threaded applications.


FUTURE ENHANCEMENTS:
====================

1. Async Package Installation
   - Support for concurrent package installations
   - Use asyncio + concurrent.futures

2. Advanced Caching
   - Cache package metadata (version, description)
   - Persistent cache between runs
   - Cache expiration policies

3. Dependency Resolution
   - Resolve package dependencies automatically
   - Download dependency tree before installation

4. Rollback Support
   - Track installed packages
   - Uninstall support for rollback
   - Transaction-like semantics

5. Progress Reporting
   - Callbacks for long-running operations
   - Installation progress percentage

6. Atomic Batch Operations
   - All-or-nothing semantics for batch installations
   - Automatic rollback on failure


DEBUGGING:
==========

Enable subprocess logging:
──────────────────────────
import subprocess
subprocess.run = lambda *args, **kwargs: \
    (print(f"Running: {args[0]}"), subprocess.run(*args, **kwargs))[1]

Check installed packages:
─────────────────────────
mgr = PackageManagerFactory.create_for_platform(Platform.UBUNTU)
packages = mgr.get_installed_packages()
print(f"Installed: {len(packages)} packages")
print("Sample packages:", packages[:10])

Verify manager creation:
────────────────────────
mgr = PackageManagerFactory.create(PackageManager.APT)
print(f"Manager: {type(mgr).__name__}")
print(f"Package manager instance created successfully")


INTEGRATION WITH PHASES:
========================

Phase 2 Module Registry ← Phase 3 Package Managers → Phase 4 Discovery
                                ↓
                         Phase 5 Policy Engine
                                ↓
                         Phase 6+ CLI/Renderer

Flow:
1. Registry provides module → package name mappings (Phase 2)
2. Package manager installs required packages (Phase 3)
3. Discovery scans installed packages against registry (Phase 4)
4. Policy engine validates configurations (Phase 5)
5. CLI wizard uses all components (Phase 6)
"""
