"""
Unit tests for AI Client Factory.
Write these tests BEFORE implementing the factory (TDD approach).

The factory creates appropriate AI clients based on provider configuration.
"""

import pytest


class TestAIClientFactory:
    """Test AIClientFactory for creating AI clients"""

    @pytest.fixture
    def mock_parameters(self):
        """Create mock StoryParameters for testing"""
        from src.models.config import StoryParameters
        return StoryParameters(
            languages=["English"],
            complexities=["simple"],
            vocabulary_levels=["basic"],
            age_groups=["3-5"],
            page_counts=[8],
            genres=["adventure"],
            art_styles=["cartoon"]
        )

    @pytest.fixture
    def mock_defaults(self):
        """Create mock DefaultValues for testing"""
        from src.models.config import DefaultValues
        return DefaultValues(
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=8
        )

    def test_create_text_client_ollama(self, mock_parameters, mock_defaults):
        """Test creating Ollama text client from config"""
        from src.ai.ai_factory import AIClientFactory
        from src.ai.ollama_client import OllamaClient
        from src.models.config import AppConfig, AIProviderConfig, OllamaConfig, TextProvider

        config = AppConfig(
            ai_providers=AIProviderConfig(
                text_provider=TextProvider.OLLAMA,
                ollama=OllamaConfig(
                    base_url="http://localhost:11434",
                    model="granite4:small-h",
                    timeout=120
                )
            ),
            parameters=mock_parameters,
            defaults=mock_defaults
        )

        client = AIClientFactory.create_text_client(config)

        assert isinstance(client, OllamaClient)
        assert client.base_url == "http://localhost:11434"
        assert client.model == "granite4:small-h"
        assert client.timeout == 120

    def test_create_text_client_openai(self, mock_parameters, mock_defaults):
        """Test creating OpenAI text client from config"""
        from src.ai.ai_factory import AIClientFactory
        from src.ai.openai_client import OpenAIClient
        from src.models.config import AppConfig, AIProviderConfig, OpenAIConfig, TextProvider

        config = AppConfig(
            ai_providers=AIProviderConfig(
                text_provider=TextProvider.OPENAI,
                openai=OpenAIConfig(
                    api_key="test-key",
                    text_model="gpt-4o-mini",
                    timeout=60
                )
            ),
            parameters=mock_parameters,
            defaults=mock_defaults
        )

        client = AIClientFactory.create_text_client(config)

        assert isinstance(client, OpenAIClient)
        assert client.api_key == "test-key"
        assert client.text_model == "gpt-4o-mini"
        assert client.timeout == 60

    def test_create_text_client_claude(self, mock_parameters, mock_defaults):
        """Test creating Claude text client from config"""
        from src.ai.ai_factory import AIClientFactory
        from src.models.config import AppConfig, AIProviderConfig, ClaudeConfig, TextProvider

        config = AppConfig(
            ai_providers=AIProviderConfig(
                text_provider=TextProvider.CLAUDE,
                claude=ClaudeConfig(
                    api_key="test-claude-key",
                    model="claude-sonnet-4-5-20250929",
                    timeout=90
                )
            ),
            parameters=mock_parameters,
            defaults=mock_defaults
        )

        # Should raise NotImplementedError since Claude client is not implemented yet
        with pytest.raises(NotImplementedError) as exc_info:
            AIClientFactory.create_text_client(config)

        assert "Claude" in str(exc_info.value)

    def test_create_text_client_unsupported_provider(self, mock_parameters, mock_defaults):
        """Test error handling for unsupported text provider"""
        from src.ai.ai_factory import AIClientFactory
        from src.models.config import AppConfig, AIProviderConfig

        # Create config with an invalid provider (this tests robustness)
        config = AppConfig(
            ai_providers=AIProviderConfig(),
            parameters=mock_parameters,
            defaults=mock_defaults
        )
        # Manually set invalid provider to test error handling
        config.ai_providers.text_provider = "invalid_provider"

        with pytest.raises(ValueError) as exc_info:
            AIClientFactory.create_text_client(config)

        assert "Unsupported text provider" in str(exc_info.value)

    def test_create_text_client_missing_ollama_config(self, mock_parameters, mock_defaults):
        """Test error when Ollama is selected but config is missing"""
        from src.ai.ai_factory import AIClientFactory
        from src.models.config import AppConfig, AIProviderConfig, TextProvider

        config = AppConfig(
            ai_providers=AIProviderConfig(
                text_provider=TextProvider.OLLAMA,
                ollama=None  # Missing config
            ),
            parameters=mock_parameters,
            defaults=mock_defaults
        )

        with pytest.raises(ValueError) as exc_info:
            AIClientFactory.create_text_client(config)

        assert "Ollama" in str(exc_info.value)
        assert "config" in str(exc_info.value).lower()

    def test_create_text_client_missing_openai_config(self, mock_parameters, mock_defaults):
        """Test error when OpenAI is selected but config is missing"""
        from src.ai.ai_factory import AIClientFactory
        from src.models.config import AppConfig, AIProviderConfig, TextProvider

        config = AppConfig(
            ai_providers=AIProviderConfig(
                text_provider=TextProvider.OPENAI,
                openai=None  # Missing config
            ),
            parameters=mock_parameters,
            defaults=mock_defaults
        )

        with pytest.raises(ValueError) as exc_info:
            AIClientFactory.create_text_client(config)

        assert "OpenAI" in str(exc_info.value)
        assert "config" in str(exc_info.value).lower()

    def test_create_text_client_missing_claude_config(self, mock_parameters, mock_defaults):
        """Test error when Claude is selected but config is missing"""
        from src.ai.ai_factory import AIClientFactory
        from src.models.config import AppConfig, AIProviderConfig, TextProvider

        config = AppConfig(
            ai_providers=AIProviderConfig(
                text_provider=TextProvider.CLAUDE,
                claude=None  # Missing config
            ),
            parameters=mock_parameters,
            defaults=mock_defaults
        )

        with pytest.raises(ValueError) as exc_info:
            AIClientFactory.create_text_client(config)

        assert "Claude" in str(exc_info.value)
        assert "config" in str(exc_info.value).lower()

    def test_create_text_client_returns_base_ai_client(self, mock_parameters, mock_defaults):
        """Test that created clients implement BaseAIClient interface"""
        from src.ai.ai_factory import AIClientFactory
        from src.ai.base_client import BaseAIClient
        from src.models.config import AppConfig, AIProviderConfig, OllamaConfig, TextProvider

        config = AppConfig(
            ai_providers=AIProviderConfig(
                text_provider=TextProvider.OLLAMA,
                ollama=OllamaConfig(
                    base_url="http://localhost:11434",
                    model="granite4:small-h",
                    timeout=120
                )
            ),
            parameters=mock_parameters,
            defaults=mock_defaults
        )

        client = AIClientFactory.create_text_client(config)

        # Verify it implements the BaseAIClient interface
        assert isinstance(client, BaseAIClient)
        assert hasattr(client, 'generate_text')

    def test_create_text_client_with_default_provider(self, mock_parameters, mock_defaults):
        """Test creating text client with default provider (Ollama)"""
        from src.ai.ai_factory import AIClientFactory
        from src.ai.ollama_client import OllamaClient
        from src.models.config import AppConfig, AIProviderConfig, OllamaConfig

        # AppConfig defaults to Ollama as text provider
        config = AppConfig(
            ai_providers=AIProviderConfig(
                ollama=OllamaConfig(
                    base_url="http://localhost:11434",
                    model="granite4:small-h",
                    timeout=120
                )
            ),
            parameters=mock_parameters,
            defaults=mock_defaults
        )

        client = AIClientFactory.create_text_client(config)

        assert isinstance(client, OllamaClient)

    def test_create_different_clients_from_same_factory(self, mock_parameters, mock_defaults):
        """Test creating multiple different clients from the same factory"""
        from src.ai.ai_factory import AIClientFactory
        from src.ai.ollama_client import OllamaClient
        from src.ai.openai_client import OpenAIClient
        from src.models.config import (
            AppConfig, AIProviderConfig, OllamaConfig, OpenAIConfig, TextProvider
        )

        # Create Ollama client
        ollama_config = AppConfig(
            ai_providers=AIProviderConfig(
                text_provider=TextProvider.OLLAMA,
                ollama=OllamaConfig(
                    base_url="http://localhost:11434",
                    model="granite4:small-h",
                    timeout=120
                )
            ),
            parameters=mock_parameters,
            defaults=mock_defaults
        )
        ollama_client = AIClientFactory.create_text_client(ollama_config)

        # Create OpenAI client
        openai_config = AppConfig(
            ai_providers=AIProviderConfig(
                text_provider=TextProvider.OPENAI,
                openai=OpenAIConfig(
                    api_key="test-key",
                    text_model="gpt-4o",
                    timeout=60
                )
            ),
            parameters=mock_parameters,
            defaults=mock_defaults
        )
        openai_client = AIClientFactory.create_text_client(openai_config)

        # Verify they are different types
        assert isinstance(ollama_client, OllamaClient)
        assert isinstance(openai_client, OpenAIClient)
        assert type(ollama_client) != type(openai_client)

    def test_factory_is_stateless(self, mock_parameters, mock_defaults):
        """Test that factory doesn't maintain state between calls"""
        from src.ai.ai_factory import AIClientFactory
        from src.models.config import AppConfig, AIProviderConfig, OllamaConfig

        config = AppConfig(
            ai_providers=AIProviderConfig(
                ollama=OllamaConfig(
                    base_url="http://localhost:11434",
                    model="granite4:small-h",
                    timeout=120
                )
            ),
            parameters=mock_parameters,
            defaults=mock_defaults
        )

        # Create two clients with same config
        client1 = AIClientFactory.create_text_client(config)
        client2 = AIClientFactory.create_text_client(config)

        # They should be different instances (factory doesn't cache)
        assert client1 is not client2
        # But same type
        assert type(client1) == type(client2)
