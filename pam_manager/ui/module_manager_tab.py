"""Module Manager GUI Widget - PyQt5/PyQt4 - Phase 5."""

from typing import List, Optional
import logging

# Try PyQt5 first, fallback to PyQt4
try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QLabel, QComboBox, QGroupBox, QCheckBox, QMessageBox,
        QHeaderView, QTextEdit
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QColor, QBrush
    QT_VERSION = 5
except ImportError:
    from PyQt4.QtGui import (
        QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QLabel, QComboBox, QGroupBox, QCheckBox, QMessageBox,
        QColor, QBrush, QTextEdit
    )
    from PyQt4.QtCore import Qt, pyqtSignal
    QT_VERSION = 4

from pam_manager.ui.module_manager import ModuleManager, ModuleInfo, ModuleStatus


logger = logging.getLogger(__name__)


class ModuleManagerTab(QWidget):
    """Tab for PAM module management."""
    
    modules_changed = pyqtSignal(list)
    installation_requested = pyqtSignal(str, str)  # module name, platform
    
    def __init__(self, parent=None):
        """
        Initialize module manager tab.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.manager = ModuleManager()
        self.current_platform = None
        
        self.setWindowTitle("Module Manager")
        self.setGeometry(100, 100, 1000, 700)
        
        self._create_ui()
        self._populate_demo_modules()
    
    def _create_ui(self):
        """Create user interface."""
        main_layout = QVBoxLayout()
        
        # Platform selector
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("Platform:"))
        
        self.platform_combo = QComboBox()
        self.platform_combo.addItems([
            "UBUNTU", "DEBIAN", "FEDORA", "RHEL", "ALMA",
            "ROCKY", "CENTOS", "KALI", "LINUX_MINT",
            "FREEBSD", "OPENBSD", "NETBSD", "MACOS"
        ])
        self.platform_combo.currentTextChanged.connect(self._on_platform_changed)
        platform_layout.addWidget(self.platform_combo)
        
        platform_layout.addStretch()
        main_layout.addLayout(platform_layout)
        
        # Modules table
        table_group = QGroupBox("Installed Modules")
        table_layout = QVBoxLayout()
        
        self.modules_table = QTableWidget()
        self.modules_table.setColumnCount(6)
        self.modules_table.setHorizontalHeaderLabels(
            ["Name", "Category", "Version", "Status", "Enabled", "Actions"]
        )
        
        if QT_VERSION == 5:
            header = self.modules_table.horizontalHeader()
            header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        table_layout.addWidget(self.modules_table)
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group)
        
        # Available for installation
        available_group = QGroupBox("Available for Installation")
        available_layout = QVBoxLayout()
        
        self.available_table = QTableWidget()
        self.available_table.setColumnCount(3)
        self.available_table.setHorizontalHeaderLabels(
            ["Name", "Version", "Actions"]
        )
        self.available_table.setMaximumHeight(150)
        
        available_layout.addWidget(self.available_table)
        available_group.setLayout(available_layout)
        main_layout.addWidget(available_group)
        
        # Module details
        details_group = QGroupBox("Module Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(120)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        main_layout.addWidget(details_group)
        
        # Report
        report_layout = QHBoxLayout()
        report_layout.addWidget(QLabel("Module Report:"))
        main_layout.addLayout(report_layout)
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        main_layout.addWidget(self.report_text)
        
        self.setLayout(main_layout)
    
    def _populate_demo_modules(self):
        """Populate with demo modules."""
        # Common PAM modules
        modules_data = [
            ("pam_unix", "authentication", "1.3.1", ModuleStatus.INSTALLED, True),
            ("pam_ldap", "authentication", "1.2.5", ModuleStatus.INSTALLED, False),
            ("pam_krb5", "authentication", "1.4.0", ModuleStatus.INSTALLED, False),
            ("pam_pwquality", "password", "1.4.4", ModuleStatus.INSTALLED, True),
            ("pam_cracklib", "password", "1.2.11", ModuleStatus.NOT_INSTALLED, False),
            ("pam_faillock", "account", "1.3.1", ModuleStatus.INSTALLED, True),
            ("pam_tally2", "account", "1.2.1", ModuleStatus.NOT_INSTALLED, False),
            ("pam_env", "session", "1.3.1", ModuleStatus.INSTALLED, True),
            ("pam_motd", "session", "1.3.1", ModuleStatus.INSTALLED, False),
            ("pam_limits", "session", "1.3.1", ModuleStatus.INSTALLED, True),
            ("pam_lastlog", "session", "1.3.1", ModuleStatus.INSTALLED, True),
        ]
        
        for name, category, version, status, enabled in modules_data:
            module = ModuleInfo(
                name=name,
                category=category,
                description=f"{name} module",
                status=status,
                installed_version=version if status != ModuleStatus.NOT_INSTALLED else None,
                available_version=version,
                enabled=enabled
            )
            self.manager.register_module(module)
        
        self._refresh_display()
    
    def _on_platform_changed(self, platform: str):
        """Handle platform change."""
        self.current_platform = platform
        logger.info(f"Platform changed to: {platform}")
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh display."""
        self._update_modules_table()
        self._update_available_table()
        self._update_report()
    
    def _update_modules_table(self):
        """Update installed modules table."""
        installed = self.manager.get_installed_modules()
        self.modules_table.setRowCount(len(installed))
        
        for row, module in enumerate(installed):
            # Name
            name_item = QTableWidgetItem(module.name)
            self.modules_table.setItem(row, 0, name_item)
            
            # Category
            cat_item = QTableWidgetItem(module.category)
            self.modules_table.setItem(row, 1, cat_item)
            
            # Version
            ver_item = QTableWidgetItem(module.installed_version or "?")
            self.modules_table.setItem(row, 2, ver_item)
            
            # Status
            status_text = "✓ OK" if module.status == ModuleStatus.INSTALLED else "✗ Error"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(
                QBrush(QColor(0, 128, 0) if module.status == ModuleStatus.INSTALLED else QColor(255, 0, 0))
            )
            self.modules_table.setItem(row, 3, status_item)
            
            # Enable/Disable checkbox
            enable_item = QTableWidgetItem()
            enable_item.setCheckState(Qt.Checked if module.enabled else Qt.Unchecked)
            self.modules_table.setItem(row, 4, enable_item)
            
            # Actions button
            action_button = QPushButton("Details")
            action_button.clicked.connect(
                lambda checked, m=module: self._show_module_details(m)
            )
            self.modules_table.setCellWidget(row, 5, action_button)
    
    def _update_available_table(self):
        """Update available modules table."""
        available = self.manager.get_available_modules()
        self.available_table.setRowCount(len(available))
        
        for row, module in enumerate(available):
            # Name
            name_item = QTableWidgetItem(module.name)
            self.available_table.setItem(row, 0, name_item)
            
            # Version
            ver_item = QTableWidgetItem(module.available_version or "?")
            self.available_table.setItem(row, 1, ver_item)
            
            # Install button
            install_button = QPushButton("Install")
            install_button.clicked.connect(
                lambda checked, m=module: self._install_module(m)
            )
            self.available_table.setCellWidget(row, 2, install_button)
    
    def _show_module_details(self, module: ModuleInfo):
        """Show module details."""
        details = [
            f"Module: {module.name}",
            f"Category: {module.category}",
            f"Description: {module.description}",
            f"Status: {module.status.value}",
            f"Version: {module.installed_version or 'N/A'}",
            f"Security Level: {module.security_level}",
        ]
        
        if module.conflicts:
            details.append(f"Conflicts with: {', '.join(module.conflicts)}")
        
        if module.alternatives:
            details.append(f"Alternatives: {', '.join(module.alternatives)}")
        
        self.details_text.setText("\n".join(details))
    
    def _install_module(self, module: ModuleInfo):
        """Install module."""
        if not self.current_platform:
            QMessageBox.warning(self, "Error", "Please select a platform first")
            return
        
        reply = QMessageBox.question(
            self,
            "Install Module",
            f"Install {module.name} on {self.current_platform}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.installation_requested.emit(module.name, self.current_platform)
            QMessageBox.information(
                self,
                "Installation",
                f"Installation of {module.name} has been requested.\n"
                f"Check the system for installation status."
            )
    
    def _update_report(self):
        """Update module report."""
        report = self.manager.generate_module_report()
        self.report_text.setText(report)
    
    def get_enabled_modules(self) -> List[str]:
        """
        Get enabled modules.
        
        Returns:
            List[str]: List of enabled module names
        """
        return self.manager.get_enabled_modules()
    
    def set_enabled_modules(self, modules: List[str]) -> bool:
        """
        Set enabled modules.
        
        Args:
            modules: List of module names to enable
            
        Returns:
            bool: True if successful
        """
        # First disable all
        for name in self.manager.get_enabled_modules():
            self.manager.disable_module(name)
        
        # Then enable specified
        for name in modules:
            success, msg = self.manager.enable_module(name)
            if not success:
                logger.warning(f"Could not enable {name}: {msg}")
        
        self.modules_changed.emit(self.manager.get_enabled_modules())
        self._refresh_display()
        return True
