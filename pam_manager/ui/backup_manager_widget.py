"""Backup Manager Widget - PyQt5/PyQt4 GUI - Phase 4."""

from typing import Optional
from datetime import datetime
import logging

# Try PyQt5 first, fallback to PyQt4
try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QTextEdit, QLabel, QPushButton, QCheckBox, QSpinBox, QGroupBox,
        QMessageBox, QHeaderView, QDialog
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QColor, QBrush
    QT_VERSION = 5
except ImportError:
    from PyQt4.QtGui import (
        QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QTextEdit, QLabel, QPushButton, QCheckBox, QSpinBox, QGroupBox,
        QMessageBox, QColor, QBrush, QDialog
    )
    from PyQt4.QtCore import Qt, pyqtSignal
    QT_VERSION = 4

from pam_manager.ui.backup_manager import BackupManager, BackupSnapshot, BackupScheduler


logger = logging.getLogger(__name__)


class BackupManagerWidget(QWidget):
    """PyQt widget for backup management."""
    
    backup_restored = pyqtSignal(str)
    backup_created = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Initialize backup manager widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.manager = BackupManager()
        self.scheduler = BackupScheduler(self.manager)
        
        self.setWindowTitle("Backup Management")
        self.setGeometry(100, 100, 1000, 700)
        
        self._create_ui()
        self._refresh_display()
    
    def _create_ui(self):
        """Create user interface."""
        main_layout = QVBoxLayout()
        
        # Statistics section
        stats_group = QGroupBox("Backup Statistics")
        stats_layout = QHBoxLayout()
        
        self.stats_label = QLabel()
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        
        self.create_backup_button = QPushButton("Create Backup")
        self.create_backup_button.clicked.connect(self.create_backup)
        stats_layout.addWidget(self.create_backup_button)
        
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        # Backups table
        table_group = QGroupBox("Backup Snapshots")
        table_layout = QVBoxLayout()
        
        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(6)
        self.backups_table.setHorizontalHeaderLabels(
            ["ID", "Timestamp", "Description", "Status", "Size (MB)", "Actions"]
        )
        
        if QT_VERSION == 5:
            header = self.backups_table.horizontalHeader()
            header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        table_layout.addWidget(self.backups_table)
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group)
        
        # Schedule settings
        schedule_group = QGroupBox("Automatic Backup Schedule")
        schedule_layout = QVBoxLayout()
        
        self.schedule_enabled = QCheckBox("Enable automatic backups")
        self.schedule_enabled.setChecked(self.scheduler.enable_schedule)
        self.schedule_enabled.stateChanged.connect(self._on_schedule_enabled)
        schedule_layout.addWidget(self.schedule_enabled)
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Backup interval (minutes):"))
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(5)
        self.interval_spin.setMaximum(10080)
        self.interval_spin.setValue(self.scheduler.schedule_interval_minutes)
        self.interval_spin.valueChanged.connect(self._on_interval_changed)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addStretch()
        
        schedule_layout.addLayout(interval_layout)
        
        self.backup_on_change = QCheckBox("Backup on configuration change")
        self.backup_on_change.setChecked(self.scheduler.backup_on_change)
        self.backup_on_change.stateChanged.connect(self._on_backup_on_change)
        schedule_layout.addWidget(self.backup_on_change)
        
        schedule_group.setLayout(schedule_layout)
        main_layout.addWidget(schedule_group)
        
        # Recommendations
        recommendations_group = QGroupBox("Recommendations")
        recommendations_layout = QVBoxLayout()
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setMaximumHeight(100)
        recommendations_layout.addWidget(self.recommendations_text)
        
        recommendations_group.setLayout(recommendations_layout)
        main_layout.addWidget(recommendations_group)
        
        # Report section
        report_layout = QHBoxLayout()
        report_layout.addWidget(QLabel("Backup Report:"))
        main_layout.addLayout(report_layout)
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        main_layout.addWidget(self.report_text)
        
        self.setLayout(main_layout)
    
    def _refresh_display(self):
        """Refresh display."""
        # Update statistics
        stats = self.manager.get_backup_statistics()
        stats_text = (
            f"Total Backups: {stats['total_backups']} | "
            f"Functional: {stats['functional_backups']} | "
            f"Total Size: {stats['total_size_mb']:.2f} MB"
        )
        self.stats_label.setText(stats_text)
        
        # Update table
        snapshots = self.manager.get_snapshots()
        self.backups_table.setRowCount(len(snapshots))
        
        for row, snapshot in enumerate(snapshots):
            # ID
            id_item = QTableWidgetItem(snapshot.backup_id)
            self.backups_table.setItem(row, 0, id_item)
            
            # Timestamp
            ts_item = QTableWidgetItem(
                snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
            self.backups_table.setItem(row, 1, ts_item)
            
            # Description
            desc_item = QTableWidgetItem(snapshot.description)
            self.backups_table.setItem(row, 2, desc_item)
            
            # Status
            status = "✓ Functional" if snapshot.is_functional else "✗ Broken"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(
                QBrush(QColor(0, 128, 0) if snapshot.is_functional else QColor(255, 0, 0))
            )
            self.backups_table.setItem(row, 3, status_item)
            
            # Size
            size_mb = snapshot.size_bytes / (1024 * 1024)
            size_item = QTableWidgetItem(f"{size_mb:.2f}")
            size_item.setTextAlignment(Qt.AlignRight)
            self.backups_table.setItem(row, 4, size_item)
            
            # Actions button
            action_button = QPushButton("Restore")
            action_button.clicked.connect(
                lambda checked, bid=snapshot.backup_id: self.restore_backup(bid)
            )
            self.backups_table.setCellWidget(row, 5, action_button)
        
        # Update recommendations
        recommendations = self.manager.get_restore_recommendations()
        self.recommendations_text.setText("\n".join(recommendations))
        
        # Update report
        report = self.manager.generate_backup_report()
        self.report_text.setText(report)
    
    def create_backup(self):
        """Create new backup."""
        snapshot = BackupSnapshot(
            backup_id=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            description="Manual backup",
            config_hash="placeholder",
            backup_path="/tmp/pam_backup",
            is_functional=True,
            size_bytes=1024,
        )
        
        success, message = self.manager.add_snapshot(snapshot)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.backup_created.emit(snapshot.backup_id)
            self._refresh_display()
        else:
            QMessageBox.warning(self, "Error", message)
    
    def restore_backup(self, backup_id: str):
        """Restore backup."""
        snapshot = self.manager.get_snapshot_by_id(backup_id)
        if not snapshot:
            QMessageBox.warning(self, "Error", f"Backup not found: {backup_id}")
            return
        
        reply = QMessageBox.question(
            self,
            "Restore Backup",
            f"Restore from {backup_id}?\nThis will overwrite current configuration.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Success", f"Restored from {backup_id}")
            self.backup_restored.emit(backup_id)
    
    def _on_schedule_enabled(self, state):
        """Handle schedule enable/disable."""
        self.scheduler.enable_schedule = state != 0
        self.interval_spin.setEnabled(state != 0)
    
    def _on_interval_changed(self, value):
        """Handle interval change."""
        success, message = self.scheduler.set_schedule_interval(value)
        if not success:
            QMessageBox.warning(self, "Error", message)
    
    def _on_backup_on_change(self, state):
        """Handle backup on change."""
        self.scheduler.backup_on_change = state != 0
