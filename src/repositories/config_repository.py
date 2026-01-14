"""
Configuration repository for persisting StoryMetadata objects.

This repository handles saving, loading, updating, and deleting story metadata
(which serves as the configuration for story generation) using JSON file storage.
"""

import json
import uuid
from pathlib import Path
from typing import Optional, List
from dataclasses import asdict

from src.models.story import StoryMetadata


class ConfigRepository:
    """
    Repository for managing StoryMetadata persistence.

    Stores story metadata/configurations as JSON files in a local directory structure.
    Each config is stored as a separate JSON file with a unique ID.
    """

    def __init__(self, storage_dir: Path):
        """
        Initialize the repository with a storage directory.

        Args:
            storage_dir: Directory where config files will be stored
        """
        self.storage_dir = Path(storage_dir)
        self.configs_dir = self.storage_dir / "configs"

        # Create directories if they don't exist
        self.configs_dir.mkdir(parents=True, exist_ok=True)

    def save(self, config: StoryMetadata) -> str:
        """
        Save a new StoryMetadata and return its ID.

        Args:
            config: The StoryMetadata to save

        Returns:
            The unique ID assigned to the config
        """
        config_id = f"config-{uuid.uuid4()}"
        config_file = self.configs_dir / f"{config_id}.json"

        # Convert config to dict and save as JSON
        config_data = asdict(config)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        return config_id

    def get(self, config_id: str) -> Optional[StoryMetadata]:
        """
        Retrieve a StoryMetadata by its ID.

        Args:
            config_id: The ID of the config to retrieve

        Returns:
            The StoryMetadata if found, None otherwise
        """
        config_file = self.configs_dir / f"{config_id}.json"

        if not config_file.exists():
            return None

        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        return StoryMetadata(**config_data)

    def list_all(self) -> List[str]:
        """
        List all config IDs in the repository.

        Returns:
            List of config IDs
        """
        config_ids = []

        for config_file in self.configs_dir.glob("*.json"):
            config_id = config_file.stem  # filename without extension
            config_ids.append(config_id)

        return sorted(config_ids)

    def update(self, config_id: str, config: StoryMetadata) -> None:
        """
        Update an existing config.

        Args:
            config_id: The ID of the config to update
            config: The new StoryMetadata data

        Raises:
            ValueError: If the config doesn't exist
        """
        config_file = self.configs_dir / f"{config_id}.json"

        if not config_file.exists():
            raise ValueError(f"Config with id {config_id} not found")

        # Convert config to dict and save as JSON
        config_data = asdict(config)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

    def delete(self, config_id: str) -> None:
        """
        Delete a config by its ID.

        Args:
            config_id: The ID of the config to delete

        Raises:
            ValueError: If the config doesn't exist
        """
        config_file = self.configs_dir / f"{config_id}.json"

        if not config_file.exists():
            raise ValueError(f"Config with id {config_id} not found")

        config_file.unlink()
