"""
Abstract base classes for AI clients.

These classes define the interface that all AI service clients must implement,
enabling dependency injection and easy swapping of AI providers.
"""

from abc import ABC, abstractmethod


class BaseAIClient(ABC):
    """
    Abstract base class for text generation AI clients.

    All text generation clients (Ollama, OpenAI, Claude) must inherit from
    this class and implement the generate_text method.
    """

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on a prompt.

        Args:
            prompt: The input prompt for text generation
            **kwargs: Additional provider-specific parameters
                     (e.g., max_tokens, temperature, model)

        Returns:
            Generated text as a string

        Raises:
            Exception: Provider-specific errors during generation
        """
        pass


class BaseImageClient(ABC):
    """
    Abstract base class for image generation AI clients.

    All image generation clients (DALL-E, Stable Diffusion) must inherit from
    this class and implement the generate_image method.
    """

    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> bytes:
        """
        Generate an image based on a prompt.

        Args:
            prompt: The input prompt for image generation
            **kwargs: Additional provider-specific parameters
                     (e.g., size, quality, style)

        Returns:
            Generated image data as bytes (PNG format)

        Raises:
            Exception: Provider-specific errors during generation
        """
        pass
