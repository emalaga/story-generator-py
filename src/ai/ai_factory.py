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

    @staticmethod
    def create_text_client_for_model(config: AppConfig, model_string: str) -> BaseAIClient:
        """
        Create a text generation client based on a provider:model string.

        Args:
            config: Application configuration containing provider settings
            model_string: String in format "provider:model" (e.g., "openai:gpt-4")

        Returns:
            BaseAIClient implementation for the specified provider and model

        Raises:
            ValueError: If model_string format is invalid or provider is unsupported
        """
        if not model_string or ':' not in model_string:
            # Fall back to default provider
            return AIClientFactory.create_text_client(config)

        parts = model_string.split(':', 1)
        provider = parts[0].lower()
        model = parts[1]

        if provider == 'openai':
            if config.ai_providers.openai is None:
                raise ValueError("OpenAI config is missing")
            # Create a modified config with the specified model
            from src.models.config import OpenAIConfig
            openai_config = OpenAIConfig(
                api_key=config.ai_providers.openai.api_key,
                text_model=model,
                image_model=config.ai_providers.openai.image_model,
                timeout=config.ai_providers.openai.timeout
            )
            return OpenAIClient(openai_config)

        elif provider == 'ollama':
            if config.ai_providers.ollama is None:
                raise ValueError("Ollama config is missing")
            # Create a modified config with the specified model
            from src.models.config import OllamaConfig
            ollama_config = OllamaConfig(
                base_url=config.ai_providers.ollama.base_url,
                model=model,
                timeout=config.ai_providers.ollama.timeout
            )
            return OllamaClient(ollama_config)

        else:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: openai, ollama"
            )
