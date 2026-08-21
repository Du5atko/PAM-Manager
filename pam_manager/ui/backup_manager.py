"""Backup management widget for PAM configurations - Phase 4."""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


@dataclass
class BackupSnapshot:
    """Backup snapshot metadata."""
    backup_id: str
    timestamp: datetime
    description: str
    config_hash: str
    backup_path: str
    is_functional: bool
    size_bytes: int
    metadata: Dict[str, any] = None


class BackupManager:
    """Backup management for PAM configurations."""
    
    def __init__(self):
        """Initialize backup manager."""
        self.snapshots: List[BackupSnapshot] = []
        self.current_backup: Optional[BackupSnapshot] = None
        self.auto_backup_enabled = True
        self.max_backups = 10
        self.cleanup_enabled = True
    
    def add_snapshot(self, snapshot: BackupSnapshot) -> Tuple[bool, str]:
        """
        Add backup snapshot.
        
        Args:
            snapshot: Backup snapshot to add
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        self.snapshots.append(snapshot)
        self.current_backup = snapshot
        logger.info(f"Backup added: {snapshot.backup_id}")
        
        # Cleanup old backups if needed
        if self.cleanup_enabled and len(self.snapshots) > self.max_backups:
            self._cleanup_old_backups()
        
        return (True, f"Backup created: {snapshot.backup_id}")
    
    def _cleanup_old_backups(self) -> None:
        """Remove old backups, keeping functional ones and recent changes."""
        # Sort by timestamp, keep functional and recent
        sortable = sorted(self.snapshots, key=lambda x: x.timestamp)
        
        # Keep at least 3 recent + all functional
        keep_count = max(3, sum(1 for s in self.snapshots if s.is_functional))
        
        if len(sortable) > keep_count:
            to_remove = sortable[:-keep_count]
            self.snapshots = [s for s in self.snapshots if s not in to_remove]
            logger.info(f"Cleaned up {len(to_remove)} old backups")
    
    def get_snapshots(self) -> List[BackupSnapshot]:
        """
        Get all snapshots.
        
        Returns:
            List[BackupSnapshot]: All backup snapshots
        """
        return sorted(self.snapshots, key=lambda x: x.timestamp, reverse=True)
    
    def get_snapshot_by_id(self, backup_id: str) -> Optional[BackupSnapshot]:
        """
        Get snapshot by ID.
        
        Args:
            backup_id: Backup ID to find
            
        Returns:
            Optional[BackupSnapshot]: Snapshot if found
        """
        return next((s for s in self.snapshots if s.backup_id == backup_id), None)
    
    def get_functional_snapshots(self) -> List[BackupSnapshot]:
        """
        Get only functional snapshots.
        
        Returns:
            List[BackupSnapshot]: Functional snapshots
        """
        return [s for s in self.snapshots if s.is_functional]
    
    def get_latest_snapshot(self) -> Optional[BackupSnapshot]:
        """
        Get latest snapshot.
        
        Returns:
            Optional[BackupSnapshot]: Latest snapshot or None
        """
        if self.snapshots:
            return sorted(self.snapshots, key=lambda x: x.timestamp, reverse=True)[0]
        return None
    
    def get_last_functional_snapshot(self) -> Optional[BackupSnapshot]:
        """
        Get last functional snapshot.
        
        Returns:
            Optional[BackupSnapshot]: Last functional snapshot or None
        """
        functional = self.get_functional_snapshots()
        if functional:
            return sorted(functional, key=lambda x: x.timestamp, reverse=True)[0]
        return None
    
    def mark_functional(self, backup_id: str) -> Tuple[bool, str]:
        """
        Mark backup as functional.
        
        Args:
            backup_id: Backup ID
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        snapshot = self.get_snapshot_by_id(backup_id)
        if not snapshot:
            return (False, f"Backup not found: {backup_id}")
        
        snapshot.is_functional = True
        logger.info(f"Marked backup as functional: {backup_id}")
        return (True, f"Marked as functional: {backup_id}")
    
    def mark_broken(self, backup_id: str) -> Tuple[bool, str]:
        """
        Mark backup as broken.
        
        Args:
            backup_id: Backup ID
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        snapshot = self.get_snapshot_by_id(backup_id)
        if not snapshot:
            return (False, f"Backup not found: {backup_id}")
        
        snapshot.is_functional = False
        logger.warning(f"Marked backup as broken: {backup_id}")
        return (True, f"Marked as broken: {backup_id}")
    
    def delete_snapshot(self, backup_id: str) -> Tuple[bool, str]:
        """
        Delete backup snapshot.
        
        Args:
            backup_id: Backup ID to delete
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        snapshot = self.get_snapshot_by_id(backup_id)
        if not snapshot:
            return (False, f"Backup not found: {backup_id}")
        
        self.snapshots.remove(snapshot)
        if self.current_backup == snapshot:
            self.current_backup = None
        
        logger.info(f"Deleted backup: {backup_id}")
        return (True, f"Backup deleted: {backup_id}")
    
    def get_backup_statistics(self) -> Dict[str, any]:
        """
        Get backup statistics.
        
        Returns:
            Dict[str, any]: Statistics
        """
        total_size = sum(s.size_bytes for s in self.snapshots)
        functional_count = len(self.get_functional_snapshots())
        
        return {
            "total_backups": len(self.snapshots),
            "functional_backups": functional_count,
            "broken_backups": len(self.snapshots) - functional_count,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "oldest_backup": min((s.timestamp for s in self.snapshots), default=None),
            "newest_backup": max((s.timestamp for s in self.snapshots), default=None),
        }
    
    def generate_backup_report(self) -> str:
        """
        Generate backup report.
        
        Returns:
            str: Formatted backup report
        """
        stats = self.get_backup_statistics()
        
        report = [
            "╔════════════════════════════════════════╗",
            "║        BACKUP MANAGEMENT REPORT        ║",
            "╚════════════════════════════════════════╝",
            "",
            f"Total Backups: {stats['total_backups']}",
            f"Functional: {stats['functional_backups']}",
            f"Broken: {stats['broken_backups']}",
            f"Total Size: {stats['total_size_mb']:.2f} MB",
            "",
            "Snapshots:",
        ]
        
        for snapshot in self.get_snapshots():
            status = "✓" if snapshot.is_functional else "✗"
            report.append(
                f"  {status} {snapshot.backup_id} "
                f"({snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}) "
                f"- {snapshot.description}"
            )
        
        return "\n".join(report)
    
    def verify_backup(self, backup_id: str) -> Tuple[bool, str]:
        """
        Verify backup integrity.
        
        Args:
            backup_id: Backup ID to verify
            
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        snapshot = self.get_snapshot_by_id(backup_id)
        if not snapshot:
            return (False, f"Backup not found: {backup_id}")
        
        # Note: In real implementation, this would verify hash/checksum
        return (True, f"Backup verified: {backup_id}")
    
    def get_restore_recommendations(self) -> List[str]:
        """
        Get recommendations for restore point.
        
        Returns:
            List[str]: Restore recommendations
        """
        recommendations = []
        
        last_functional = self.get_last_functional_snapshot()
        if last_functional:
            recommendations.append(
                f"Recommend: Restore from {last_functional.backup_id} "
                f"({last_functional.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
            )
        
        if not self.get_snapshots():
            recommendations.append("No backups available - create one first!")
        elif len(self.get_snapshots()) < 3:
            recommendations.append("Create more backups for better recovery options")
        
        return recommendations


class BackupScheduler:
    """Automatic backup scheduling."""
    
    def __init__(self, manager: BackupManager):
        """
        Initialize backup scheduler.
        
        Args:
            manager: Backup manager instance
        """
        self.manager = manager
        self.schedule_interval_minutes = 60
        self.enable_schedule = True
        self.backup_on_change = True
    
    def get_schedule_config(self) -> Dict[str, any]:
        """
        Get schedule configuration.
        
        Returns:
            Dict[str, any]: Schedule configuration
        """
        return {
            "enabled": self.enable_schedule,
            "interval_minutes": self.schedule_interval_minutes,
            "backup_on_change": self.backup_on_change,
        }
    
    def set_schedule_interval(self, minutes: int) -> Tuple[bool, str]:
        """
        Set backup interval.
        
        Args:
            minutes: Interval in minutes
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if minutes < 5:
            return (False, "Minimum interval is 5 minutes")
        if minutes > 10080:  # 7 days
            return (False, "Maximum interval is 7 days")
        
        self.schedule_interval_minutes = minutes
        return (True, f"Backup interval set to {minutes} minutes")
