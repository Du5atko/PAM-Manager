"""Configuration Wizard Widget - PyQt5/PyQt4 GUI wrapper - Phase 4."""

from typing import Optional, Callable
import logging

# Try PyQt5 first, fallback to PyQt4
try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
        QCheckBox, QPushButton, QProgressBar, QTabWidget, QWidget,
        QTextEdit, QMessageBox, QSpinBox, QGroupBox
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    QT_VERSION = 5
except ImportError:
    from PyQt4.QtGui import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
        QCheckBox, QPushButton, QProgressBar, QTabWidget, QWidget,
        QTextEdit, QMessageBox, QSpinBox, QGroupBox
    )
    from PyQt4.QtCore import Qt, pyqtSignal
    QT_VERSION = 4

from pam_manager.ui.wizard import ConfigurationWizard


logger = logging.getLogger(__name__)


class ConfigurationWizardWidget(QDialog):
    """PyQt widget for configuration wizard."""
    
    # Signals
    wizard_completed = pyqtSignal(dict)
    wizard_cancelled = pyqtSignal()
    step_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """
        Initialize wizard widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.wizard = ConfigurationWizard()
        self.callback = None
        
        self.setWindowTitle("PAM Configuration Wizard")
        self.setGeometry(100, 100, 800, 600)
        
        self._create_ui()
        self._connect_signals()
        self._update_current_step()
    
    def _create_ui(self):
        """Create user interface."""
        main_layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(6)
        main_layout.addWidget(self.progress_bar)
        
        # Step label
        self.step_label = QLabel()
        main_layout.addWidget(self.step_label)
        
        # Content area (stacked widgets simulation)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)
        main_layout.addWidget(self.content_widget)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.back_button = QPushButton("< Back")
        self.back_button.clicked.connect(self.previous_step)
        buttons_layout.addWidget(self.back_button)
        
        buttons_layout.addStretch()
        
        self.next_button = QPushButton("Next >")
        self.next_button.clicked.connect(self.next_step)
        buttons_layout.addWidget(self.next_button)
        
        self.finish_button = QPushButton("Finish")
        self.finish_button.clicked.connect(self.finish)
        self.finish_button.setVisible(False)
        buttons_layout.addWidget(self.finish_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)
        buttons_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
    
    def _connect_signals(self):
        """Connect signals."""
        pass  # Signals already connected in _create_ui
    
    def _update_current_step(self):
        """Update current step display."""
        step_idx = self.wizard.state.current_step
        step_name = self.wizard.STEPS[step_idx]
        
        # Update progress bar
        self.progress_bar.setValue(step_idx + 1)
        
        # Update step label
        self.step_label.setText(
            f"Step {step_idx + 1} of {len(self.wizard.STEPS)}: {step_name.replace('_', ' ').title()}"
        )
        
        # Update button states
        self.back_button.setEnabled(step_idx > 0)
        self.finish_button.setVisible(step_idx == len(self.wizard.STEPS) - 1)
        self.next_button.setVisible(step_idx < len(self.wizard.STEPS) - 1)
        
        # Clear content layout
        while self.content_layout.count():
            self.content_layout.takeAt(0).widget().deleteLater()
        
        # Create step UI
        if step_name == "platform_selection":
            self._create_platform_step()
        elif step_name == "service_selection":
            self._create_service_step()
        elif step_name == "module_selection":
            self._create_module_step()
        elif step_name == "security_level":
            self._create_security_step()
        elif step_name == "backup_verification":
            self._create_backup_step()
        elif step_name == "review_and_apply":
            self._create_review_step()
        
        self.step_changed.emit(step_idx)
    
    def _create_platform_step(self):
        """Create platform selection step."""
        group = QGroupBox("Select Platform")
        layout = QVBoxLayout()
        
        label = QLabel("Choose your platform:")
        layout.addWidget(label)
        
        self.platform_combo = QComboBox()
        platforms = self.wizard.get_platform_selection()
        for platform, description in platforms.items():
            self.platform_combo.addItem(description, platform)
        layout.addWidget(self.platform_combo)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setText(
            "Select the operating system and distribution you are configuring.\n"
            "This wizard will generate platform-specific PAM configurations."
        )
        layout.addWidget(info_text)
        
        group.setLayout(layout)
        self.content_layout.addWidget(group)
    
    def _create_service_step(self):
        """Create service selection step."""
        group = QGroupBox("Select Services")
        layout = QVBoxLayout()
        
        label = QLabel("Choose services to configure:")
        layout.addWidget(label)
        
        self.service_checkboxes = {}
        for service, description in self.wizard.SERVICES.items():
            checkbox = QCheckBox(f"{service}: {description}")
            checkbox.setChecked(service in self.wizard.state.services)
            checkbox.stateChanged.connect(
                lambda checked, s=service: self._on_service_toggled(s, checked)
            )
            self.service_checkboxes[service] = checkbox
            layout.addWidget(checkbox)
        
        layout.addStretch()
        group.setLayout(layout)
        self.content_layout.addWidget(group)
    
    def _create_module_step(self):
        """Create module selection step."""
        group = QGroupBox("Module Selection")
        layout = QVBoxLayout()
        
        label = QLabel("Module selection will be configured based on security level.")
        layout.addWidget(label)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setText(
            "Proceed to the Security Level step to select modules.\n"
            "The wizard will automatically configure appropriate modules based on your security requirements."
        )
        layout.addWidget(info_text)
        
        layout.addStretch()
        group.setLayout(layout)
        self.content_layout.addWidget(group)
    
    def _create_security_step(self):
        """Create security level step."""
        group = QGroupBox("Security Level")
        layout = QVBoxLayout()
        
        label = QLabel("Choose security level:")
        layout.addWidget(label)
        
        self.security_combo = QComboBox()
        for level, description in self.wizard.SECURITY_PRESETS.items():
            self.security_combo.addItem(description, level)
        layout.addWidget(self.security_combo)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setText(
            "• Basic: Simple authentication (pam_unix)\n"
            "• Moderate: Added password quality checks\n"
            "• Hardened: Comprehensive security measures\n"
            "• Paranoid: Maximum security (may affect usability)"
        )
        layout.addWidget(info_text)
        
        layout.addStretch()
        group.setLayout(layout)
        self.content_layout.addWidget(group)
    
    def _create_backup_step(self):
        """Create backup verification step."""
        group = QGroupBox("Backup Verification")
        layout = QVBoxLayout()
        
        label = QLabel("Backup Settings:")
        layout.addWidget(label)
        
        self.backup_checkbox = QCheckBox("Create backup before applying configuration")
        self.backup_checkbox.setChecked(self.wizard.state.backup_enabled)
        layout.addWidget(self.backup_checkbox)
        
        self.auto_restart_checkbox = QCheckBox("Automatically restart PAM services")
        self.auto_restart_checkbox.setChecked(self.wizard.state.auto_restart)
        layout.addWidget(self.auto_restart_checkbox)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setText(
            "It is strongly recommended to create a backup before applying changes.\n"
            "This allows you to restore the previous configuration if needed.\n"
            "Auto-restart will apply configuration changes immediately."
        )
        layout.addWidget(info_text)
        
        layout.addStretch()
        group.setLayout(layout)
        self.content_layout.addWidget(group)
    
    def _create_review_step(self):
        """Create review and apply step."""
        group = QGroupBox("Review Configuration")
        layout = QVBoxLayout()
        
        label = QLabel("Review your configuration:")
        layout.addWidget(label)
        
        self.review_text = QTextEdit()
        self.review_text.setReadOnly(True)
        summary = self.wizard.get_summary()
        self.review_text.setText(self._format_summary(summary))
        layout.addWidget(self.review_text)
        
        layout.addStretch()
        group.setLayout(layout)
        self.content_layout.addWidget(group)
    
    def _format_summary(self, summary: dict) -> str:
        """Format summary for display."""
        lines = [
            "═" * 40,
            "PAM CONFIGURATION SUMMARY",
            "═" * 40,
            "",
        ]
        
        if summary.get("platform"):
            lines.append(f"Platform: {summary['platform']}")
        
        if summary.get("services"):
            lines.append(f"Services: {', '.join(summary['services'])}")
        
        if summary.get("security_level"):
            lines.append(f"Security Level: {summary['security_level']}")
        
        if summary.get("modules"):
            lines.append(f"\nModules to configure:")
            for module in summary['modules']:
                lines.append(f"  • {module}")
        
        return "\n".join(lines)
    
    def _on_service_toggled(self, service: str, checked: int):
        """Handle service checkbox toggle."""
        if checked:
            if service not in self.wizard.state.services:
                self.wizard.state.services.append(service)
        else:
            if service in self.wizard.state.services:
                self.wizard.state.services.remove(service)
    
    def next_step(self):
        """Move to next step."""
        if self.wizard.state.current_step == 0:
            # Platform selection
            platform = self.platform_combo.currentData()
            success, message = self.wizard.set_platform(platform)
            if not success:
                QMessageBox.warning(self, "Error", message)
                return
        
        elif self.wizard.state.current_step == 3:
            # Security level selection
            level = self.security_combo.currentData()
            self.wizard.state.hardened_mode = level != "basic"
        
        elif self.wizard.state.current_step == 4:
            # Backup settings
            self.wizard.state.backup_enabled = self.backup_checkbox.isChecked()
            self.wizard.state.auto_restart = self.auto_restart_checkbox.isChecked()
        
        self.wizard.next_step()
        self._update_current_step()
    
    def previous_step(self):
        """Move to previous step."""
        self.wizard.previous_step()
        self._update_current_step()
    
    def finish(self):
        """Finish wizard."""
        try:
            config = self.wizard.generate_configuration()
            if config:
                self.wizard_completed.emit(config)
                QMessageBox.information(self, "Success", "Configuration generated successfully!")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to generate configuration")
        except Exception as e:
            logger.error(f"Error finishing wizard: {e}")
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
    
    def cancel(self):
        """Cancel wizard."""
        reply = QMessageBox.question(
            self,
            "Cancel Wizard",
            "Are you sure you want to cancel? Any unsaved progress will be lost.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.wizard_cancelled.emit()
            self.reject()
    
    def set_callback(self, callback: Callable):
        """
        Set callback for wizard events.
        
        Args:
            callback: Callback function
        """
        self.callback = callback
