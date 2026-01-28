"""
Image Generator Service for orchestrating image generation workflow.

This service coordinates the complete image generation process, including:
- Managing conversation sessions for visual consistency
- Building image prompts with character profiles
- Generating images using AI image client
- Managing image URLs and prompts for story pages
"""

import logging
from typing import List, Optional

from src.ai.gpt_image_client import GPTImageClient
from src.domain.prompt_builder import PromptBuilder
from src.models.character import CharacterProfile
from src.models.story import Story

logger = logging.getLogger(__name__)


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
        the art bible and character references. This only happens once per
        story load - subsequent calls reuse the existing session.

        Args:
            story: The story to ensure a session for

        Returns:
            The session ID (response ID) for the story
        """
        print(f"[ImageGenerator] ensure_session called for story_id={story.id}", flush=True)
        print(f"[ImageGenerator]   story.image_session_id={story.image_session_id}", flush=True)
        logger.info(f"ensure_session called for story {story.id}")

        # First check: if context is already initialized for this story, just return existing session
        if self.image_client.is_context_initialized(story.id):
            session_id = self.image_client.get_session_id(story.id)
            if session_id:
                print(f"[ImageGenerator]   Context already initialized, using existing session: {session_id}", flush=True)
                logger.info(f"Context already initialized for story {story.id}, reusing session")
                return session_id

        # Check if we have a session ID and it's loaded in the client
        if story.image_session_id:
            print(f"[ImageGenerator]   Story has existing session_id, checking if loaded in client...", flush=True)
            # Load the session into the client if not already there
            if not self.image_client.get_session_id(story.id):
                print(f"[ImageGenerator]   Session not in client, loading it...", flush=True)
                self.image_client.set_session_id(story.id, story.image_session_id)

            # Validate the session is still usable
            print(f"[ImageGenerator]   Validating session...", flush=True)
            if await self.image_client.validate_session(story.id):
                print(f"[ImageGenerator]   Session is valid, marking context as initialized", flush=True)
                self.image_client.mark_context_initialized(story.id)
                return story.image_session_id
            print(f"[ImageGenerator]   Session validation failed", flush=True)

        # No valid session - rebuild visual context (this should only happen once per story load)
        print(f"[ImageGenerator]   No valid session, rebuilding visual context...", flush=True)
        logger.info(f"No valid session for story {story.id}, rebuilding visual context")
        session_id = await self.rebuild_visual_context(story)
        story.image_session_id = session_id

        # Mark context as initialized so we don't rebuild again for subsequent pages
        self.image_client.mark_context_initialized(story.id)
        print(f"[ImageGenerator]   Visual context rebuilt, new session_id={session_id}, marked as initialized", flush=True)
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
        print(f"[ImageGenerator] rebuild_visual_context called for story {story.id}", flush=True)
        logger.info(f"Rebuilding visual context for story {story.id}")

        # Clear any existing session
        print(f"[ImageGenerator]   Clearing existing session...", flush=True)
        self.image_client.clear_session(story.id)

        # Get art style from story metadata
        art_style = story.metadata.art_style or "cartoon"
        story_title = story.metadata.title or ""
        print(f"[ImageGenerator]   art_style={art_style}, title={story_title}", flush=True)

        # Start new session with art style context
        print(f"[ImageGenerator]   Starting new session...", flush=True)
        logger.info(f"Starting new session with art_style={art_style}, title={story_title}")
        try:
            session_id = await self.image_client.start_session(
                story.id,
                art_style,
                story_title
            )
            print(f"[ImageGenerator]   New session started with ID: {session_id}", flush=True)
            logger.info(f"New session started with ID: {session_id}")
        except Exception as e:
            print(f"[ImageGenerator]   FAILED to start session: {type(e).__name__}: {e}", flush=True)
            raise

        # If art bible exists with a prompt, regenerate it to establish style
        if story.art_bible and story.art_bible.prompt:
            print(f"[ImageGenerator]   Art bible exists, regenerating...", flush=True)
            logger.info(f"Regenerating art bible (prompt length: {len(story.art_bible.prompt)})")
            try:
                image_url = await self.image_client.generate_image(
                    story.id,
                    story.art_bible.prompt,
                    size='1536x1024',
                    quality='high'
                )
                story.art_bible.image_url = image_url
                print(f"[ImageGenerator]   Art bible regenerated successfully", flush=True)
                logger.info(f"Art bible regenerated successfully")
            except Exception as e:
                print(f"[ImageGenerator]   Art bible regeneration failed: {e}", flush=True)
                logger.warning(f"Failed to regenerate art bible: {e}")
        else:
            print(f"[ImageGenerator]   No art bible prompt to regenerate", flush=True)
            logger.info("No art bible prompt to regenerate")

        # Regenerate each character reference to establish characters
        if story.character_references:
            print(f"[ImageGenerator]   Regenerating {len(story.character_references)} character references...", flush=True)
            logger.info(f"Regenerating {len(story.character_references)} character references")
            for char_ref in story.character_references:
                if char_ref.prompt:
                    print(f"[ImageGenerator]   Regenerating character: {char_ref.character_name}...", flush=True)
                    logger.info(f"Regenerating character reference for {char_ref.character_name}")
                    try:
                        image_url = await self.image_client.generate_image(
                            story.id,
                            char_ref.prompt,
                            size='1536x1024',
                            quality='high'
                        )
                        char_ref.image_url = image_url
                        print(f"[ImageGenerator]   Character {char_ref.character_name} regenerated", flush=True)
                        logger.info(f"Character reference for {char_ref.character_name} regenerated")
                    except Exception as e:
                        print(f"[ImageGenerator]   Character {char_ref.character_name} failed: {e}", flush=True)
                        logger.warning(f"Failed to regenerate character reference for {char_ref.character_name}: {e}")
        else:
            logger.info("No character references to regenerate")

        # Update session ID
        story.image_session_id = self.image_client.get_session_id(story.id)
        logger.info(f"Visual context rebuild complete, session_id: {story.image_session_id}")
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
        art_style: str,
        size: str = '1024x1024',
        quality: str = 'low'
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
            size: Image size (default: 1024x1024)
            quality: Image quality/detail level (default: low)

        Returns:
            URL of the generated image

        Raises:
            Exception: If image generation fails
        """
        logger.info(f"Generating image for page, story_id={story.id}, art_style={art_style}, size={size}, quality={quality}")
        logger.info(f"Scene description length: {len(scene_description)}, characters: {len(character_profiles)}")

        # Ensure session exists
        logger.info("Ensuring session exists...")
        await self.ensure_session(story)
        logger.info(f"Session ensured, session_id: {story.image_session_id}")

        # Use AI to create a concise scene summary from full text
        logger.info("Summarizing scene...")
        scene_summary = await self.prompt_builder.summarize_scene(
            scene_description,
            character_profiles=character_profiles
        )
        logger.info(f"Scene summary: {scene_summary[:100]}..." if len(scene_summary) > 100 else f"Scene summary: {scene_summary}")

        # Build a simplified prompt (no need for detailed art bible/character descriptions
        # since the conversation context already knows about them)
        prompt = self.prompt_builder.build_conversation_prompt(
            scene_summary,
            character_profiles,
            art_style
        )
        logger.info(f"Built prompt (length: {len(prompt)})")

        # Generate image using conversation context
        logger.info(f"Generating image with GPT-4o (size={size}, quality={quality})...")
        image_url = await self.image_client.generate_image(
            story.id,
            prompt,
            size=size,
            quality=quality
        )
        logger.info(f"Image generated, URL length: {len(image_url) if image_url else 0}")

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
