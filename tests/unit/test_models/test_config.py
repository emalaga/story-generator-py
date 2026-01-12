"""
Unit tests for Configuration Models.
Write these tests BEFORE implementing the models (TDD approach).
"""

import pytest
from dataclasses import FrozenInstanceError


class TestTextProvider:
    """Test TextProvider enum"""

    def test_text_provider_values(self):
        """Test that TextProvider has correct values"""
        from src.models.config import TextProvider

        assert TextProvider.OLLAMA.value == "ollama"
        assert TextProvider.OPENAI.value == "openai"
        assert TextProvider.CLAUDE.value == "claude"

    def test_text_provider_from_string(self):
        """Test creating TextProvider from string"""
        from src.models.config import TextProvider

        assert TextProvider("ollama") == TextProvider.OLLAMA
        assert TextProvider("openai") == TextProvider.OPENAI
        assert TextProvider("claude") == TextProvider.CLAUDE


class TestImageProvider:
    """Test ImageProvider enum"""

    def test_image_provider_values(self):
        """Test that ImageProvider has correct values"""
        from src.models.config import ImageProvider

        assert ImageProvider.DALLE2.value == "dall-e-2"
        assert ImageProvider.DALLE3.value == "dall-e-3"
        assert ImageProvider.STABLE_DIFFUSION.value == "stable-diffusion"

    def test_image_provider_from_string(self):
        """Test creating ImageProvider from string"""
        from src.models.config import ImageProvider

        assert ImageProvider("dall-e-2") == ImageProvider.DALLE2
        assert ImageProvider("dall-e-3") == ImageProvider.DALLE3
        assert ImageProvider("stable-diffusion") == ImageProvider.STABLE_DIFFUSION


class TestOllamaConfig:
    """Test OllamaConfig dataclass"""

    def test_ollama_config_defaults(self):
        """Test OllamaConfig with default values"""
        from src.models.config import OllamaConfig

        config = OllamaConfig()

        assert config.base_url == "http://localhost:11434"
        assert config.model == "granite4:small-h"
        assert config.timeout == 120

    def test_ollama_config_custom_values(self):
        """Test OllamaConfig with custom values"""
        from src.models.config import OllamaConfig

        config = OllamaConfig(
            base_url="http://custom:8080",
            model="llama2",
            timeout=60
        )

        assert config.base_url == "http://custom:8080"
        assert config.model == "llama2"
        assert config.timeout == 60

    def test_ollama_config_is_frozen(self):
        """Test that OllamaConfig is immutable (frozen)"""
        from src.models.config import OllamaConfig

        config = OllamaConfig()

        with pytest.raises(FrozenInstanceError):
            config.base_url = "http://new:1234"


class TestOpenAIConfig:
    """Test OpenAIConfig dataclass"""

    def test_openai_config_defaults(self):
        """Test OpenAIConfig with default values"""
        from src.models.config import OpenAIConfig

        config = OpenAIConfig(api_key="test-key")

        assert config.api_key == "test-key"
        assert config.text_model == "gpt-4"
        assert config.image_model == "dall-e-3"
        assert config.timeout == 120

    def test_openai_config_custom_values(self):
        """Test OpenAIConfig with custom values"""
        from src.models.config import OpenAIConfig

        config = OpenAIConfig(
            api_key="custom-key",
            text_model="gpt-3.5-turbo",
            image_model="dall-e-2",
            timeout=60
        )

        assert config.api_key == "custom-key"
        assert config.text_model == "gpt-3.5-turbo"
        assert config.image_model == "dall-e-2"
        assert config.timeout == 60


class TestClaudeConfig:
    """Test ClaudeConfig dataclass"""

    def test_claude_config_defaults(self):
        """Test ClaudeConfig with default values"""
        from src.models.config import ClaudeConfig

        config = ClaudeConfig(api_key="test-key")

        assert config.api_key == "test-key"
        assert config.model == "claude-sonnet-4-5-20250929"
        assert config.timeout == 120

    def test_claude_config_custom_values(self):
        """Test ClaudeConfig with custom values"""
        from src.models.config import ClaudeConfig

        config = ClaudeConfig(
            api_key="custom-key",
            model="claude-opus-4",
            timeout=60
        )

        assert config.api_key == "custom-key"
        assert config.model == "claude-opus-4"
        assert config.timeout == 60


class TestAIProviderConfig:
    """Test AIProviderConfig dataclass"""

    def test_ai_provider_config_defaults(self):
        """Test AIProviderConfig with default values"""
        from src.models.config import AIProviderConfig, TextProvider, ImageProvider

        config = AIProviderConfig()

        assert config.text_provider == TextProvider.OLLAMA
        assert config.image_provider == ImageProvider.DALLE3
        assert config.ollama is None
        assert config.openai is None
        assert config.claude is None

    def test_ai_provider_config_with_providers(self):
        """Test AIProviderConfig with provider configurations"""
        from src.models.config import (
            AIProviderConfig,
            TextProvider,
            ImageProvider,
            OllamaConfig,
            OpenAIConfig
        )

        ollama = OllamaConfig()
        openai = OpenAIConfig(api_key="test-key")

        config = AIProviderConfig(
            text_provider=TextProvider.OLLAMA,
            image_provider=ImageProvider.DALLE3,
            ollama=ollama,
            openai=openai
        )

        assert config.text_provider == TextProvider.OLLAMA
        assert config.image_provider == ImageProvider.DALLE3
        assert config.ollama == ollama
        assert config.openai == openai


class TestStoryParameters:
    """Test StoryParameters dataclass"""

    def test_story_parameters_creation(self):
        """Test creating StoryParameters"""
        from src.models.config import StoryParameters

        params = StoryParameters(
            languages=["Spanish", "French"],
            complexities=["beginner", "intermediate"],
            vocabulary_levels=["low", "medium"],
            age_groups=["4-7 years"],
            page_counts=[5, 10],
            genres=["Adventure"],
            art_styles=["watercolor children's book illustration"]
        )

        assert params.languages == ["Spanish", "French"]
        assert params.complexities == ["beginner", "intermediate"]
        assert params.vocabulary_levels == ["low", "medium"]
        assert params.age_groups == ["4-7 years"]
        assert params.page_counts == [5, 10]
        assert params.genres == ["Adventure"]
        assert params.art_styles == ["watercolor children's book illustration"]

    def test_story_parameters_full_set(self):
        """Test StoryParameters with full data set"""
        from src.models.config import StoryParameters

        params = StoryParameters(
            languages=["Spanish", "French", "German", "Italian", "Portuguese",
                      "Mandarin", "Japanese", "Korean", "Arabic", "Russian", "English"],
            complexities=["beginner", "intermediate", "advanced"],
            vocabulary_levels=["low", "medium", "high"],
            age_groups=["0-3 years", "4-7 years", "8-12 years", "13+ years"],
            page_counts=[3, 5, 8, 10, 15, 20],
            genres=["Adventure", "Fantasy", "Science Fiction", "Mystery",
                   "Friendship", "Family", "Animals", "Nature",
                   "Educational", "Bedtime Story"],
            art_styles=["watercolor children's book illustration",
                       "digital cartoon illustration",
                       "pencil sketch style"]
        )

        assert len(params.languages) == 11
        assert len(params.complexities) == 3
        assert len(params.vocabulary_levels) == 3
        assert len(params.age_groups) == 4
        assert len(params.page_counts) == 6
        assert len(params.genres) == 10
        assert len(params.art_styles) == 3


class TestDefaultValues:
    """Test DefaultValues dataclass"""

    def test_default_values_creation(self):
        """Test creating DefaultValues"""
        from src.models.config import DefaultValues

        defaults = DefaultValues(
            language="Spanish",
            complexity="beginner",
            vocabulary_diversity="medium",
            age_group="4-7 years",
            num_pages=5,
            genre="Adventure",
            art_style="watercolor children's book illustration"
        )

        assert defaults.language == "Spanish"
        assert defaults.complexity == "beginner"
        assert defaults.vocabulary_diversity == "medium"
        assert defaults.age_group == "4-7 years"
        assert defaults.num_pages == 5
        assert defaults.genre == "Adventure"
        assert defaults.art_style == "watercolor children's book illustration"

    def test_default_values_optional_genre(self):
        """Test DefaultValues with optional genre"""
        from src.models.config import DefaultValues

        defaults = DefaultValues(
            language="Spanish",
            complexity="beginner",
            vocabulary_diversity="medium",
            age_group="4-7 years",
            num_pages=5
        )

        assert defaults.genre is None
        assert defaults.art_style is None


class TestAppConfig:
    """Test AppConfig dataclass"""

    def test_app_config_creation(self):
        """Test creating AppConfig"""
        from src.models.config import (
            AppConfig,
            AIProviderConfig,
            StoryParameters,
            DefaultValues
        )

        ai_providers = AIProviderConfig()
        parameters = StoryParameters(
            languages=["Spanish"],
            complexities=["beginner"],
            vocabulary_levels=["medium"],
            age_groups=["4-7 years"],
            page_counts=[5],
            genres=["Adventure"],
            art_styles=["watercolor children's book illustration"]
        )
        defaults = DefaultValues(
            language="Spanish",
            complexity="beginner",
            vocabulary_diversity="medium",
            age_group="4-7 years",
            num_pages=5
        )

        config = AppConfig(
            ai_providers=ai_providers,
            parameters=parameters,
            defaults=defaults
        )

        assert config.ai_providers == ai_providers
        assert config.parameters == parameters
        assert config.defaults == defaults
        assert config.auto_save_interval == 120
        assert config.data_directory == "./data"

    def test_app_config_custom_settings(self):
        """Test AppConfig with custom settings"""
        from src.models.config import (
            AppConfig,
            AIProviderConfig,
            StoryParameters,
            DefaultValues
        )

        ai_providers = AIProviderConfig()
        parameters = StoryParameters(
            languages=["Spanish"],
            complexities=["beginner"],
            vocabulary_levels=["medium"],
            age_groups=["4-7 years"],
            page_counts=[5],
            genres=["Adventure"],
            art_styles=["watercolor children's book illustration"]
        )
        defaults = DefaultValues(
            language="Spanish",
            complexity="beginner",
            vocabulary_diversity="medium",
            age_group="4-7 years",
            num_pages=5
        )

        config = AppConfig(
            ai_providers=ai_providers,
            parameters=parameters,
            defaults=defaults,
            auto_save_interval=60,
            data_directory="./custom_data"
        )

        assert config.auto_save_interval == 60
        assert config.data_directory == "./custom_data"
