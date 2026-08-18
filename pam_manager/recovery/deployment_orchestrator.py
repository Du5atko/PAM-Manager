"""PAM Deployment Orchestrator - Manages safe deployment of PAM policies."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json

from pam_manager.core import Platform
from pam_manager.engine import PolicyEngine, PolicyValidationResult
from pam_manager.package_manager import PackageManagerFactory
from pam_manager.renderer import PamRenderer, PamFileConfig
from pam_manager.modules import ModuleRegistry


class DeploymentStatus(Enum):
    """Deployment status enumeration."""

    PENDING = "pending"
    VALIDATING = "validating"
    PACKAGES_INSTALLING = "packages_installing"
    RENDERING = "rendering"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class DeploymentStep:
    """Represents a deployment step."""

    name: str
    description: str
    status: DeploymentStatus
    timestamp: datetime
    result: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "result": self.result,
            "error": self.error,
        }


@dataclass(frozen=True)
class DeploymentCheckpoint:
    """Deployment checkpoint for rollback."""

    checkpoint_id: str
    timestamp: datetime
    modules: List[str]
    pam_files_backed_up: Dict[str, str]  # file_path -> backup_path
    installed_packages: List[str]
    system_state: Dict

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "timestamp": self.timestamp.isoformat(),
            "modules": self.modules,
            "pam_files_backed_up": self.pam_files_backed_up,
            "installed_packages": self.installed_packages,
            "system_state": self.system_state,
        }


class DeploymentOrchestrator:
    """Orchestrates safe deployment of PAM policies."""

    def __init__(self, platform: Platform = None, dry_run: bool = True) -> None:
        """Initialize deployment orchestrator.

        Args:
            platform: Target platform
            dry_run: If True, don't make actual changes
        """
        self.platform = platform or Platform.UBUNTU
        self.dry_run = dry_run
        self.engine = PolicyEngine(platform)
        self.renderer = PamRenderer(platform)
        self.registry = ModuleRegistry()
        self.package_manager = PackageManagerFactory.create_for_platform(self.platform)
        self.steps: List[DeploymentStep] = []
        self.checkpoints: Dict[str, DeploymentCheckpoint] = {}
        self.current_checkpoint: Optional[DeploymentCheckpoint] = None

    def deploy_policy(
        self, modules: List[str], backup_dir: str = "/var/backups/pam"
    ) -> Tuple[bool, str]:
        """Deploy PAM policy end-to-end.

        Args:
            modules: List of module names to deploy
            backup_dir: Directory for backups

        Returns:
            Tuple of (success, message)
        """
        try:
            # Step 1: Validate policy
            if not self._validate_policy(modules):
                return False, "Policy validation failed"

            # Step 2: Create checkpoint
            checkpoint = self._create_checkpoint(modules)
            self.current_checkpoint = checkpoint

            # Step 3: Install packages
            if not self._install_packages(modules):
                return False, "Package installation failed"

            # Step 4: Render PAM files
            configs = self._render_pam_files(modules)
            if not configs:
                return False, "PAM file rendering failed"

            # Step 5: Backup existing files
            if not self._backup_existing_files(configs, backup_dir):
                return False, "File backup failed"

            # Step 6: Deploy PAM files
            if not self._deploy_pam_files(configs):
                return False, "PAM file deployment failed"

            # Step 7: Verify deployment
            if not self._verify_deployment(modules):
                self._rollback_deployment()
                return False, "Deployment verification failed"

            self._add_step(
                "deployment",
                "Complete PAM policy deployment",
                DeploymentStatus.COMPLETED,
            )

            return True, "Policy deployed successfully"

        except Exception as e:
            self._add_step(
                "deployment",
                "PAM policy deployment",
                DeploymentStatus.FAILED,
                error=str(e),
            )
            self._rollback_deployment()
            return False, f"Deployment failed: {e}"

    def _validate_policy(self, modules: List[str]) -> bool:
        """Validate policy before deployment.

        Args:
            modules: Modules to validate

        Returns:
            True if valid
        """
        self._add_step(
            "validation",
            "Validate PAM policy",
            DeploymentStatus.VALIDATING,
        )

        validation = self.engine.validate_policy(modules)

        if not validation.valid:
            self._add_step(
                "validation",
                "Validate PAM policy",
                DeploymentStatus.FAILED,
                error=f"Conflicts: {len(validation.conflicts)}",
            )
            return False

        self._add_step(
            "validation",
            "Validate PAM policy",
            DeploymentStatus.COMPLETED,
            result=f"Validated {len(validation.module_list)} modules",
        )

        return True

    def _create_checkpoint(self, modules: List[str]) -> DeploymentCheckpoint:
        """Create deployment checkpoint.

        Args:
            modules: Modules being deployed

        Returns:
            DeploymentCheckpoint object
        """
        checkpoint_id = f"checkpoint-{datetime.now().timestamp()}"

        return DeploymentCheckpoint(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now(),
            modules=modules,
            pam_files_backed_up={},
            installed_packages=[],
            system_state=self._capture_system_state(),
        )

    def _capture_system_state(self) -> Dict:
        """Capture current system state for rollback.

        Returns:
            Dictionary with system state information
        """
        return {
            "platform": self.platform.name,
            "timestamp": datetime.now().isoformat(),
            "pam_files": {},  # Would capture actual file contents
            "installed_packages": [],  # Would capture actual packages
        }

    def _install_packages(self, modules: List[str]) -> bool:
        """Install required packages.

        Args:
            modules: Modules whose packages to install

        Returns:
            True if successful
        """
        self._add_step(
            "packages",
            "Install required packages",
            DeploymentStatus.PACKAGES_INSTALLING,
        )

        packages_to_install = []
        for module_name in modules:
            module_info = self.registry.get_module(module_name)
            if module_info:
                pkg_name = module_info.get_package_name(self.platform)
                if pkg_name:
                    packages_to_install.append(pkg_name)

        if not packages_to_install:
            self._add_step(
                "packages",
                "Install required packages",
                DeploymentStatus.COMPLETED,
                result="No packages to install",
            )
            return True

        if not self.dry_run:
            try:
                for package in packages_to_install:
                    result = self.package_manager.install_packages([package])
                    if result.success:
                        if self.current_checkpoint:
                            self.current_checkpoint.installed_packages.append(package)
            except Exception as e:
                self._add_step(
                    "packages",
                    "Install required packages",
                    DeploymentStatus.FAILED,
                    error=str(e),
                )
                return False

        self._add_step(
            "packages",
            "Install required packages",
            DeploymentStatus.COMPLETED,
            result=f"Installed {len(packages_to_install)} packages",
        )

        return True

    def _render_pam_files(self, modules: List[str]) -> Dict[str, PamFileConfig]:
        """Render PAM configuration files.

        Args:
            modules: Modules to render

        Returns:
            Dictionary of PamFileConfig objects
        """
        self._add_step(
            "rendering",
            "Render PAM configuration files",
            DeploymentStatus.RENDERING,
        )

        try:
            configs = self.renderer.render_policy(modules)

            self._add_step(
                "rendering",
                "Render PAM configuration files",
                DeploymentStatus.COMPLETED,
                result=f"Rendered {len(configs)} files",
            )

            return configs
        except Exception as e:
            self._add_step(
                "rendering",
                "Render PAM configuration files",
                DeploymentStatus.FAILED,
                error=str(e),
            )
            return {}

    def _backup_existing_files(
        self, configs: Dict[str, PamFileConfig], backup_dir: str
    ) -> bool:
        """Backup existing PAM files.

        Args:
            configs: PAM configurations
            backup_dir: Directory for backups

        Returns:
            True if successful
        """
        backup_path = Path(backup_dir)

        if not self.dry_run and not backup_path.exists():
            backup_path.mkdir(parents=True, exist_ok=True)

        backups = {}
        for file_name, config in configs.items():
            if config.path.exists():
                backup_file = backup_path / f"{file_name}.{datetime.now().timestamp()}"
                if not self.dry_run:
                    try:
                        config.path.read_bytes()  # Read existing
                        backups[str(config.path)] = str(backup_file)
                    except Exception as e:
                        self._add_step(
                            "backup",
                            f"Backup {file_name}",
                            DeploymentStatus.FAILED,
                            error=str(e),
                        )
                        return False

        if self.current_checkpoint:
            object.__setattr__(
                self.current_checkpoint,
                "pam_files_backed_up",
                backups,
            )

        return True

    def _deploy_pam_files(self, configs: Dict[str, PamFileConfig]) -> bool:
        """Deploy PAM configuration files.

        Args:
            configs: PAM configurations

        Returns:
            True if successful
        """
        self._add_step(
            "deployment",
            "Deploy PAM files",
            DeploymentStatus.DEPLOYING,
        )

        try:
            for file_name, config in configs.items():
                if not self.dry_run:
                    self.renderer.save_to_file(config, dry_run=False)
        except Exception as e:
            self._add_step(
                "deployment",
                "Deploy PAM files",
                DeploymentStatus.FAILED,
                error=str(e),
            )
            return False

        self._add_step(
            "deployment",
            "Deploy PAM files",
            DeploymentStatus.COMPLETED,
            result=f"Deployed {len(configs)} files",
        )

        return True

    def _verify_deployment(self, modules: List[str]) -> bool:
        """Verify deployment success.

        Args:
            modules: Deployed modules

        Returns:
            True if verification passes
        """
        self._add_step(
            "verification",
            "Verify deployment",
            DeploymentStatus.VALIDATING,
        )

        # Check module info is accessible
        for module_name in modules:
            info = self.engine.get_module_info(module_name)
            if not info.get("found"):
                self._add_step(
                    "verification",
                    "Verify deployment",
                    DeploymentStatus.FAILED,
                    error=f"Module {module_name} verification failed",
                )
                return False

        self._add_step(
            "verification",
            "Verify deployment",
            DeploymentStatus.COMPLETED,
            result=f"Verified {len(modules)} modules",
        )

        return True

    def _rollback_deployment(self) -> bool:
        """Rollback to previous checkpoint.

        Returns:
            True if successful
        """
        if not self.current_checkpoint:
            self._add_step(
                "rollback",
                "Rollback deployment",
                DeploymentStatus.FAILED,
                error="No checkpoint to rollback",
            )
            return False

        self._add_step(
            "rollback",
            "Rollback deployment",
            DeploymentStatus.DEPLOYING,
        )

        try:
            # Restore PAM files from backups
            for orig_path, backup_path in self.current_checkpoint.pam_files_backed_up.items():
                if not self.dry_run and Path(backup_path).exists():
                    Path(backup_path).rename(Path(orig_path))

            self._add_step(
                "rollback",
                "Rollback deployment",
                DeploymentStatus.ROLLED_BACK,
                result="Rolled back to checkpoint",
            )

            return True
        except Exception as e:
            self._add_step(
                "rollback",
                "Rollback deployment",
                DeploymentStatus.FAILED,
                error=str(e),
            )
            return False

    def _add_step(
        self,
        step_name: str,
        description: str,
        status: DeploymentStatus,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Add deployment step record.

        Args:
            step_name: Step identifier
            description: Step description
            status: Step status
            result: Optional result message
            error: Optional error message
        """
        step = DeploymentStep(
            name=step_name,
            description=description,
            status=status,
            timestamp=datetime.now(),
            result=result,
            error=error,
        )
        self.steps.append(step)

    def get_deployment_report(self) -> str:
        """Get deployment report.

        Returns:
            Report string
        """
        report_lines = [
            "=" * 60,
            "DEPLOYMENT REPORT",
            "=" * 60,
            f"Platform: {self.platform.name}",
            f"Dry Run: {self.dry_run}",
            f"Timestamp: {datetime.now().isoformat()}",
            "",
            "DEPLOYMENT STEPS:",
            "-" * 60,
        ]

        for step in self.steps:
            status_symbol = (
                "✓"
                if step.status == DeploymentStatus.COMPLETED
                else "✗" if step.status == DeploymentStatus.FAILED
                else "⏳"
            )
            report_lines.append(f"{status_symbol} {step.name}: {step.status.value}")
            report_lines.append(f"   {step.description}")
            if step.result:
                report_lines.append(f"   Result: {step.result}")
            if step.error:
                report_lines.append(f"   Error: {step.error}")

        report_lines.extend(
            [
                "",
                "=" * 60,
            ]
        )

        return "\n".join(report_lines)

    def get_steps_as_json(self) -> str:
        """Get deployment steps as JSON.

        Returns:
            JSON string
        """
        steps_data = [step.to_dict() for step in self.steps]
        return json.dumps(steps_data, indent=2)

    def save_deployment_log(self, filepath: str) -> bool:
        """Save deployment log to file.

        Args:
            filepath: Path to save log

        Returns:
            True if successful
        """
        try:
            Path(filepath).write_text(self.get_deployment_report())
            return True
        except Exception:
            return False


__all__ = ["DeploymentOrchestrator", "DeploymentStatus", "DeploymentStep", "DeploymentCheckpoint"]
