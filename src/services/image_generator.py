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
        art_style: str,
        art_bible=None,
        character_references=None
    ) -> str:
        """
        Generate a single image for a story page with art bible and character reference guidance.

        Args:
            scene_description: Description of the scene to illustrate (full page text)
            character_profiles: List of character profiles for consistency
            art_style: Artistic style (e.g., "cartoon", "watercolor")
            art_bible: Optional art bible with style guidelines
            character_references: Optional character references for consistency

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

        # Build image prompt with the summarized scene, art bible, and character references
        prompt = self.prompt_builder.build_image_prompt(
            scene_summary,
            character_profiles,
            art_style,
            art_bible=art_bible,
            character_references=character_references
        )

        # Generate image using detailed text prompts
        # Note: OpenAI's API doesn't support passing reference images for style consistency.
        # The /images/edits endpoint is for editing existing images with masks, not for
        # using reference images to guide new generation.
        # Instead, we rely on very detailed text prompts that include art bible style
        # constraints and character descriptions (already built into the prompt above).
        image_url = await self.image_client.generate_image(prompt)

        return image_url

    async def generate_images_for_story(self, story: Story) -> Story:
        """
        Generate images for all pages in a story with art bible and character reference guidance.

        Creates consistent illustrations for each story page using character
        profiles, art bible style guidelines, and character references.

        Args:
            story: Complete story with pages, character profiles, art bible, and character references

        Returns:
            Updated story with image URLs and prompts on each page
        """
        # Get art style from story metadata
        art_style = story.metadata.art_style or "cartoon"

        # Get character profiles (may be empty list)
        character_profiles = story.characters or []

        # Get art bible and character references (may be None)
        art_bible = story.art_bible
        character_references = story.character_references

        # Generate image for each page
        for page in story.pages:
            try:
                # Use AI to create a concise scene summary from full page text
                # Pass character profiles so AI knows not to make assumptions
                scene_summary = await self.prompt_builder.summarize_scene(
                    page.text,
                    character_profiles=character_profiles
                )

                # Build image prompt with the summarized scene, art bible, and character references
                prompt = self.prompt_builder.build_image_prompt(
                    scene_summary,
                    character_profiles,
                    art_style,
                    art_bible=art_bible,
                    character_references=character_references
                )

                # Generate image using detailed text prompts
                # Note: OpenAI's API doesn't support passing reference images for style consistency.
                # Instead, we rely on detailed text prompts with art bible and character constraints.
                image_url = await self.image_client.generate_image(prompt)

                # Update page with image URL and prompt
                page.image_url = image_url
                page.image_prompt = prompt

            except Exception:
                # If image generation fails for this page, skip it
                # but continue with other pages
                continue

        return story
