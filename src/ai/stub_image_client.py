"""
Stub Image Client for development and testing.

This client returns placeholder image URLs instead of generating real images.
Replace this with a real image client (DALL-E, Stable Diffusion, etc.) for production.
"""

from src.ai.base_client import BaseImageClient


class StubImageClient(BaseImageClient):
    """
    Stub implementation of image client for development.

    Returns placeholder image URLs from placeholder.com instead of generating
    real images. This allows the application to work without requiring an actual
    image generation API.
    """

    def __init__(self):
        """Initialize the stub image client."""
        self.call_count = 0

    async def generate_image(self, prompt: str, **kwargs) -> str:
        """
        Return a placeholder image URL.

        Args:
            prompt: The image generation prompt (logged but not used)
            **kwargs: Additional parameters (ignored)

        Returns:
            URL to a placeholder image
        """
        self.call_count += 1

        # Return a placeholder image URL
        # Using placeholder.com which provides free placeholder images
        # Format: https://via.placeholder.com/{width}x{height}?text={text}
        width = kwargs.get('width', 512)
        height = kwargs.get('height', 512)

        # Create a simple text label from the first few words of the prompt
        words = prompt.split()[:3]
        text = '+'.join(words) if words else 'Story+Image'

        placeholder_url = f"https://via.placeholder.com/{width}x{height}?text={text}"

        return placeholder_url
