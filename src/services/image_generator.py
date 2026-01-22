"""
Image Generator Service for orchestrating image generation workflow.

This service coordinates the complete image generation process, including:
- Managing conversation sessions for visual consistency
- Building image prompts with character profiles
- Generating images using AI image client
- Managing image URLs and prompts for story pages
"""

from typing import List, Optional

from src.ai.gpt_image_client import GPTImageClient
from src.domain.prompt_builder import PromptBuilder
from src.models.character import CharacterProfile
from src.models.story import Story


class ImageGeneratorService:
    """
    Orchestrates the complete image generation workflow with session management.

    Uses conversation sessions to maintain visual consistency across all images
    for a story (art bible, character references, page illustrations).
    """

    def __init__(
        self,
        image_client: GPTImageClient,
        prompt_builder: PromptBuilder
    ):
        """
        Initialize the image generator service.

        Args:
            image_client: GPT-4o client for conversation-based image generation
            prompt_builder: Builder for creating AI image prompts
        """
        self.image_client = image_client
        self.prompt_builder = prompt_builder

    async def ensure_session(self, story: Story) -> str:
        """
        Ensure a valid conversation session exists for this story.

        If no valid session exists, rebuilds visual context by regenerating
        the art bible and character references.

        Args:
            story: The story to ensure a session for

        Returns:
            The session ID (response ID) for the story
        """
        # Check if we have a session ID and it's loaded in the client
        if story.image_session_id:
            # Load the session into the client if not already there
            if not self.image_client.get_session_id(story.id):
                self.image_client.set_session_id(story.id, story.image_session_id)

            # Validate the session is still usable
            if await self.image_client.validate_session(story.id):
                return story.image_session_id

        # No valid session - rebuild visual context
        session_id = await self.rebuild_visual_context(story)
        story.image_session_id = session_id
        return session_id

    async def rebuild_visual_context(self, story: Story) -> str:
        """
        Start fresh session and regenerate visual context (art bible + characters).

        This is called when loading a project with no active session or when
        the session has become invalid.

        Args:
            story: The story to rebuild context for

        Returns:
            The new session ID
        """
        # Clear any existing session
        self.image_client.clear_session(story.id)

        # Get art style from story metadata
        art_style = story.metadata.art_style or "cartoon"
        story_title = story.metadata.title or ""

        # Start new session with art style context
        session_id = await self.image_client.start_session(
            story.id,
            art_style,
            story_title
        )

        # If art bible exists with a prompt, regenerate it to establish style
        if story.art_bible and story.art_bible.prompt:
            try:
                image_url = await self.image_client.generate_image(
                    story.id,
                    story.art_bible.prompt,
                    size='1536x1024',
                    quality='high'
                )
                story.art_bible.image_url = image_url
            except Exception as e:
                print(f"Warning: Failed to regenerate art bible: {e}")

        # Regenerate each character reference to establish characters
        if story.character_references:
            for char_ref in story.character_references:
                if char_ref.prompt:
                    try:
                        image_url = await self.image_client.generate_image(
                            story.id,
                            char_ref.prompt,
                            size='1536x1024',
                            quality='high'
                        )
                        char_ref.image_url = image_url
                    except Exception as e:
                        print(f"Warning: Failed to regenerate character reference for {char_ref.character_name}: {e}")

        # Update session ID
        story.image_session_id = self.image_client.get_session_id(story.id)
        return story.image_session_id

    async def generate_art_bible_image(
        self,
        story: Story,
        prompt: str
    ) -> str:
        """
        Generate an art bible image for a story.

        This should be the first image generated for a story, establishing
        the visual style that all subsequent images will follow.

        Args:
            story: The story to generate art bible for
            prompt: The art bible prompt

        Returns:
            URL of the generated image
        """
        # Ensure session exists (start new if needed)
        await self.ensure_session(story)

        # Generate art bible image
        image_url = await self.image_client.generate_image(
            story.id,
            prompt,
            size='1536x1024',
            quality='high'
        )

        # Update session ID in story
        story.image_session_id = self.image_client.get_session_id(story.id)

        return image_url

    async def generate_character_reference_image(
        self,
        story: Story,
        prompt: str,
        character_name: str
    ) -> str:
        """
        Generate a character reference image within the story's session.

        This uses the conversation context, so it automatically maintains
        consistency with the art bible and any previously generated characters.

        Args:
            story: The story (for session context)
            prompt: The character reference prompt
            character_name: Name of the character

        Returns:
            URL of the generated image
        """
        # Ensure session exists
        await self.ensure_session(story)

        # Generate character reference - the conversation context knows about the art bible
        image_url = await self.image_client.generate_image(
            story.id,
            prompt,
            size='1536x1024',
            quality='high'
        )

        # Update session ID in story
        story.image_session_id = self.image_client.get_session_id(story.id)

        return image_url

    async def generate_image_for_page(
        self,
        story: Story,
        scene_description: str,
        character_profiles: List[CharacterProfile],
        art_style: str
    ) -> str:
        """
        Generate a single image for a story page using conversation context.

        The conversation session maintains consistency with the art bible
        and character references automatically.

        Args:
            story: The story (for session context)
            scene_description: Description of the scene to illustrate (full page text)
            character_profiles: List of character profiles
            art_style: Artistic style (e.g., "cartoon", "watercolor")

        Returns:
            URL of the generated image

        Raises:
            Exception: If image generation fails
        """
        # Ensure session exists
        await self.ensure_session(story)

        # Use AI to create a concise scene summary from full text
        scene_summary = await self.prompt_builder.summarize_scene(
            scene_description,
            character_profiles=character_profiles
        )

        # Build a simplified prompt (no need for detailed art bible/character descriptions
        # since the conversation context already knows about them)
        prompt = self.prompt_builder.build_conversation_prompt(
            scene_summary,
            character_profiles,
            art_style
        )

        # Generate image using conversation context
        image_url = await self.image_client.generate_image(
            story.id,
            prompt,
            size='1024x1024',
            quality='high'
        )

        # Update session ID in story
        story.image_session_id = self.image_client.get_session_id(story.id)

        return image_url

    async def generate_images_for_story(self, story: Story) -> Story:
        """
        Generate images for all pages in a story using conversation context.

        Uses the story's conversation session to maintain visual consistency
        across all page illustrations.

        Args:
            story: Complete story with pages and character profiles

        Returns:
            Updated story with image URLs and prompts on each page
        """
        # Ensure session exists
        await self.ensure_session(story)

        # Get art style from story metadata
        art_style = story.metadata.art_style or "cartoon"

        # Get character profiles (may be empty list)
        character_profiles = story.characters or []

        # Generate image for each page
        for page in story.pages:
            try:
                # Use AI to create a concise scene summary from full page text
                scene_summary = await self.prompt_builder.summarize_scene(
                    page.text,
                    character_profiles=character_profiles
                )

                # Build conversation-aware prompt
                prompt = self.prompt_builder.build_conversation_prompt(
                    scene_summary,
                    character_profiles,
                    art_style
                )

                # Generate image using conversation context
                image_url = await self.image_client.generate_image(
                    story.id,
                    prompt,
                    size='1024x1024',
                    quality='high'
                )

                # Update page with image URL and prompt
                page.image_url = image_url
                page.image_prompt = prompt

            except Exception as e:
                # If image generation fails for this page, skip it
                # but continue with other pages
                print(f"Warning: Failed to generate image for page {page.page_number}: {e}")
                continue

        # Update session ID in story
        story.image_session_id = self.image_client.get_session_id(story.id)

        return story
