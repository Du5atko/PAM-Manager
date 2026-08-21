"""Transactional Access Module - Atomic PAM Configuration Management.

Provides transactional file access with backup, verify, commit, and rollback
capabilities. Maintains snapshots of functional configurations.
"""

import logging
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class Snapshot:
    """Represents a snapshot of a functional configuration state."""
    timestamp: str
    verification_timestamp: str
    config_hash: str
    backup_path: Path
    is_functional: bool = True
    metadata: Dict = None
    
    def to_dict(self) -> Dict:
        """Convert snapshot to dictionary."""
        return {
            'timestamp': self.timestamp,
            'verification_timestamp': self.verification_timestamp,
            'config_hash': self.config_hash,
            'backup_path': str(self.backup_path),
            'is_functional': self.is_functional,
            'metadata': self.metadata or {}
        }


class TransactionState:
    """Represents current transaction state."""
    
    def __init__(self):
        self.step = 0
        self.backup_created = False
        self.backup_path = None
        self.verified = False
        self.committed = False
        self.original_content = None
        self.new_content = None
        self.steps = []
    
    def mark_step(self, step_name: str) -> None:
        """Mark completion of a transaction step."""
        self.steps.append({
            'name': step_name,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed'
        })
        logger.debug(f"Transaction step completed: {step_name}")
    
    def add_rollback_point(self, step_name: str) -> None:
        """Add rollback point for a step."""
        self.steps.append({
            'name': step_name,
            'timestamp': datetime.now().isoformat(),
            'status': 'rollback_available'
        })
    
    def get_steps(self) -> List[Dict]:
        """Get list of completed steps."""
        return self.steps


class TransactionalAccess:
    """Manages atomic transactions for PAM configuration files.
    
    Workflow:
    1. Backup - Create backup of current configuration
    2. Verify - Verify backup integrity
    3. Modify - Apply changes
    4. Test - Test modified configuration
    5. Commit - Make changes permanent
    
    Rollback:
    - Can rollback to last functional snapshot
    - Maintains all snapshots except intermediate versions
    """
    
    def __init__(self, config_dir: Path, backup_dir: Path = None,
                 snapshots_dir: Path = None, max_snapshots: int = 10):
        """Initialize TransactionalAccess.
        
        Args:
            config_dir: Directory containing PAM configuration files
            backup_dir: Directory for backups (default: config_dir/.backup)
            snapshots_dir: Directory for snapshots (default: config_dir/.snapshots)
            max_snapshots: Maximum number of snapshots to keep
        """
        self.config_dir = Path(config_dir)
        self.backup_dir = Path(backup_dir or self.config_dir / '.backup')
        self.snapshots_dir = Path(snapshots_dir or self.config_dir / '.snapshots')
        self.max_snapshots = max_snapshots
        self.snapshots: List[Snapshot] = []
        self.current_transaction: Optional[TransactionState] = None
        
        # Create directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing snapshots
        self._load_snapshots()
    
    # ========================================================================
    # Snapshot Management
    # ========================================================================
    
    def _load_snapshots(self) -> None:
        """Load existing snapshots from snapshots directory."""
        snapshots_file = self.snapshots_dir / 'snapshots.json'
        
        if snapshots_file.exists():
            try:
                with open(snapshots_file, 'r') as f:
                    data = json.load(f)
                    self.snapshots = [
                        Snapshot(
                            timestamp=s['timestamp'],
                            verification_timestamp=s['verification_timestamp'],
                            config_hash=s['config_hash'],
                            backup_path=Path(s['backup_path']),
                            is_functional=s.get('is_functional', True),
                            metadata=s.get('metadata')
                        )
                        for s in data.get('snapshots', [])
                    ]
                logger.info(f"Loaded {len(self.snapshots)} snapshots")
            except Exception as e:
                logger.warning(f"Failed to load snapshots: {e}")
    
    def _save_snapshots(self) -> None:
        """Save snapshots to snapshots directory."""
        snapshots_file = self.snapshots_dir / 'snapshots.json'
        
        try:
            with open(snapshots_file, 'w') as f:
                data = {
                    'snapshots': [s.to_dict() for s in self.snapshots],
                    'last_updated': datetime.now().isoformat(),
                    'total_snapshots': len(self.snapshots)
                }
                json.dump(data, f, indent=2)
            logger.debug("Snapshots saved")
        except Exception as e:
            logger.error(f"Failed to save snapshots: {e}")
    
    def _cleanup_old_snapshots(self) -> None:
        """Remove old snapshots, keeping only functional ones and recent changes."""
        if len(self.snapshots) <= self.max_snapshots:
            return
        
        # Keep last functional snapshot and all snapshots after it
        last_functional_idx = -1
        for i in range(len(self.snapshots) - 1, -1, -1):
            if self.snapshots[i].is_functional:
                last_functional_idx = i
                break
        
        # Keep all snapshots from last_functional to end
        # Delete older ones if exceeding max_snapshots
        snapshots_to_keep = max(
            self.max_snapshots,
            len(self.snapshots) - last_functional_idx
        )
        
        if len(self.snapshots) > snapshots_to_keep:
            to_remove = self.snapshots[:len(self.snapshots) - snapshots_to_keep]
            for snapshot in to_remove:
                try:
                    if snapshot.backup_path.exists():
                        snapshot.backup_path.unlink()
                    logger.debug(f"Removed old snapshot: {snapshot.backup_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove snapshot: {e}")
            
            self.snapshots = self.snapshots[len(to_remove):]
    
    # ========================================================================
    # Transaction Operations
    # ========================================================================
    
    def begin_transaction(self, config_file: Path, description: str = "") -> TransactionState:
        """Begin a new transaction.
        
        Args:
            config_file: Path to configuration file
            description: Transaction description
            
        Returns:
            TransactionState object
        """
        self.current_transaction = TransactionState()
        self.current_transaction.original_content = self._read_file(config_file)
        logger.info(f"Transaction started for {config_file.name}")
        return self.current_transaction
    
    def backup_step(self, config_file: Path) -> Tuple[bool, str]:
        """Step 1: Create backup of current configuration.
        
        Args:
            config_file: Path to file to backup
            
        Returns:
            Tuple of (success, backup_path_or_error)
        """
        if not self.current_transaction:
            return False, "No active transaction"
        
        try:
            backup_path = self.backup_dir / f"{config_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            shutil.copy2(config_file, backup_path)
            
            self.current_transaction.backup_path = backup_path
            self.current_transaction.backup_created = True
            self.current_transaction.mark_step("backup")
            
            logger.info(f"Backup created: {backup_path}")
            return True, str(backup_path)
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False, str(e)
    
    def verify_step(self, config_file: Path) -> Tuple[bool, str]:
        """Step 2: Verify backup integrity.
        
        Args:
            config_file: Path to file to verify
            
        Returns:
            Tuple of (success, message)
        """
        if not self.current_transaction or not self.current_transaction.backup_created:
            return False, "Backup not created"
        
        try:
            if not self.current_transaction.backup_path.exists():
                return False, "Backup file not found"
            
            # Verify backup matches original
            original_hash = self._compute_hash(config_file)
            backup_hash = self._compute_hash(self.current_transaction.backup_path)
            
            if original_hash != backup_hash:
                return False, "Backup verification failed - hash mismatch"
            
            self.current_transaction.verified = True
            self.current_transaction.mark_step("verify")
            
            logger.info(f"Backup verified: {original_hash}")
            return True, "Backup verified successfully"
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False, str(e)
    
    def test_step(self, test_func) -> Tuple[bool, str]:
        """Step 3: Test modified configuration.
        
        Args:
            test_func: Callable that tests configuration
            
        Returns:
            Tuple of (success, message)
        """
        if not self.current_transaction or not self.current_transaction.verified:
            return False, "Verification not completed"
        
        try:
            result = test_func()
            self.current_transaction.mark_step("test")
            return True if result else False, "Configuration test passed" if result else "Configuration test failed"
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return False, str(e)
    
    def commit_step(self, config_file: Path, is_functional: bool = True) -> Tuple[bool, str]:
        """Step 5: Commit changes and create snapshot.
        
        Args:
            config_file: Path to configuration file
            is_functional: Whether configuration is verified as functional
            
        Returns:
            Tuple of (success, message)
        """
        if not self.current_transaction:
            return False, "No active transaction"
        
        try:
            config_hash = self._compute_hash(config_file)
            
            # Create snapshot
            snapshot = Snapshot(
                timestamp=datetime.now().isoformat(),
                verification_timestamp=datetime.now().isoformat(),
                config_hash=config_hash,
                backup_path=self.current_transaction.backup_path,
                is_functional=is_functional,
                metadata={
                    'transaction_steps': self.current_transaction.get_steps()
                }
            )
            
            self.snapshots.append(snapshot)
            self._save_snapshots()
            self._cleanup_old_snapshots()
            
            self.current_transaction.committed = True
            self.current_transaction.mark_step("commit")
            
            logger.info(f"Configuration committed: {config_hash}")
            return True, f"Configuration committed (snapshot: {config_hash})"
        except Exception as e:
            logger.error(f"Commit failed: {e}")
            return False, str(e)
    
    def rollback(self, config_file: Path, snapshot_index: int = -1) -> Tuple[bool, str]:
        """Rollback to previous snapshot.
        
        Args:
            config_file: Path to configuration file
            snapshot_index: Index of snapshot to rollback to (default: last)
            
        Returns:
            Tuple of (success, message)
        """
        if not self.snapshots:
            return False, "No snapshots available"
        
        if snapshot_index >= len(self.snapshots) or snapshot_index < -len(self.snapshots):
            return False, f"Invalid snapshot index: {snapshot_index}"
        
        snapshot = self.snapshots[snapshot_index]
        
        try:
            if not snapshot.backup_path.exists():
                return False, f"Snapshot backup not found: {snapshot.backup_path}"
            
            shutil.copy2(snapshot.backup_path, config_file)
            logger.info(f"Rolled back to snapshot: {snapshot.timestamp}")
            return True, f"Rolled back to snapshot from {snapshot.timestamp}"
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False, str(e)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    @staticmethod
    def _read_file(path: Path) -> str:
        """Read file content."""
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            return ""
    
    @staticmethod
    def _compute_hash(path: Path) -> str:
        """Compute SHA256 hash of file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute hash: {e}")
            return ""
    
    def get_snapshots(self) -> List[Snapshot]:
        """Get list of all snapshots."""
        return self.snapshots
    
    def get_last_functional_snapshot(self) -> Optional[Snapshot]:
        """Get last functional snapshot."""
        for snapshot in reversed(self.snapshots):
            if snapshot.is_functional:
                return snapshot
        return None


__all__ = ['TransactionalAccess', 'Snapshot', 'TransactionState']
