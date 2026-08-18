"""Policy model module."""

from datetime import UTC, datetime
from typing import Dict, Optional

import yaml

from pam_manager.core import SecurityPolicy


class PolicyModel:
    """Manages security policy models."""

    @staticmethod
    def create_default_policy(name: str = "default") -> SecurityPolicy:
        """Create a default security policy.

        Args:
            name: Name for the policy

        Returns:
            SecurityPolicy: Default policy with sensible defaults
        """
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        return SecurityPolicy(
            name=name,
            version="0.1",
            created_timestamp=now,
            last_modified_timestamp=now,
            description="Default security policy",
        )

    @staticmethod
    def from_dict(data: Dict) -> SecurityPolicy:
        """Create policy from dictionary.

        Args:
            data: Dictionary representation of policy

        Returns:
            SecurityPolicy: Policy object

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            # Basic validation
            required_fields = ["name", "version", "created_timestamp"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return SecurityPolicy(
                name=data["name"],
                version=data["version"],
                created_timestamp=data["created_timestamp"],
                last_modified_timestamp=data.get(
                    "last_modified_timestamp",
                    data["created_timestamp"],
                ),
                description=data.get("description", ""),
                # Note: Full implementation would parse nested policy sections
            )
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid policy data: {str(e)}")

    @staticmethod
    def to_dict(policy: SecurityPolicy) -> Dict:
        """Convert policy to dictionary.

        Args:
            policy: Policy object

        Returns:
            dict: Dictionary representation
        """
        from dataclasses import asdict

        return asdict(policy)

    @staticmethod
    def from_yaml(yaml_content: str) -> SecurityPolicy:
        """Load policy from YAML string.

        Args:
            yaml_content: YAML content as string

        Returns:
            SecurityPolicy: Policy object

        Raises:
            ValueError: If YAML is invalid or missing required fields
        """
        try:
            data = yaml.safe_load(yaml_content)
            if not isinstance(data, dict):
                raise ValueError("YAML must contain a dictionary")
            return PolicyModel.from_dict(data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {str(e)}")

    @staticmethod
    def to_yaml(policy: SecurityPolicy) -> str:
        """Convert policy to YAML string.

        Args:
            policy: Policy object

        Returns:
            str: YAML representation
        """
        data = PolicyModel.to_dict(policy)
        return yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    @staticmethod
    def load_from_file(path: str) -> SecurityPolicy:
        """Load policy from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            SecurityPolicy: Policy object

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file content is invalid
        """
        with open(path, "r") as f:
            return PolicyModel.from_yaml(f.read())

    @staticmethod
    def save_to_file(policy: SecurityPolicy, path: str) -> None:
        """Save policy to YAML file.

        Args:
            policy: Policy object
            path: Path to save YAML file
        """
        with open(path, "w") as f:
            f.write(PolicyModel.to_yaml(policy))


__all__ = ["PolicyModel"]
