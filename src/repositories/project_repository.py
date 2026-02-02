"""
Project repository for persisting Project objects.

This repository handles saving, loading, updating, and deleting complete
story projects including all related data (story, characters, prompts).
"""

import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import asdict
from datetime import datetime

from src.models.project import Project, ProjectStatus
from src.models.story import Story, StoryMetadata, StoryPage, PDFOptions, CoverPage
from src.models.character import CharacterProfile
from src.models.image_prompt import ImagePrompt
from src.models.art_bible import ArtBible, CharacterReference


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
        self.images_dir = self.storage_dir / "images"

        # Create directories if they don't exist
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def get_project_images_dir(self, project_id: str) -> Path:
        """
        Get the images directory for a specific project.
        Creates the directory structure if it doesn't exist.

        Args:
            project_id: The project ID

        Returns:
            Path to the project's images directory
        """
        project_images_dir = self.images_dir / project_id
        project_images_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (project_images_dir / "art_bible").mkdir(exist_ok=True)
        (project_images_dir / "characters").mkdir(exist_ok=True)
        (project_images_dir / "pages").mkdir(exist_ok=True)

        return project_images_dir

    def save(self, project: Project) -> str:
        """
        Save a Project and return its ID.
        Creates the project directory structure for images.

        Args:
            project: The Project to save

        Returns:
            The project ID
        """
        # Create project directory structure
        self.get_project_images_dir(project.id)

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

    def list_all(self) -> List[Dict]:
        """
        List all projects with their metadata.

        Returns:
            List of dictionaries with project metadata (id, name, title, created_at, num_pages, language, user_prompt)
        """
        projects_metadata = []

        for project_file in self.projects_dir.glob("*.json"):
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)

                story_data = project_data.get('story', {})
                story_metadata = story_data.get('metadata', {})
                pages = story_data.get('pages', [])

                # Extract relevant metadata
                metadata = {
                    'id': project_data.get('id'),
                    'name': project_data.get('name'),
                    'title': story_metadata.get('title', 'Untitled'),
                    'num_pages': len(pages) if pages else story_metadata.get('num_pages', 0),
                    'language': story_metadata.get('language', 'Unknown'),
                    'user_prompt': story_metadata.get('user_prompt', ''),
                    'created_at': project_data.get('created_at'),
                    'updated_at': project_data.get('updated_at')
                }
                projects_metadata.append(metadata)
            except (json.JSONDecodeError, KeyError):
                # Skip corrupted project files
                continue

        # Sort by creation date (newest first)
        projects_metadata.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return projects_metadata

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
        Delete a project by its ID, including all associated images.

        Args:
            project_id: The ID of the project to delete

        Raises:
            ValueError: If the project doesn't exist
        """
        project_file = self.projects_dir / f"{project_id}.json"

        if not project_file.exists():
            raise ValueError(f"Project with id {project_id} not found")

        # Delete project JSON file
        project_file.unlink()

        # Delete project images directory if it exists
        project_images_dir = self.images_dir / project_id
        if project_images_dir.exists():
            shutil.rmtree(project_images_dir)

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
        # Helper to serialize datetime fields
        def serialize_datetime(dt):
            return dt.isoformat() if isinstance(dt, datetime) else dt

        # Serialize pages with proper datetime handling
        pages = []
        for page in story.pages:
            page_dict = asdict(page)
            if page_dict.get('image_generated_at'):
                page_dict['image_generated_at'] = serialize_datetime(page_dict['image_generated_at'])
            pages.append(page_dict)

        # Serialize art_bible with proper datetime handling
        art_bible_dict = None
        if story.art_bible:
            art_bible_dict = asdict(story.art_bible)
            if art_bible_dict.get('image_generated_at'):
                art_bible_dict['image_generated_at'] = serialize_datetime(art_bible_dict['image_generated_at'])

        # Serialize character_references with proper datetime handling
        character_refs = None
        if story.character_references:
            character_refs = []
            for char_ref in story.character_references:
                char_ref_dict = asdict(char_ref)
                if char_ref_dict.get('image_generated_at'):
                    char_ref_dict['image_generated_at'] = serialize_datetime(char_ref_dict['image_generated_at'])
                character_refs.append(char_ref_dict)

        # Serialize cover_page with proper datetime handling
        cover_page_dict = None
        if story.cover_page:
            cover_page_dict = asdict(story.cover_page)
            if cover_page_dict.get('image_generated_at'):
                cover_page_dict['image_generated_at'] = serialize_datetime(cover_page_dict['image_generated_at'])

        return {
            'id': story.id,
            'metadata': asdict(story.metadata),
            'pages': pages,
            'vocabulary': story.vocabulary,
            'characters': [asdict(char) for char in story.characters] if story.characters else None,
            'art_bible': art_bible_dict,
            'character_references': character_refs,
            'cover_page': cover_page_dict,
            'pdf_options': asdict(story.pdf_options) if story.pdf_options else None,
            'image_session_id': story.image_session_id,
            'text_model': story.text_model,
            'text_generated_at': serialize_datetime(story.text_generated_at) if story.text_generated_at else None,
            'text_edited_at': serialize_datetime(story.text_edited_at) if story.text_edited_at else None,
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
        # Helper to parse datetime from ISO string
        def parse_datetime(value):
            if value is None:
                return None
            if isinstance(value, datetime):
                return value
            return datetime.fromisoformat(value)

        metadata = StoryMetadata(**data['metadata'])

        # Deserialize pages with proper datetime handling
        pages = []
        for page_data in data['pages']:
            page_data = dict(page_data)  # Make a copy to avoid modifying original
            if 'image_generated_at' in page_data:
                page_data['image_generated_at'] = parse_datetime(page_data['image_generated_at'])
            pages.append(StoryPage(**page_data))

        characters = None
        if data.get('characters') is not None:
            characters = [
                CharacterProfile(**char_data) for char_data in data['characters']
            ]

        # Deserialize art_bible with proper datetime handling
        art_bible = None
        if data.get('art_bible') is not None:
            art_bible_data = dict(data['art_bible'])
            if 'image_generated_at' in art_bible_data:
                art_bible_data['image_generated_at'] = parse_datetime(art_bible_data['image_generated_at'])
            art_bible = ArtBible(**art_bible_data)

        # Deserialize character_references with proper datetime handling
        character_references = None
        if data.get('character_references') is not None:
            character_references = []
            for char_ref_data in data['character_references']:
                char_ref_data = dict(char_ref_data)
                if 'image_generated_at' in char_ref_data:
                    char_ref_data['image_generated_at'] = parse_datetime(char_ref_data['image_generated_at'])
                character_references.append(CharacterReference(**char_ref_data))

        pdf_options = None
        if data.get('pdf_options') is not None:
            pdf_options = PDFOptions(**data['pdf_options'])

        # Deserialize cover_page with proper datetime handling
        cover_page = None
        if data.get('cover_page') is not None:
            cover_page_data = dict(data['cover_page'])
            if 'image_generated_at' in cover_page_data:
                cover_page_data['image_generated_at'] = parse_datetime(cover_page_data['image_generated_at'])
            cover_page = CoverPage(**cover_page_data)

        return Story(
            id=data['id'],
            metadata=metadata,
            pages=pages,
            vocabulary=data.get('vocabulary', []),
            characters=characters,
            art_bible=art_bible,
            character_references=character_references,
            cover_page=cover_page,
            pdf_options=pdf_options,
            image_session_id=data.get('image_session_id'),
            text_model=data.get('text_model'),
            text_generated_at=parse_datetime(data.get('text_generated_at')),
            text_edited_at=parse_datetime(data.get('text_edited_at')),
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
