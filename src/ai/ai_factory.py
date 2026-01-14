"""
AI Client Factory for dependency injection.

This factory creates appropriate AI client instances based on the
provider configuration, enabling easy swapping of AI providers.
"""

from src.ai.base_client import BaseAIClient
from src.ai.ollama_client import OllamaClient
from src.ai.openai_client import OpenAIClient
from src.models.config import AppConfig, TextProvider


class AIClientFactory:
    """
    Factory for creating AI clients based on configuration.

    This factory implements the Factory pattern to provide dependency injection
    for AI services, making it easy to swap between different providers
    (Ollama, OpenAI, Claude) based on configuration.
    """

    @staticmethod
    def create_text_client(config: AppConfig) -> BaseAIClient:
        """
        Create a text generation client based on the configured provider.

        Args:
            config: Application configuration containing provider settings

        Returns:
            BaseAIClient implementation for the configured provider

        Raises:
            ValueError: If provider is unsupported or configuration is missing
            NotImplementedError: If provider is valid but not yet implemented
        """
        provider = config.ai_providers.text_provider

        if provider == TextProvider.OLLAMA:
            if config.ai_providers.ollama is None:
                raise ValueError(
                    "Ollama text provider selected but Ollama config is missing"
                )
            return OllamaClient(config.ai_providers.ollama)

        elif provider == TextProvider.OPENAI:
            if config.ai_providers.openai is None:
                raise ValueError(
                    "OpenAI text provider selected but OpenAI config is missing"
                )
            return OpenAIClient(config.ai_providers.openai)

        elif provider == TextProvider.CLAUDE:
            if config.ai_providers.claude is None:
                raise ValueError(
                    "Claude text provider selected but Claude config is missing"
                )
            raise NotImplementedError(
                "Claude text client is not yet implemented. "
                "Please use Ollama or OpenAI as the text provider."
            )

        else:
            raise ValueError(
                f"Unsupported text provider: {provider}. "
                f"Supported providers: {[p.value for p in TextProvider]}"
            )
