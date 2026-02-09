"""
Image Generator Service for orchestrating image generation workflow.

This service coordinates the complete image generation process, including:
- Managing conversation sessions for visual consistency
- Building image prompts with character profiles
- Generating images using AI image client
- Managing image URLs and prompts for story pages
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

from src.ai.gpt_image_client import GPTImageClient
from src.domain.prompt_builder import PromptBuilder
from src.models.character import CharacterProfile
from src.models.story import Story
from src.utils.ai_logger import log_ai_call

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
        prompt_builder: PromptBuilder,
        images_dir: Optional[Union[str, Path]] = None
    ):
        """
        Initialize the image generator service.

        Args:
            image_client: GPT-4o client for conversation-based image generation
            prompt_builder: Builder for creating AI image prompts
            images_dir: Base directory for stored images (for resolving relative paths)
        """
        self.image_client = image_client
        self.prompt_builder = prompt_builder
        self.images_dir = Path(images_dir) if images_dir else None

    def _resolve_image_path(self, relative_path: str) -> str:
        """
        Resolve a relative image path to a full filesystem path.

        Args:
            relative_path: Path like 'images/project-id/art_bible/file.png'

        Returns:
            Full path to the image file
        """
        if not relative_path:
            return relative_path

        # Strip leading slash
        path = relative_path.lstrip('/')

        # If we have an images_dir, resolve the path
        if self.images_dir:
            # Strip 'images/' prefix since images_dir already points to images folder
            if path.startswith('images/'):
                path = path[7:]  # Remove "images/" prefix
            full_path = str(self.images_dir / path)
            return full_path

        # Fallback: return as-is
        return path

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
        Start fresh session and load existing visual context (art bible + characters).

        This loads existing images into the session WITHOUT regenerating them,
        so the AI can reference them for visual consistency in future generations.

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
            session_id, session_cost = await self.image_client.start_session(
                story.id,
                art_style,
                story_title
            )
            print(f"[ImageGenerator]   New session started with ID: {session_id}, cost: ${session_cost:.6f}", flush=True)
            logger.info(f"New session started with ID: {session_id}")

            # Log the session start
            log_ai_call(
                call_type='session',
                model='gpt-4o',
                prompt=f"Start visual consistency session for '{story_title}' with art style '{art_style}'",
                payload={'art_style': art_style, 'story_title': story_title},
                response_summary=f'Session started: {session_id[:20]}...',
                cost=session_cost,
                project_id=story.id
            )
        except Exception as e:
            print(f"[ImageGenerator]   FAILED to start session: {type(e).__name__}: {e}", flush=True)
            log_ai_call(
                call_type='session',
                model='gpt-4o',
                prompt=f"Start visual consistency session for '{story_title}'",
                error=str(e),
                project_id=story.id
            )
            raise

        # Load existing art bible image into session (if it exists)
        if story.art_bible and story.art_bible.local_image_path:
            print(f"[ImageGenerator]   Loading existing art bible image into session...", flush=True)
            logger.info(f"Loading existing art bible image: {story.art_bible.local_image_path}")

            # Resolve the image path to full filesystem path
            art_bible_full_path = self._resolve_image_path(story.art_bible.local_image_path)
            print(f"[ImageGenerator]   Resolved path: {art_bible_full_path}", flush=True)

            try:
                description = f"Art style: {art_style}. Story: {story_title}."
                if story.art_bible.prompt:
                    description += f" Original prompt: {story.art_bible.prompt[:200]}"

                _ref_id, ref_cost = await self.image_client.load_reference_image(
                    story.id,
                    art_bible_full_path,
                    description,
                    reference_type="art_bible"
                )
                print(f"[ImageGenerator]   Art bible loaded into session successfully, cost: ${ref_cost:.6f}", flush=True)
                logger.info(f"Art bible loaded into session successfully")

                # Log the art bible load
                log_ai_call(
                    call_type='session',
                    model='gpt-4o',
                    prompt=f"Load existing art bible image into session",
                    payload={'image_path': story.art_bible.local_image_path, 'action': 'load_reference'},
                    response_summary=f'Loaded art bible into session (no new image generated)',
                    cost=ref_cost,
                    project_id=story.id,
                    metadata={'reference_type': 'art_bible'}
                )
            except Exception as e:
                print(f"[ImageGenerator]   Failed to load art bible: {e}", flush=True)
                logger.warning(f"Failed to load art bible into session: {e}")
        else:
            print(f"[ImageGenerator]   No art bible image to load", flush=True)
            logger.info("No art bible image to load")

        # Load existing character reference images into session
        if story.character_references:
            print(f"[ImageGenerator]   Loading {len(story.character_references)} character references into session...", flush=True)
            logger.info(f"Loading {len(story.character_references)} character references into session")
            for char_ref in story.character_references:
                if char_ref.local_image_path:
                    print(f"[ImageGenerator]   Loading character: {char_ref.character_name}...", flush=True)
                    logger.info(f"Loading character reference for {char_ref.character_name}")

                    # Resolve the image path to full filesystem path
                    char_full_path = self._resolve_image_path(char_ref.local_image_path)
                    print(f"[ImageGenerator]   Resolved path: {char_full_path}", flush=True)

                    try:
                        description = f"Character name: {char_ref.character_name}."
                        if char_ref.physical_description:
                            description += f" {char_ref.physical_description}"
                        if char_ref.clothing:
                            description += f" Wearing: {char_ref.clothing}"
                        if char_ref.distinctive_features:
                            description += f" Features: {char_ref.distinctive_features}"

                        _ref_id, ref_cost = await self.image_client.load_reference_image(
                            story.id,
                            char_full_path,
                            description,
                            reference_type="character"
                        )
                        print(f"[ImageGenerator]   Character {char_ref.character_name} loaded, cost: ${ref_cost:.6f}", flush=True)
                        logger.info(f"Character reference for {char_ref.character_name} loaded")

                        # Log the character load
                        log_ai_call(
                            call_type='session',
                            model='gpt-4o',
                            prompt=f"Load existing character reference image for '{char_ref.character_name}'",
                            payload={'image_path': char_ref.local_image_path, 'character_name': char_ref.character_name, 'action': 'load_reference'},
                            response_summary=f'Loaded character "{char_ref.character_name}" into session (no new image generated)',
                            cost=ref_cost,
                            project_id=story.id,
                            metadata={'reference_type': 'character', 'character_name': char_ref.character_name}
                        )
                    except Exception as e:
                        print(f"[ImageGenerator]   Character {char_ref.character_name} failed to load: {e}", flush=True)
                        logger.warning(f"Failed to load character reference for {char_ref.character_name}: {e}")
        else:
            logger.info("No character references to load")

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
