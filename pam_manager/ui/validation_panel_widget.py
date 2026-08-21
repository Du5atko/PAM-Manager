"""Validation Panel Widget - PyQt5/PyQt4 GUI - Phase 4."""

from typing import Optional
import logging

# Try PyQt5 first, fallback to PyQt4
try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QTextEdit, QLabel, QPushButton, QComboBox, QGroupBox, QHeaderView
    )
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QColor, QFont, QBrush
    QT_VERSION = 5
except ImportError:
    from PyQt4.QtGui import (
        QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QTextEdit, QLabel, QPushButton, QComboBox, QGroupBox, QColor,
        QFont, QBrush
    )
    from PyQt4.QtCore import Qt
    QT_VERSION = 4

from pam_manager.ui.validation_panel import ValidationPanel, ValidationLevel


logger = logging.getLogger(__name__)


class ValidationPanelWidget(QWidget):
    """PyQt widget for validation panel display."""
    
    def __init__(self, parent=None):
        """
        Initialize validation panel widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.panel = ValidationPanel()
        
        self.setWindowTitle("PAM Validation Results")
        self.setGeometry(100, 100, 1000, 600)
        
        self._create_ui()
        self._update_display()
    
    def _create_ui(self):
        """Create user interface."""
        main_layout = QVBoxLayout()
        
        # Summary section
        summary_layout = QHBoxLayout()
        
        self.summary_label = QLabel()
        summary_layout.addWidget(self.summary_label)
        
        summary_layout.addStretch()
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_messages)
        summary_layout.addWidget(self.clear_button)
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_results)
        summary_layout.addWidget(self.export_button)
        
        main_layout.addLayout(summary_layout)
        
        # Filter section
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filter by level:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All", None)
        self.filter_combo.addItem("Critical", ValidationLevel.CRITICAL)
        self.filter_combo.addItem("Errors", ValidationLevel.ERROR)
        self.filter_combo.addItem("Warnings", ValidationLevel.WARNING)
        self.filter_combo.addItem("Info", ValidationLevel.INFO)
        self.filter_combo.currentIndexChanged.connect(self._update_display)
        filter_layout.addWidget(self.filter_combo)
        
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        
        # Messages table
        self.messages_table = QTableWidget()
        self.messages_table.setColumnCount(5)
        self.messages_table.setHorizontalHeaderLabels(
            ["Level", "Stage", "Message", "Module", "Line"]
        )
        
        if QT_VERSION == 5:
            header = self.messages_table.horizontalHeader()
            header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        main_layout.addWidget(self.messages_table)
        
        # Report section
        report_layout = QHBoxLayout()
        report_layout.addWidget(QLabel("Analysis Report:"))
        main_layout.addLayout(report_layout)
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setMaximumHeight(200)
        main_layout.addWidget(self.report_text)
        
        self.setLayout(main_layout)
    
    def add_validation_result(self, level: ValidationLevel, stage: str, message: str,
                             line_number: Optional[int] = None,
                             module_name: Optional[str] = None) -> None:
        """
        Add validation result.
        
        Args:
            level: Validation level
            stage: Validation stage
            message: Message text
            line_number: Optional line number
            module_name: Optional module name
        """
        self.panel.add_validation_result(
            level=level,
            stage=stage,
            message=message,
            line_number=line_number,
            module_name=module_name,
        )
        self._update_display()
    
    def _update_display(self):
        """Update display."""
        # Update summary
        summary = self.panel.get_summary()
        summary_text = (
            f"Total: {summary['total']} | "
            f"Critical: {summary['critical']} | "
            f"Errors: {summary['error']} | "
            f"Warnings: {summary['warning']} | "
            f"Info: {summary['info']}"
        )
        self.summary_label.setText(summary_text)
        
        # Update table
        selected_level = self.filter_combo.currentData()
        
        if selected_level is None:
            messages = self.panel.messages
        else:
            messages = self.panel.get_messages_by_level(selected_level)
        
        self.messages_table.setRowCount(len(messages))
        
        color_map = {
            ValidationLevel.CRITICAL: QColor(255, 200, 200),  # Light red
            ValidationLevel.ERROR: QColor(255, 220, 220),     # Very light red
            ValidationLevel.WARNING: QColor(255, 255, 200),   # Light yellow
            ValidationLevel.INFO: QColor(200, 220, 255),      # Light blue
        }
        
        for row, message in enumerate(messages):
            # Level cell
            level_item = QTableWidgetItem(message.level.value.upper())
            level_item.setBackground(QBrush(color_map[message.level]))
            level_item.setFont(QFont("Monospace"))
            self.messages_table.setItem(row, 0, level_item)
            
            # Stage cell
            stage_item = QTableWidgetItem(message.stage)
            stage_item.setBackground(QBrush(color_map[message.level]))
            self.messages_table.setItem(row, 1, stage_item)
            
            # Message cell
            msg_item = QTableWidgetItem(message.message)
            msg_item.setBackground(QBrush(color_map[message.level]))
            self.messages_table.setItem(row, 2, msg_item)
            
            # Module cell
            module_item = QTableWidgetItem(message.module_name or "")
            module_item.setBackground(QBrush(color_map[message.level]))
            self.messages_table.setItem(row, 3, module_item)
            
            # Line cell
            line_item = QTableWidgetItem(str(message.line_number or ""))
            line_item.setBackground(QBrush(color_map[message.level]))
            line_item.setTextAlignment(Qt.AlignRight)
            self.messages_table.setItem(row, 4, line_item)
        
        # Update report
        report = self.panel.get_analysis_report()
        self.report_text.setText(report)
    
    def clear_messages(self) -> None:
        """Clear all messages."""
        self.panel.clear_messages()
        self._update_display()
    
    def export_results(self) -> None:
        """Export results."""
        import json
        results = self.panel.export_as_json()
        
        # Create export dialog
        try:
            from PyQt5.QtWidgets import QFileDialog
        except ImportError:
            from PyQt4.QtGui import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Validation Results",
            "validation_results.json",
            "JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w') as f:
                        json.dump(results, f, indent=2, default=str)
                else:
                    with open(filename, 'w') as f:
                        f.write(self.panel.get_analysis_report())
                logger.info(f"Exported results to {filename}")
            except Exception as e:
                logger.error(f"Error exporting results: {e}")
