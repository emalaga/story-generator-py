"""
GPT-4o Conversation Image Client for generating images using OpenAI's Responses API.

This client uses conversation sessions with GPT-4o to generate consistent
illustrations for story pages. All images for a story (art bible, characters,
pages) are generated within the same conversation thread, allowing GPT-4o to
maintain visual consistency through context.
"""

import asyncio
import base64
import logging
import os
from typing import Optional, Dict, Any, Union, Tuple
import httpx
from openai import AsyncOpenAI

from src.ai.base_client import BaseImageClient
from src.models.config import OpenAIConfig
from src.utils.image_cost_calculator import estimate_gpt_image_cost, extract_usage_from_response

logger = logging.getLogger(__name__)


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
        # Use a generous timeout for image generation (default 300 seconds = 5 minutes)
        # Image generation can take 2-4 minutes with GPT-4o
        self.timeout = max(config.timeout, 300) if config.timeout else 300

        # Initialize async OpenAI client with explicit timeout
        # The timeout applies to all HTTP requests made by the client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=httpx.Timeout(self.timeout, connect=60.0)
        )

        # Session state: story_id -> last response_id
        self._sessions: Dict[str, str] = {}

        # Track which stories have had their visual context initialized in this session
        # This prevents repeated rebuilds when generating multiple pages
        self._context_initialized: Dict[str, bool] = {}

    def get_session_id(self, story_id: str) -> Optional[str]:
        """Get the current session (response) ID for a story."""
        return self._sessions.get(story_id)

    def set_session_id(self, story_id: str, response_id: str):
        """Set the session ID for a story (used when loading from persistence)."""
        self._sessions[story_id] = response_id

    def is_context_initialized(self, story_id: str) -> bool:
        """Check if visual context (art bible + characters) has been initialized for this story."""
        return self._context_initialized.get(story_id, False)

    def mark_context_initialized(self, story_id: str):
        """Mark that visual context has been initialized for this story."""
        self._context_initialized[story_id] = True

    def clear_session(self, story_id: str):
        """Clear the session for a story (used when starting a new story)."""
        if story_id in self._sessions:
            del self._sessions[story_id]
        if story_id in self._context_initialized:
            del self._context_initialized[story_id]

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
        print(f"[GPTImageClient] start_session called: story_id={story_id}, art_style={art_style}", flush=True)
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

        print(f"[GPTImageClient]   About to call responses.create for session start...", flush=True)
        for attempt in range(max_retries):
            try:
                print(f"[GPTImageClient]   Attempt {attempt + 1}/{max_retries}...", flush=True)
                response = await self.client.responses.create(
                    model=self.model,
                    input=system_prompt
                )
                print(f"[GPTImageClient]   Session started, response.id={response.id}", flush=True)

                # Store the response ID as the session ID
                self._sessions[story_id] = response.id
                return response.id

            except Exception as e:
                print(f"[GPTImageClient]   Session start error: {type(e).__name__}: {e}", flush=True)
                if attempt < max_retries - 1:
                    print(f"[GPTImageClient]   Retrying in {retry_delay}s...", flush=True)
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    raise Exception(f"Failed to start session after {max_retries} attempts: {str(e)}")

    async def load_reference_image(
        self,
        story_id: str,
        image_path: str,
        description: str,
        reference_type: str = "reference"
    ) -> str:
        """
        Load an existing image into the session context without generating a new one.

        This adds the image to the conversation so the model can reference it
        for visual consistency in future generations.

        Args:
            story_id: The story ID for session context
            image_path: Path to the local image file
            description: Description of what this image represents
            reference_type: Type of reference ("art_bible" or "character")

        Returns:
            The updated response ID

        Raises:
            ValueError: If no session exists or image not found
            Exception: If loading fails
        """
        import base64
        import os

        print(f"[GPTImageClient] load_reference_image called:", flush=True)
        print(f"[GPTImageClient]   story_id={story_id}", flush=True)
        print(f"[GPTImageClient]   image_path={image_path}", flush=True)
        print(f"[GPTImageClient]   reference_type={reference_type}", flush=True)

        if not self.api_key:
            raise ValueError("OpenAI API key not found")

        previous_response_id = self._sessions.get(story_id)
        print(f"[GPTImageClient]   previous_response_id={previous_response_id}", flush=True)
        if not previous_response_id:
            raise ValueError(f"No session exists for story {story_id}. Start a session first.")

        # Load the image from disk
        # Don't strip leading / from absolute paths
        full_path = image_path
        print(f"[GPTImageClient]   full_path={full_path}", flush=True)
        if not os.path.exists(full_path):
            print(f"[GPTImageClient]   ERROR: Image file not found!", flush=True)
            raise ValueError(f"Image not found: {full_path}")

        with open(full_path, 'rb') as f:
            image_data = f.read()

        image_size_kb = len(image_data) / 1024
        print(f"[GPTImageClient]   Image loaded: {image_size_kb:.1f} KB", flush=True)

        # Determine mime type
        if full_path.lower().endswith('.png'):
            mime_type = 'image/png'
        elif full_path.lower().endswith('.gif'):
            mime_type = 'image/gif'
        elif full_path.lower().endswith('.webp'):
            mime_type = 'image/webp'
        else:
            mime_type = 'image/jpeg'

        base64_data = base64.b64encode(image_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_data}"
        print(f"[GPTImageClient]   base64 data length: {len(base64_data)} chars", flush=True)
        print(f"[GPTImageClient]   mime_type: {mime_type}", flush=True)

        print(f"[GPTImageClient] load_reference_image: {reference_type} for story {story_id}", flush=True)
        logger.info(f"Loading {reference_type} reference image into session: {image_path}")

        # Build input with image and description
        # Use the standard message format (not input_text/input_image which requires image_generation tool)
        if reference_type == "art_bible":
            context_text = f"This is the ART BIBLE for this story. It defines the visual style, color palette, and artistic approach. All images generated for this story must match this style exactly. Description: {description}"
        else:
            context_text = f"This is a CHARACTER REFERENCE image. {description}. When this character appears in any scene, they must look exactly like this - same face, hair, clothing, and all distinctive features."

        input_content = [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": context_text},
                    {"type": "input_image", "image_url": data_url}
                ]
            }
        ]

        max_retries = 3
        retry_delay = 2

        print(f"[GPTImageClient]   Sending reference image to OpenAI API...", flush=True)
        for attempt in range(max_retries):
            try:
                print(f"[GPTImageClient]   API call attempt {attempt + 1}/{max_retries}...", flush=True)
                response = await self.client.responses.create(
                    model=self.model,
                    input=input_content,
                    previous_response_id=previous_response_id
                )

                # Update session with new response ID
                self._sessions[story_id] = response.id
                print(f"[GPTImageClient]   SUCCESS! Reference image loaded", flush=True)
                print(f"[GPTImageClient]   New response_id={response.id}", flush=True)

                # Log the model's response text if any
                if hasattr(response, 'output') and response.output:
                    for item in response.output:
                        if hasattr(item, 'content'):
                            for content in item.content:
                                if hasattr(content, 'text'):
                                    print(f"[GPTImageClient]   Model response: {content.text[:200]}...", flush=True)

                logger.info(f"Reference image loaded into session, response_id: {response.id}")

                return response.id

            except Exception as e:
                print(f"[GPTImageClient]   Load reference FAILED: {type(e).__name__}: {e}", flush=True)
                if attempt < max_retries - 1:
                    print(f"[GPTImageClient]   Retrying in {retry_delay}s...", flush=True)
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    raise Exception(f"Failed to load reference image after {max_retries} attempts: {str(e)}")

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
        print(f"[GPTImageClient] generate_image called: story_id={story_id}, size={size}, quality={quality}", flush=True)
        print(f"[GPTImageClient]   previous_response_id={previous_response_id}", flush=True)
        logger.info(f"generate_image called: story_id={story_id}, size={size}, quality={quality}")
        logger.info(f"Previous response ID: {previous_response_id}")
        logger.debug(f"Prompt (first 200 chars): {prompt[:200]}...")

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

                print(f"[GPTImageClient]   Calling responses.create (attempt {attempt + 1}/{max_retries})...", flush=True)
                logger.info(f"Calling OpenAI responses.create (attempt {attempt + 1}/{max_retries})...")
                response = await self.client.responses.create(**request_params)
                print(f"[GPTImageClient]   Response received, response.id={response.id}", flush=True)
                logger.info(f"OpenAI response received, response.id: {response.id}")

                # Update session with new response ID
                self._sessions[story_id] = response.id
                print(f"[GPTImageClient]   Session updated to {response.id}", flush=True)

                # Extract image URL from response
                print(f"[GPTImageClient]   Extracting image URL from response...", flush=True)
                image_url = self._extract_image_url(response)
                if image_url:
                    print(f"[GPTImageClient]   Image URL extracted, length={len(image_url)}", flush=True)
                    logger.info(f"Image URL extracted successfully, length: {len(image_url)}")
                    return image_url

                print(f"[GPTImageClient]   ERROR: No image in response!", flush=True)
                logger.error("No image was generated in the response")
                raise ValueError("No image was generated in the response")

            except Exception as e:
                error_str = str(e)
                print(f"[GPTImageClient]   EXCEPTION: {type(e).__name__}: {error_str}", flush=True)
                logger.error(f"Image generation error: {error_str}")

                # Check if it's a retryable error (server errors, timeouts)
                if any(x in error_str.lower() for x in ['timeout', 'server', '500', '502', '503', '504']):
                    if attempt < max_retries - 1:
                        print(f"[GPTImageClient]   Retrying in {retry_delay}s...", flush=True)
                        logger.warning(f"Retryable error (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...")
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
        print(f"[GPTImageClient] _extract_image_url called", flush=True)
        logger.debug(f"Extracting image URL from response: {response.id if hasattr(response, 'id') else 'unknown'}")

        if not hasattr(response, 'output') or not response.output:
            print(f"[GPTImageClient]   Response has no output! response attrs: {dir(response)}", flush=True)
            logger.warning("Response has no output attribute or output is empty")
            return None

        print(f"[GPTImageClient]   Response has {len(response.output)} output items", flush=True)
        logger.debug(f"Response has {len(response.output)} output items")

        for idx, item in enumerate(response.output):
            item_type = getattr(item, 'type', 'unknown')
            print(f"[GPTImageClient]   Output item {idx}: type={item_type}", flush=True)
            logger.debug(f"Output item {idx}: type={item_type}")

            # Check for image generation result
            if hasattr(item, 'type') and item.type == 'image_generation_call':
                print(f"[GPTImageClient]   Found image_generation_call item!", flush=True)
                logger.debug(f"Found image_generation_call item")
                if hasattr(item, 'result') and item.result:
                    result = item.result
                    print(f"[GPTImageClient]   Image result found, length={len(result)}", flush=True)
                    logger.info(f"Image result found, length: {len(result)}, starts with: {result[:50] if len(result) > 50 else result}")
                    # Check if it's base64 data (not a URL)
                    if result and not result.startswith('http') and not result.startswith('data:'):
                        # It's raw base64 data, convert to data URL
                        print(f"[GPTImageClient]   Converting base64 to data URL", flush=True)
                        logger.debug("Converting base64 to data URL")
                        return f"data:image/png;base64,{result}"
                    return result
                else:
                    print(f"[GPTImageClient]   image_generation_call has no result!", flush=True)
                    logger.warning(f"image_generation_call has no result or result is empty")

            # Alternative structure: direct image URL in content
            if hasattr(item, 'content'):
                print(f"[GPTImageClient]   Item has content with {len(item.content)} items", flush=True)
                logger.debug(f"Item has content attribute with {len(item.content)} items")
                for content_item in item.content:
                    content_type = getattr(content_item, 'type', 'unknown')
                    print(f"[GPTImageClient]     Content item type: {content_type}", flush=True)
                    logger.debug(f"Content item type: {content_type}")
                    if hasattr(content_item, 'type') and content_item.type == 'image':
                        if hasattr(content_item, 'image_url'):
                            print(f"[GPTImageClient]     Found image_url in content!", flush=True)
                            logger.info("Found image_url in content")
                            return content_item.image_url.url
                        elif hasattr(content_item, 'url'):
                            print(f"[GPTImageClient]     Found url in content!", flush=True)
                            logger.info("Found url in content")
                            return content_item.url
                        elif hasattr(content_item, 'source') and hasattr(content_item.source, 'data'):
                            # Base64 data in source.data
                            print(f"[GPTImageClient]     Found base64 data in source.data!", flush=True)
                            logger.info("Found base64 data in source.data")
                            return f"data:image/png;base64,{content_item.source.data}"

        print(f"[GPTImageClient]   WARNING: No image URL found in any output item!", flush=True)
        logger.warning("No image URL found in response output")
        return None

    async def generate_image_with_cost(
        self,
        story_id: str,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        model_name: str = "gpt-image-1",
        reference_images: Optional[list] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an image and return both the image URL and cost information.

        Args:
            story_id: The story ID to use for session context
            prompt: The prompt describing the image to generate
            size: Image size ("1024x1024", "1024x1536", "1536x1024", "auto")
            quality: Image quality ("low", "medium", "high")
            model_name: The model name for cost calculation (e.g., 'gpt-image-1')
            reference_images: Optional list of reference images. Each item should be a dict
                             with 'data' (base64 encoded) and 'mime_type' keys
            **kwargs: Additional parameters

        Returns:
            Dictionary with 'image_url', 'cost', and 'usage' keys

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
        num_refs = len(reference_images) if reference_images else 0
        print(f"[GPTImageClient] generate_image_with_cost called: story_id={story_id}, model={model_name}, size={size}, quality={quality}, reference_images={num_refs}", flush=True)
        logger.info(f"generate_image_with_cost called: story_id={story_id}, model={model_name}, size={size}, quality={quality}, reference_images={num_refs}")

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Build the input - either a simple string or a message with images
                if reference_images:
                    # When reference images are provided, construct input as a message
                    # with text and image content items
                    message_content = []

                    # Separate art bible, character references, and page references
                    art_bible_ref = None
                    char_refs = []
                    char_descriptions = []
                    page_refs = []

                    for ref_img in reference_images:
                        ref_name = ref_img.get('character_name', 'Unknown')
                        if ref_name == 'Art Bible':
                            art_bible_ref = ref_img
                        elif ref_name.startswith('Page '):
                            page_refs.append(ref_img)
                        else:
                            char_refs.append(ref_img)
                            char_descriptions.append(ref_name)

                    # Add art bible first if present
                    if art_bible_ref:
                        message_content.append({
                            "type": "input_text",
                            "text": "ART STYLE REFERENCE (Art Bible): This image defines the visual style, color palette, and artistic approach. Match this style exactly in the generated image:"
                        })
                        data_url = f"data:{art_bible_ref['mime_type']};base64,{art_bible_ref['data']}"
                        message_content.append({
                            "type": "input_image",
                            "image_url": data_url
                        })

                    # Add character reference images
                    for ref_img in char_refs:
                        char_name = ref_img.get('character_name', 'Unknown Character')

                        message_content.append({
                            "type": "input_text",
                            "text": f"Reference image for character '{char_name}'. Use this exact appearance for this character in the generated image:"
                        })

                        data_url = f"data:{ref_img['mime_type']};base64,{ref_img['data']}"
                        message_content.append({
                            "type": "input_image",
                            "image_url": data_url
                        })

                    # Add page reference images
                    for ref_img in page_refs:
                        page_label = ref_img.get('character_name', 'Page')

                        message_content.append({
                            "type": "input_text",
                            "text": f"SCENE REFERENCE ({page_label}): This is a previously generated illustration from this story. Maintain the same visual style, environment details, color palette, and character appearances as shown in this image:"
                        })

                        data_url = f"data:{ref_img['mime_type']};base64,{ref_img['data']}"
                        message_content.append({
                            "type": "input_image",
                            "image_url": data_url
                        })

                    # Build the enhanced prompt
                    prompt_parts = []
                    prompt_parts.append("CRITICAL INSTRUCTIONS:")

                    if art_bible_ref:
                        prompt_parts.append("- Match the art style, colors, and visual approach from the Art Bible reference image exactly.")

                    if char_descriptions:
                        char_list = ", ".join(char_descriptions)
                        prompt_parts.append(f"- I have provided reference images for the following characters: {char_list}.")
                        prompt_parts.append("- You MUST copy the EXACT appearance of each character from their reference image - same face, hair color, hair style, clothing, accessories, and all distinctive features.")
                        prompt_parts.append("- Do NOT change or reimagine how the characters look.")

                    if page_refs:
                        page_labels = [ref.get('character_name', 'Page') for ref in page_refs]
                        page_list = ", ".join(page_labels)
                        prompt_parts.append(f"- I have provided scene reference images from: {page_list}.")
                        prompt_parts.append("- Maintain visual consistency with these previously generated scenes - same art style, color palette, lighting, and character appearances.")

                    prompt_parts.append(f"Now generate the following scene: {prompt}")

                    enhanced_prompt = " ".join(prompt_parts)
                    message_content.append({
                        "type": "input_text",
                        "text": enhanced_prompt
                    })

                    # Wrap in a message structure
                    input_content = [
                        {
                            "type": "message",
                            "role": "user",
                            "content": message_content
                        }
                    ]

                    ref_summary = []
                    if art_bible_ref:
                        ref_summary.append("Art Bible")
                        print(f"[GPTImageClient]   Art Bible reference: {len(art_bible_ref['data'])} chars base64", flush=True)
                    if char_descriptions:
                        ref_summary.extend(char_descriptions)
                        for ref_img in char_refs:
                            print(f"[GPTImageClient]   Character '{ref_img.get('character_name')}': {len(ref_img['data'])} chars base64", flush=True)
                    if page_refs:
                        page_labels = [ref.get('character_name', 'Page') for ref in page_refs]
                        ref_summary.extend(page_labels)
                        for ref_img in page_refs:
                            print(f"[GPTImageClient]   Page ref '{ref_img.get('character_name')}': {len(ref_img['data'])} chars base64", flush=True)
                    ref_list = ", ".join(ref_summary)
                    print(f"[GPTImageClient]   Including {len(reference_images)} reference images: {ref_list}", flush=True)
                    print(f"[GPTImageClient]   Total message_content items: {len(message_content)}", flush=True)
                    for i, item in enumerate(message_content):
                        item_type = item.get('type', 'unknown')
                        if item_type == 'input_text':
                            text = item.get('text', '')[:100]
                            print(f"[GPTImageClient]   Content {i}: {item_type} - '{text}...'", flush=True)
                        else:
                            print(f"[GPTImageClient]   Content {i}: {item_type}", flush=True)
                    logger.info(f"Including {len(reference_images)} reference images: {ref_list}")
                else:
                    input_content = prompt

                # Build the request
                # Note: The main "model" must be a text model (e.g., gpt-4o) for the Responses API
                # The image model is specified inside the image_generation tool configuration
                request_params = {
                    "model": self.model,
                    "input": input_content,
                    "tools": [{"type": "image_generation", "size": size, "quality": quality, "model": model_name}]
                }

                # Add conversation context if we have a previous response
                if previous_response_id:
                    request_params["previous_response_id"] = previous_response_id

                print(f"[GPTImageClient]   Calling responses.create with text_model={self.model}, image_model={model_name} (attempt {attempt + 1}/{max_retries})...", flush=True)
                response = await self.client.responses.create(**request_params)
                print(f"[GPTImageClient]   Response received, response.id={response.id}", flush=True)

                # Update session with new response ID
                self._sessions[story_id] = response.id

                # Extract image URL from response
                image_url = self._extract_image_url(response)
                if not image_url:
                    raise ValueError("No image was generated in the response")

                # Extract usage and calculate cost
                usage_data = extract_usage_from_response(response)
                cost_info = None
                if usage_data:
                    try:
                        cost_info = estimate_gpt_image_cost(
                            model=model_name,
                            size=size,
                            quality=quality,
                            usage=usage_data
                        )
                        print(f"[GPTImageClient]   Cost calculated: ${cost_info.get('total_estimated_cost', 0):.4f}", flush=True)
                        logger.info(f"Cost calculated: ${cost_info.get('total_estimated_cost', 0):.4f}")
                    except Exception as e:
                        print(f"[GPTImageClient]   Cost calculation failed: {e}", flush=True)
                        logger.warning(f"Cost calculation failed: {e}")

                return {
                    'image_url': image_url,
                    'cost': cost_info.get('total_estimated_cost', 0.0) if cost_info else None,
                    'cost_breakdown': cost_info,
                    'usage': usage_data
                }

            except Exception as e:
                error_str = str(e)
                print(f"[GPTImageClient]   EXCEPTION: {type(e).__name__}: {error_str}", flush=True)
                logger.error(f"Image generation error: {error_str}")

                # Check if it's a retryable error (server errors, timeouts)
                if any(x in error_str.lower() for x in ['timeout', 'server', '500', '502', '503', '504']):
                    if attempt < max_retries - 1:
                        print(f"[GPTImageClient]   Retrying in {retry_delay}s...", flush=True)
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue

                raise Exception(f"Image generation failed: {error_str}")

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
