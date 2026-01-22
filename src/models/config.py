"""
Configuration data models for the story generator application.

These models define the structure for AI provider configuration,
story parameters, and default values loaded from JSON files.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class TextProvider(str, Enum):
    """Text generation provider options"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    CLAUDE = "claude"


class ImageProvider(str, Enum):
    """Image generation provider options"""
    GPT_4O = "gpt-4o"  # Conversation-based image generation with GPT-4o
    GPT_IMAGE = "gpt-image-1"
    DALLE2 = "dall-e-2"  # Legacy support
    DALLE3 = "dall-e-3"  # Legacy support
    STABLE_DIFFUSION = "stable-diffusion"


@dataclass(frozen=True)
class OllamaConfig:
    """Ollama server configuration"""
    base_url: str = "http://localhost:11434"
    model: str = "granite4:small-h"
    timeout: int = 120


@dataclass(frozen=True)
class OpenAIConfig:
    """OpenAI API configuration"""
    api_key: str
    text_model: str = "gpt-4"
    image_model: str = "dall-e-3"
    timeout: int = 120


@dataclass(frozen=True)
class ClaudeConfig:
    """Anthropic Claude API configuration"""
    api_key: str
    model: str = "claude-sonnet-4-5-20250929"
    timeout: int = 120


@dataclass
class AIProviderConfig:
    """AI provider configuration"""
    text_provider: TextProvider = TextProvider.OLLAMA
    image_provider: ImageProvider = ImageProvider.GPT_IMAGE
    ollama: Optional[OllamaConfig] = None
    openai: Optional[OpenAIConfig] = None
    claude: Optional[ClaudeConfig] = None


@dataclass
class StoryParameters:
    """Available story generation parameters (loaded from parameters.json)"""
    languages: List[str]
    complexities: List[str]
    vocabulary_levels: List[str]
    age_groups: List[str]
    page_counts: List[int]
    genres: List[str]
    art_styles: List[str]


@dataclass
class DefaultValues:
    """Default values for story generation (loaded from defaults.json)"""
    language: str
    complexity: str
    vocabulary_diversity: str
    age_group: str
    num_pages: int
    genre: Optional[str] = None
    art_style: Optional[str] = None


@dataclass
class AppConfig:
    """Application configuration"""
    ai_providers: AIProviderConfig
    parameters: StoryParameters
    defaults: DefaultValues
    auto_save_interval: int = 120  # seconds
    data_directory: str = "./data"
