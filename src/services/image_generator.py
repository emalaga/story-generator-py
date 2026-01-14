"""
Image Generator Service for orchestrating image generation workflow.

This service coordinates the complete image generation process, including:
- Building image prompts with character profiles
- Generating images using AI image client
- Managing image URLs and prompts for story pages
"""

from typing import List

from src.ai.base_client import BaseImageClient
from src.domain.prompt_builder import PromptBuilder
from src.models.character import CharacterProfile
from src.models.story import Story


class ImageGeneratorService:
    """
    Orchestrates the complete image generation workflow.

    This service integrates AI image generation with prompt building to create
    consistent character illustrations for story pages.
    """

    def __init__(
        self,
        image_client: BaseImageClient,
        prompt_builder: PromptBuilder
    ):
        """
        Initialize the image generator service.

        Args:
            image_client: AI client for image generation
            prompt_builder: Builder for creating AI image prompts
        """
        self.image_client = image_client
        self.prompt_builder = prompt_builder

    async def generate_image_for_page(
        self,
        scene_description: str,
        character_profiles: List[CharacterProfile],
        art_style: str
    ) -> str:
        """
        Generate a single image for a story page.

        Args:
            scene_description: Description of the scene to illustrate (full page text)
            character_profiles: List of character profiles for consistency
            art_style: Artistic style (e.g., "cartoon", "watercolor")

        Returns:
            URL of the generated image

        Raises:
            Exception: If image generation fails
        """
        # Use AI to create a concise scene summary from full text
        # Pass character profiles so AI knows not to make assumptions
        scene_summary = await self.prompt_builder.summarize_scene(
            scene_description,
            character_profiles=character_profiles
        )

        # Build image prompt with the summarized scene
        prompt = self.prompt_builder.build_image_prompt(
            scene_summary,
            character_profiles,
            art_style
        )

        # Generate image using AI client
        image_url = await self.image_client.generate_image(prompt)

        return image_url

    async def generate_images_for_story(self, story: Story) -> Story:
        """
        Generate images for all pages in a story.

        Creates consistent illustrations for each story page using character
        profiles and the story's art style.

        Args:
            story: Complete story with pages and character profiles

        Returns:
            Updated story with image URLs and prompts on each page
        """
        # Get art style from story metadata
        art_style = story.metadata.art_style or "cartoon"

        # Get character profiles (may be empty list)
        character_profiles = story.characters or []

        # Generate image for each page
        for page in story.pages:
            try:
                # Use AI to create a concise scene summary from full page text
                # Pass character profiles so AI knows not to make assumptions
                scene_summary = await self.prompt_builder.summarize_scene(
                    page.text,
                    character_profiles=character_profiles
                )

                # Build image prompt with the summarized scene
                prompt = self.prompt_builder.build_image_prompt(
                    scene_summary,
                    character_profiles,
                    art_style
                )

                # Generate image
                image_url = await self.image_client.generate_image(prompt)

                # Update page with image URL and prompt
                page.image_url = image_url
                page.image_prompt = prompt

            except Exception:
                # If image generation fails for this page, skip it
                # but continue with other pages
                continue

        return story
