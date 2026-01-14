"""
Project repository for persisting Project objects.

This repository handles saving, loading, updating, and deleting complete
story projects including all related data (story, characters, prompts).
"""

import json
from pathlib import Path
from typing import Optional, List
from dataclasses import asdict
from datetime import datetime

from src.models.project import Project, ProjectStatus
from src.models.story import Story, StoryMetadata, StoryPage
from src.models.character import Character, CharacterProfile
from src.models.image_prompt import ImagePrompt


class ProjectRepository:
    """
    Repository for managing Project persistence.

    Stores complete projects as JSON files in a local directory structure.
    Each project is stored as a separate JSON file with its ID as the filename.
    """

    def __init__(self, storage_dir: Path):
        """
        Initialize the repository with a storage directory.

        Args:
            storage_dir: Directory where project files will be stored
        """
        self.storage_dir = Path(storage_dir)
        self.projects_dir = self.storage_dir / "projects"

        # Create directories if they don't exist
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def save(self, project: Project) -> str:
        """
        Save a Project and return its ID.

        Args:
            project: The Project to save

        Returns:
            The project ID
        """
        project_file = self.projects_dir / f"{project.id}.json"

        # Convert project to dict with proper serialization
        project_data = self._serialize_project(project)

        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)

        return project.id

    def get(self, project_id: str) -> Optional[Project]:
        """
        Retrieve a Project by its ID.

        Args:
            project_id: The ID of the project to retrieve

        Returns:
            The Project if found, None otherwise
        """
        project_file = self.projects_dir / f"{project_id}.json"

        if not project_file.exists():
            return None

        with open(project_file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)

        return self._deserialize_project(project_data)

    def list_all(self) -> List[str]:
        """
        List all project IDs in the repository.

        Returns:
            List of project IDs
        """
        project_ids = []

        for project_file in self.projects_dir.glob("*.json"):
            project_id = project_file.stem  # filename without extension
            project_ids.append(project_id)

        return sorted(project_ids)

    def update(self, project_id: str, project: Project) -> None:
        """
        Update an existing project.

        Args:
            project_id: The ID of the project to update
            project: The new Project data

        Raises:
            ValueError: If the project doesn't exist
        """
        project_file = self.projects_dir / f"{project_id}.json"

        if not project_file.exists():
            raise ValueError(f"Project with id {project_id} not found")

        # Convert project to dict with proper serialization
        project_data = self._serialize_project(project)

        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)

    def delete(self, project_id: str) -> None:
        """
        Delete a project by its ID.

        Args:
            project_id: The ID of the project to delete

        Raises:
            ValueError: If the project doesn't exist
        """
        project_file = self.projects_dir / f"{project_id}.json"

        if not project_file.exists():
            raise ValueError(f"Project with id {project_id} not found")

        project_file.unlink()

    def _serialize_project(self, project: Project) -> dict:
        """
        Serialize a Project to a dictionary for JSON storage.

        Args:
            project: The Project to serialize

        Returns:
            Dictionary representation of the project
        """
        data = {
            'id': project.id,
            'name': project.name,
            'status': project.status.value,
            'story': self._serialize_story(project.story),
            'character_profiles': [
                asdict(profile) for profile in project.character_profiles
            ],
            'image_prompts': [
                self._serialize_image_prompt(prompt) for prompt in project.image_prompts
            ],
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat()
        }

        return data

    def _serialize_story(self, story: Story) -> dict:
        """Serialize a Story to a dictionary."""
        return {
            'id': story.id,
            'metadata': asdict(story.metadata),
            'pages': [asdict(page) for page in story.pages],
            'vocabulary': story.vocabulary,
            'characters': [asdict(char) for char in story.characters] if story.characters else None,
            'created_at': story.created_at.isoformat(),
            'updated_at': story.updated_at.isoformat()
        }

    def _serialize_image_prompt(self, prompt: ImagePrompt) -> dict:
        """Serialize an ImagePrompt to a dictionary."""
        return {
            'page_number': prompt.page_number,
            'scene_description': prompt.scene_description,
            'art_style': prompt.art_style,
            'characters': [asdict(profile) for profile in prompt.characters],
            'lighting': prompt.lighting,
            'mood': prompt.mood,
            'additional_details': prompt.additional_details
        }

    def _deserialize_project(self, data: dict) -> Project:
        """
        Deserialize a Project from a dictionary.

        Args:
            data: Dictionary representation of the project

        Returns:
            Reconstructed Project object
        """
        story = self._deserialize_story(data['story'])

        character_profiles = [
            CharacterProfile(**profile_data)
            for profile_data in data['character_profiles']
        ]

        image_prompts = [
            self._deserialize_image_prompt(prompt_data)
            for prompt_data in data['image_prompts']
        ]

        return Project(
            id=data['id'],
            name=data['name'],
            story=story,
            status=ProjectStatus(data['status']),
            character_profiles=character_profiles,
            image_prompts=image_prompts,
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )

    def _deserialize_story(self, data: dict) -> Story:
        """Deserialize a Story from a dictionary."""
        metadata = StoryMetadata(**data['metadata'])

        pages = [
            StoryPage(**page_data) for page_data in data['pages']
        ]

        characters = None
        if data.get('characters') is not None:
            characters = [
                Character(**char_data) for char_data in data['characters']
            ]

        return Story(
            id=data['id'],
            metadata=metadata,
            pages=pages,
            vocabulary=data['vocabulary'],
            characters=characters,
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )

    def _deserialize_image_prompt(self, data: dict) -> ImagePrompt:
        """Deserialize an ImagePrompt from a dictionary."""
        characters = [
            CharacterProfile(**profile_data)
            for profile_data in data['characters']
        ]

        return ImagePrompt(
            page_number=data['page_number'],
            scene_description=data['scene_description'],
            art_style=data['art_style'],
            characters=characters,
            lighting=data.get('lighting'),
            mood=data.get('mood'),
            additional_details=data.get('additional_details')
        )
