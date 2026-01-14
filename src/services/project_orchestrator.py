"""
Project Orchestrator for coordinating end-to-end story generation workflow.

This orchestrator manages the complete pipeline from project creation through
story generation, character extraction, and image generation.
"""

import uuid
from typing import Optional

from src.models.project import Project, ProjectStatus
from src.models.story import StoryMetadata
from src.repositories.project_repository import ProjectRepository
from src.services.image_generator import ImageGeneratorService
from src.services.story_generator import StoryGeneratorService


class ProjectOrchestrator:
    """
    Orchestrates the complete end-to-end story generation workflow.

    This high-level service coordinates story generation, image generation,
    and project persistence, managing the entire pipeline from start to finish.
    """

    def __init__(
        self,
        story_generator: StoryGeneratorService,
        image_generator: ImageGeneratorService,
        project_repository: ProjectRepository
    ):
        """
        Initialize the project orchestrator.

        Args:
            story_generator: Service for generating stories
            image_generator: Service for generating images
            project_repository: Repository for persisting projects
        """
        self.story_generator = story_generator
        self.image_generator = image_generator
        self.project_repository = project_repository

    async def create_project(
        self,
        metadata: StoryMetadata,
        theme: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> Project:
        """
        Create a complete new story project with text and images.

        Coordinates the full workflow:
        1. Generate story text with characters
        2. Generate images for all pages
        3. Save project to repository

        Args:
            metadata: Story metadata with parameters
            theme: Optional theme or moral for the story
            custom_prompt: Optional custom story idea

        Returns:
            Complete Project with story and images

        Raises:
            Exception: If any generation step fails
        """
        # Step 1: Generate story with characters
        story = await self.story_generator.generate_story(
            metadata,
            theme=theme,
            custom_prompt=custom_prompt
        )

        # Step 2: Generate images for all story pages
        story = await self.image_generator.generate_images_for_story(story)

        # Step 3: Create project with generated story
        project = Project(
            id=str(uuid.uuid4()),
            name=metadata.title,
            story=story,
            status=ProjectStatus.COMPLETED,
            character_profiles=story.characters or [],
            image_prompts=[]  # Image prompts are stored on pages
        )

        # Step 4: Save project to repository
        await self.project_repository.save_project(project)

        return project

    async def regenerate_story(
        self,
        project_id: str,
        metadata: StoryMetadata,
        theme: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> Project:
        """
        Regenerate story for an existing project.

        Creates a new story with new text and images, replacing the old one.

        Args:
            project_id: ID of existing project
            metadata: Story metadata with parameters
            theme: Optional theme or moral
            custom_prompt: Optional custom story idea

        Returns:
            Updated Project with new story

        Raises:
            Exception: If generation or update fails
        """
        # Get existing project
        project = await self.project_repository.get_project(project_id)

        # Generate new story
        story = await self.story_generator.generate_story(
            metadata,
            theme=theme,
            custom_prompt=custom_prompt
        )

        # Generate images for new story
        story = await self.image_generator.generate_images_for_story(story)

        # Update project with new story
        project.story = story

        # Save updated project
        await self.project_repository.update_project(project)

        return project

    async def regenerate_images(self, project_id: str) -> Project:
        """
        Regenerate images for an existing project's story.

        Keeps the story text but creates new images for all pages.

        Args:
            project_id: ID of existing project

        Returns:
            Updated Project with new images

        Raises:
            Exception: If image generation or update fails
        """
        # Get existing project
        project = await self.project_repository.get_project(project_id)

        # Generate new images for existing story
        story = await self.image_generator.generate_images_for_story(project.story)

        # Update project with re-imaged story
        project.story = story

        # Save updated project
        await self.project_repository.update_project(project)

        return project

    async def get_project(self, project_id: str) -> Project:
        """
        Retrieve an existing project.

        Args:
            project_id: ID of project to retrieve

        Returns:
            Project with story and images

        Raises:
            Exception: If project not found
        """
        return await self.project_repository.get_project(project_id)
