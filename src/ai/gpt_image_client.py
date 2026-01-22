"""
GPT-4o Conversation Image Client for generating images using OpenAI's Responses API.

This client uses conversation sessions with GPT-4o to generate consistent
illustrations for story pages. All images for a story (art bible, characters,
pages) are generated within the same conversation thread, allowing GPT-4o to
maintain visual consistency through context.
"""

import asyncio
import base64
import os
from typing import Optional, Dict, Any
from openai import AsyncOpenAI

from src.ai.base_client import BaseImageClient
from src.models.config import OpenAIConfig


class GPTImageClient(BaseImageClient):
    """
    Client for OpenAI GPT-4o image generation using conversation sessions.

    Uses the responses.create API to maintain conversation context across
    multiple image generations, enabling visual consistency without passing
    reference images explicitly.
    """

    def __init__(self, config: OpenAIConfig, model: str = "gpt-4o"):
        """
        Initialize the GPT-4o image client.

        Args:
            config: OpenAIConfig with API key and timeout
            model: Model to use (default: "gpt-4o")
        """
        self.config = config
        self.api_key = config.api_key or os.getenv('OPENAI_API_KEY', '')
        self.model = model
        self.timeout = config.timeout

        # Initialize async OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)

        # Session state: story_id -> last response_id
        self._sessions: Dict[str, str] = {}

    def get_session_id(self, story_id: str) -> Optional[str]:
        """Get the current session (response) ID for a story."""
        return self._sessions.get(story_id)

    def set_session_id(self, story_id: str, response_id: str):
        """Set the session ID for a story (used when loading from persistence)."""
        self._sessions[story_id] = response_id

    def clear_session(self, story_id: str):
        """Clear the session for a story (used when starting a new story)."""
        if story_id in self._sessions:
            del self._sessions[story_id]

    async def start_session(self, story_id: str, art_style: str, story_title: str = "") -> str:
        """
        Start a new conversation session for a story.

        This creates the initial context that all subsequent image generations
        will build upon.

        Args:
            story_id: Unique identifier for the story
            art_style: The art style to use (e.g., "cartoon", "watercolor")
            story_title: Optional title of the story

        Returns:
            The response ID to use for continuing the conversation
        """
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY in your .env file"
            )

        # Create initial system context
        system_prompt = f"""You are an expert children's book illustrator creating illustrations for a story.

Art Style: {art_style}
{"Story: " + story_title if story_title else ""}

IMPORTANT GUIDELINES:
- All images must maintain perfect visual consistency throughout the story
- Characters must look EXACTLY the same in every illustration
- The art style, colors, and techniques must remain consistent
- When I reference "the art bible" or "previously created characters", use them exactly as designed

You will help me create:
1. An Art Bible - establishing the visual style
2. Character Reference Sheets - detailed character designs
3. Page Illustrations - scenes from the story

Respond briefly to acknowledge you're ready, then wait for my requests."""

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = await self.client.responses.create(
                    model=self.model,
                    input=system_prompt
                )

                # Store the response ID as the session ID
                self._sessions[story_id] = response.id
                return response.id

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Session start error (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    raise Exception(f"Failed to start session after {max_retries} attempts: {str(e)}")

    async def generate_image(
        self,
        story_id: str,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        **kwargs
    ) -> str:
        """
        Generate an image within a story's conversation session.

        Args:
            story_id: The story ID to use for session context
            prompt: The prompt describing the image to generate
            size: Image size ("1024x1024", "1024x1536", "1536x1024", "auto")
            quality: Image quality ("low", "medium", "high")
            **kwargs: Additional parameters

        Returns:
            URL to the generated image

        Raises:
            ValueError: If no session exists for the story
            Exception: If image generation fails
        """
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY in your .env file"
            )

        # Get the previous response ID for conversation continuity
        previous_response_id = self._sessions.get(story_id)

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Build the request
                request_params = {
                    "model": self.model,
                    "input": prompt,
                    "tools": [{"type": "image_generation", "size": size, "quality": quality}]
                }

                # Add conversation context if we have a previous response
                if previous_response_id:
                    request_params["previous_response_id"] = previous_response_id

                response = await self.client.responses.create(**request_params)

                # Update session with new response ID
                self._sessions[story_id] = response.id

                # Extract image URL from response
                image_url = self._extract_image_url(response)
                if image_url:
                    return image_url

                raise ValueError("No image was generated in the response")

            except Exception as e:
                error_str = str(e)

                # Check if it's a retryable error (server errors, timeouts)
                if any(x in error_str.lower() for x in ['timeout', 'server', '500', '502', '503', '504']):
                    if attempt < max_retries - 1:
                        print(f"Image generation error (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue

                raise Exception(f"Image generation failed: {error_str}")

    def _extract_image_url(self, response) -> Optional[str]:
        """
        Extract the image URL or base64 data from a responses.create response.

        The response structure contains output items, and we need to find
        the image generation result. The result may be a URL or base64 data.
        If base64 data is returned, it's converted to a data URL for consistency.
        """
        if not hasattr(response, 'output') or not response.output:
            return None

        for item in response.output:
            # Check for image generation result
            if hasattr(item, 'type') and item.type == 'image_generation_call':
                if hasattr(item, 'result') and item.result:
                    result = item.result
                    # Check if it's base64 data (not a URL)
                    if result and not result.startswith('http') and not result.startswith('data:'):
                        # It's raw base64 data, convert to data URL
                        return f"data:image/png;base64,{result}"
                    return result
            # Alternative structure: direct image URL in content
            if hasattr(item, 'content'):
                for content_item in item.content:
                    if hasattr(content_item, 'type') and content_item.type == 'image':
                        if hasattr(content_item, 'image_url'):
                            return content_item.image_url.url
                        elif hasattr(content_item, 'url'):
                            return content_item.url
                        elif hasattr(content_item, 'source') and hasattr(content_item.source, 'data'):
                            # Base64 data in source.data
                            return f"data:image/png;base64,{content_item.source.data}"

        return None

    async def validate_session(self, story_id: str) -> bool:
        """
        Check if a session is still valid.

        Args:
            story_id: The story ID to check

        Returns:
            True if session exists and is valid, False otherwise
        """
        session_id = self._sessions.get(story_id)
        if not session_id:
            return False

        # For now, we assume if we have a session ID, it's valid
        # OpenAI's conversation sessions don't expire quickly
        return True

    # Legacy method for backward compatibility
    async def generate_image_legacy(self, prompt: str, **kwargs) -> str:
        """
        Legacy method that generates an image without session context.
        Use generate_image() with story_id for conversation-based generation.
        """
        # Create a temporary story ID for this one-off generation
        temp_story_id = f"_temp_{id(prompt)}"
        try:
            # Start a minimal session
            await self.start_session(temp_story_id, "illustration", "")
            return await self.generate_image(temp_story_id, prompt, **kwargs)
        finally:
            self.clear_session(temp_story_id)
