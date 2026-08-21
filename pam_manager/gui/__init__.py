"""GUI integration layer for Phase 4 widgets - Phase 5."""

from typing import Optional, Callable, Dict, Any, List
import logging

# Try PyQt5 first, fallback to PyQt4
try:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
    from PyQt5.QtCore import Qt, pyqtSignal
    QT_VERSION = 5
except ImportError:
    from PyQt4.QtGui import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
    from PyQt4.QtCore import Qt, pyqtSignal
    QT_VERSION = 4

from pam_manager.ui.wizard_widget import ConfigurationWizardWidget
from pam_manager.ui.validation_panel_widget import ValidationPanelWidget
from pam_manager.ui.backup_manager_widget import BackupManagerWidget
from pam_manager.ui.dependency_graph_widget import DependencyGraphWidget
from pam_manager.ui.module_manager_tab import ModuleManagerTab


logger = logging.getLogger(__name__)


class ConfigurationWizardTab(QWidget):
    """Tab wrapper for ConfigurationWizard."""
    
    configuration_generated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """
        Initialize wizard tab.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.wizard = ConfigurationWizardWidget()
        
        # Connect signals
        self.wizard.wizard_completed.connect(self._on_wizard_completed)
        self.wizard.wizard_cancelled.connect(self._on_wizard_cancelled)
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.wizard)
        self.setLayout(layout)
        
        logger.info("ConfigurationWizardTab initialized")
    
    def _on_wizard_completed(self, config: Dict[str, Any]):
        """Handle wizard completion."""
        logger.info(f"Configuration generated: {config}")
        self.configuration_generated.emit(config)
    
    def _on_wizard_cancelled(self):
        """Handle wizard cancellation."""
        logger.info("Configuration wizard cancelled")


class ValidationTab(QWidget):
    """Tab wrapper for ValidationPanel."""
    
    validation_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Initialize validation tab.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.panel = ValidationPanelWidget()
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.panel)
        self.setLayout(layout)
        
        logger.info("ValidationTab initialized")
    
    def add_validation_result(self, level, stage, message, **kwargs):
        """
        Add validation result.
        
        Args:
            level: Validation level
            stage: Validation stage
            message: Message text
            **kwargs: Additional parameters
        """
        self.panel.add_validation_result(level, stage, message, **kwargs)
        self.validation_updated.emit()
    
    def get_panel(self):
        """
        Get validation panel.
        
        Returns:
            ValidationPanelWidget: The panel widget
        """
        return self.panel


class BackupTab(QWidget):
    """Tab wrapper for BackupManager."""
    
    backup_restored = pyqtSignal(str)
    backup_created = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Initialize backup tab.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.manager_widget = BackupManagerWidget()
        
        # Connect signals
        self.manager_widget.backup_restored.connect(self._on_backup_restored)
        self.manager_widget.backup_created.connect(self._on_backup_created)
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.manager_widget)
        self.setLayout(layout)
        
        logger.info("BackupTab initialized")
    
    def _on_backup_restored(self, backup_id: str):
        """Handle backup restoration."""
        logger.info(f"Backup restored: {backup_id}")
        self.backup_restored.emit(backup_id)
    
    def _on_backup_created(self, backup_id: str):
        """Handle backup creation."""
        logger.info(f"Backup created: {backup_id}")
        self.backup_created.emit(backup_id)
    
    def get_manager(self):
        """
        Get backup manager.
        
        Returns:
            BackupManagerWidget: The manager widget
        """
        return self.manager_widget


class DependencyTab(QWidget):
    """Tab wrapper for DependencyGraph."""
    
    configuration_validated = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        """
        Initialize dependency tab.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.graph_widget = DependencyGraphWidget()
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.graph_widget)
        self.setLayout(layout)
        
        logger.info("DependencyTab initialized")
    
    def validate_configuration(self, modules):
        """
        Validate configuration.
        
        Args:
            modules: List of module names
            
        Returns:
            bool: True if valid
        """
        is_valid = self.graph_widget.validate_configuration(modules)
        self.configuration_validated.emit(is_valid)
        return is_valid
    
    def get_visualizer(self):
        """
        Get dependency visualizer.
        
        Returns:
            DependencyVisualizer: The visualizer instance
        """
        return self.graph_widget.visualizer


class ModulesTab(QWidget):
    """Tab wrapper for ModuleManager."""
    
    modules_changed = pyqtSignal(list)
    installation_requested = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        """
        Initialize modules tab.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.manager_tab = ModuleManagerTab()
        
        # Connect signals
        self.manager_tab.modules_changed.connect(self._on_modules_changed)
        self.manager_tab.installation_requested.connect(self._on_installation_requested)
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.manager_tab)
        self.setLayout(layout)
        
        logger.info("ModulesTab initialized")
    
    def _on_modules_changed(self, modules: List[str]):
        """Handle module changes."""
        logger.info(f"Modules changed: {modules}")
        self.modules_changed.emit(modules)
    
    def _on_installation_requested(self, module_name: str, platform: str):
        """Handle installation request."""
        logger.info(f"Installation requested: {module_name} on {platform}")
        self.installation_requested.emit(module_name, platform)
    
    def get_manager_tab(self) -> ModuleManagerTab:
        """
        Get module manager tab.
        
        Returns:
            ModuleManagerTab: The tab instance
        """
        return self.manager_tab


class PAMManagerGUIExtension:
    """Extension class for integrating Phase 4 widgets into PAMManagerGUI."""
    
    def __init__(self, pam_gui):
        """
        Initialize extension.
        
        Args:
            pam_gui: PAMManagerGUI instance
        """
        self.pam_gui = pam_gui
        self.wizard_tab = None
        self.validation_tab = None
        self.backup_tab = None
        self.dependency_tab = None
        self.modules_tab = None
        
        logger.info("PAMManagerGUIExtension initialized")
    
    def add_phase4_tabs(self) -> bool:
        """
        Add Phase 4 tabs to PAMManagerGUI.
        
        Returns:
            bool: True if successful
        """
        try:
            # Create tab wrappers
            self.wizard_tab = ConfigurationWizardTab(self.pam_gui)
            self.validation_tab = ValidationTab(self.pam_gui)
            self.backup_tab = BackupTab(self.pam_gui)
            self.dependency_tab = DependencyTab(self.pam_gui)
            self.modules_tab = ModulesTab(self.pam_gui)
            
            # Add to tabs (before "About" tab)
            # Get current tab count to insert before last tab
            tab_count = self.pam_gui.tabs.count()
            last_tab_index = tab_count - 1  # Index of "About" tab
            
            self.pam_gui.tabs.insertTab(last_tab_index, self.wizard_tab, "Configuration Wizard")
            self.pam_gui.tabs.insertTab(last_tab_index + 1, self.validation_tab, "Validation")
            self.pam_gui.tabs.insertTab(last_tab_index + 2, self.backup_tab, "Backup")
            self.pam_gui.tabs.insertTab(last_tab_index + 3, self.dependency_tab, "Dependencies")
            self.pam_gui.tabs.insertTab(last_tab_index + 4, self.modules_tab, "Module Manager")
            
            # Connect signals
            self._connect_signals()
            
            logger.info("Phase 4 tabs added successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error adding Phase 4 tabs: {e}")
            return False
    
    def _connect_signals(self):
        """Connect signals between tabs and GUI."""
        # Wizard → Validation: When config generated, validate it
        self.wizard_tab.configuration_generated.connect(
            self._on_configuration_generated
        )
        
        # Backup → auto-backup on configuration changes
        # This would be connected to configuration change signals
        
        # Dependency graph → validation
        self.dependency_tab.configuration_validated.connect(
            self._on_dependency_validation
        )
    
    def _on_configuration_generated(self, config: Dict[str, Any]):
        """Handle configuration generation from wizard."""
        logger.info("Configuration generated from wizard")
        
        # Auto-validate new configuration
        modules = config.get("modules", [])
        if modules:
            self.dependency_tab.validate_configuration(modules)
    
    def _on_dependency_validation(self, is_valid: bool):
        """Handle dependency validation result."""
        status = "✓ Valid" if is_valid else "✗ Invalid"
        logger.info(f"Dependency validation result: {status}")
    
    def get_wizard_tab(self) -> Optional[ConfigurationWizardTab]:
        """Get wizard tab."""
        return self.wizard_tab
    
    def get_validation_tab(self) -> Optional[ValidationTab]:
        """Get validation tab."""
        return self.validation_tab
    
    def get_backup_tab(self) -> Optional[BackupTab]:
        """Get backup tab."""
        return self.backup_tab
    
    def get_dependency_tab(self) -> Optional[DependencyTab]:
        """Get dependency tab."""
        return self.dependency_tab
    
    def get_modules_tab(self) -> Optional[ModulesTab]:
        """Get modules tab."""
        return self.modules_tab
