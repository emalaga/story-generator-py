# Children's Story Generator - Architecture Document

## 1. Architecture Overview

### 1.1 Design Principles
- **Modular Design**: Each component is a self-contained Python module
- **Direct Module Communication**: Modules call each other directly (no unnecessary APIs)
- **Test-Driven Development (TDD)**: Unit tests written before implementation
- **Separation of Concerns**: Clear boundaries between business logic, AI integration, and UI
- **Data-Driven**: Well-defined data structures for inter-module communication

### 1.2 Architecture Pattern
**Layered Architecture with Service-Oriented Modules**

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Interface Layer                     │
│                     (Flask/FastAPI Routes)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Application Service Layer                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Story      │  │   Image      │  │   Export     │      │
│  │  Generator   │  │  Generator   │  │   Service    │      │
│  │   Service    │  │   Service    │  │              │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────┐
│                    Core Domain Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Character   │  │  Vocabulary  │  │    Story     │      │
│  │  Extractor   │  │  Analyzer    │  │   Manager    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  AI Integration Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Ollama     │  │    OpenAI    │  │  AI Factory  │      │
│  │   Client     │  │    Client    │  │   (Config)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Data Persistence Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Project    │  │    Config    │  │    Image     │      │
│  │  Repository  │  │  Repository  │  │   Storage    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Project Structure

```
story-generator-py/
├── app.py                          # Flask/FastAPI application entry point
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Pytest configuration
├── .env.example                    # Environment variables template
│
├── src/
│   ├── __init__.py
│   │
│   ├── models/                     # Data structures (domain models)
│   │   ├── __init__.py
│   │   ├── story.py               # Story, Page, StoryMetadata classes
│   │   ├── character.py           # Character, CharacterProfile classes
│   │   ├── image.py               # ImagePrompt, GeneratedImage classes
│   │   ├── vocabulary.py          # VocabularyEntry, VocabularyList classes
│   │   └── config.py              # AIProviderConfig, AppConfig classes
│   │
│   ├── services/                   # Business logic services
│   │   ├── __init__.py
│   │   ├── story_generator.py     # Story generation orchestration
│   │   ├── image_generator.py     # Image generation orchestration
│   │   ├── export_service.py      # PDF/export functionality
│   │   └── project_manager.py     # Save/load projects
│   │
│   ├── domain/                     # Core domain logic
│   │   ├── __init__.py
│   │   ├── character_extractor.py # Extract characters from story
│   │   ├── vocabulary_analyzer.py # Extract and translate vocabulary
│   │   ├── prompt_builder.py      # Build AI prompts for consistency
│   │   └── story_validator.py     # Validate story content
│   │
│   ├── ai/                         # AI integration layer
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract base classes
│   │   ├── ollama_client.py       # Ollama integration
│   │   ├── openai_client.py       # OpenAI (GPT + DALL-E) integration
│   │   ├── claude_client.py       # Anthropic Claude integration (optional)
│   │   └── ai_factory.py          # Factory for AI client selection
│   │
│   ├── repositories/               # Data persistence
│   │   ├── __init__.py
│   │   ├── project_repository.py  # Save/load story projects
│   │   ├── config_repository.py   # Load/save configuration
│   │   └── image_storage.py       # Save/load generated images
│   │
│   ├── web/                        # Web interface
│   │   ├── __init__.py
│   │   ├── routes.py              # Flask/FastAPI routes
│   │   ├── static/                # CSS, JS, images
│   │   └── templates/             # HTML templates
│   │
│   └── utils/                      # Utility functions
│       ├── __init__.py
│       ├── validators.py          # Input validation
│       └── logger.py              # Logging configuration
│
├── tests/                          # Test directory (mirrors src/)
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   │
│   ├── unit/                      # Unit tests
│   │   ├── test_models/
│   │   │   ├── test_story.py
│   │   │   ├── test_character.py
│   │   │   └── test_vocabulary.py
│   │   │
│   │   ├── test_services/
│   │   │   ├── test_story_generator.py
│   │   │   └── test_image_generator.py
│   │   │
│   │   ├── test_domain/
│   │   │   ├── test_character_extractor.py
│   │   │   ├── test_vocabulary_analyzer.py
│   │   │   └── test_prompt_builder.py
│   │   │
│   │   └── test_ai/
│   │       ├── test_ollama_client.py
│   │       └── test_openai_client.py
│   │
│   └── integration/               # Integration tests
│       ├── test_story_generation_flow.py
│       └── test_image_generation_flow.py
│
├── data/                          # Local data storage
│   ├── projects/                 # Saved story projects
│   ├── images/                   # Generated images
│   └── config/                   # Configuration files
│       ├── config.json           # AI provider configuration
│       ├── parameters.json       # Story parameters and options
│       └── defaults.json         # Default values for story generation
│
└── docs/                          # Documentation
    ├── SPECIFICATIONS.md
    ├── ARCHITECTURE.md
    └── API.md
```

---

## 3. Data Structures

### 3.1 Core Domain Models

#### Story Models (`src/models/story.py`)

```python
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class Complexity(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class VocabularyDiversity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class StoryMetadata:
    """Metadata for story generation"""
    prompt: str
    language: str
    complexity: Complexity
    vocabulary_diversity: VocabularyDiversity
    target_age_group: str
    num_pages: int
    genre: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Page:
    """Single page of a story"""
    page_number: int
    text: str
    is_approved: bool = False
    edited: bool = False
    original_text: Optional[str] = None  # Track if user edited

    def edit(self, new_text: str) -> None:
        """Edit page text"""
        if not self.original_text:
            self.original_text = self.text
        self.text = new_text
        self.edited = True
        self.is_approved = False

@dataclass
class Story:
    """Complete story with all pages"""
    id: str
    title: str
    metadata: StoryMetadata
    pages: List[Page]
    vocabulary: Optional['VocabularyList'] = None
    all_pages_approved: bool = False

    def approve_all_pages(self) -> None:
        """Approve all pages at once"""
        for page in self.pages:
            page.is_approved = True
        self.all_pages_approved = True

    def get_page(self, page_number: int) -> Optional[Page]:
        """Get specific page by number"""
        for page in self.pages:
            if page.page_number == page_number:
                return page
        return None

    def get_full_text(self) -> str:
        """Get complete story text"""
        return "\n\n".join([page.text for page in self.pages])
```

#### Character Models (`src/models/character.py`)

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class CharacterProfile:
    """Detailed character description for consistency"""
    name: str
    age: Optional[str] = None
    physical_description: str = ""
    hair_color: Optional[str] = None
    hair_style: Optional[str] = None
    eye_color: Optional[str] = None
    clothing: str = ""
    distinctive_features: List[str] = field(default_factory=list)
    personality_traits: List[str] = field(default_factory=list)
    role: str = ""  # protagonist, antagonist, supporting

    def to_prompt_string(self) -> str:
        """Convert to consistent prompt description"""
        parts = [self.name]
        if self.age:
            parts.append(f"{self.age} years old")
        if self.physical_description:
            parts.append(self.physical_description)
        if self.hair_color and self.hair_style:
            parts.append(f"{self.hair_color} hair in {self.hair_style}")
        elif self.hair_color:
            parts.append(f"{self.hair_color} hair")
        if self.eye_color:
            parts.append(f"{self.eye_color} eyes")
        if self.clothing:
            parts.append(f"wearing {self.clothing}")
        if self.distinctive_features:
            parts.extend(self.distinctive_features)

        return ", ".join(parts)

@dataclass
class CharacterSet:
    """Collection of all characters in a story"""
    characters: Dict[str, CharacterProfile] = field(default_factory=dict)

    def add_character(self, profile: CharacterProfile) -> None:
        """Add character to set"""
        self.characters[profile.name] = profile

    def get_character(self, name: str) -> Optional[CharacterProfile]:
        """Get character by name"""
        return self.characters.get(name)

    def get_all_prompt_strings(self) -> Dict[str, str]:
        """Get all characters as prompt strings"""
        return {
            name: profile.to_prompt_string()
            for name, profile in self.characters.items()
        }
```

#### Image Models (`src/models/image.py`)

```python
from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime

@dataclass
class ImagePrompt:
    """Image generation prompt for a single page"""
    page_number: int
    prompt_text: str
    character_descriptions: Dict[str, str]  # character_name -> description
    art_style: str
    is_approved: bool = False
    edited: bool = False
    original_prompt: Optional[str] = None

    def edit(self, new_prompt: str) -> None:
        """Edit prompt text"""
        if not self.original_prompt:
            self.original_prompt = self.prompt_text
        self.prompt_text = new_prompt
        self.edited = True
        self.is_approved = False

@dataclass
class GeneratedImage:
    """Generated image data"""
    page_number: int
    image_path: str
    prompt_used: str
    generation_timestamp: datetime = field(default_factory=datetime.now)
    is_approved: bool = False
    regeneration_count: int = 0

    def mark_for_regeneration(self) -> None:
        """Mark image for regeneration"""
        self.is_approved = False
        self.regeneration_count += 1

@dataclass
class ImageSet:
    """Collection of all image prompts and generated images"""
    prompts: Dict[int, ImagePrompt] = field(default_factory=dict)  # page_num -> prompt
    images: Dict[int, GeneratedImage] = field(default_factory=dict)  # page_num -> image
    art_style: str = "watercolor children's book illustration"
    all_prompts_approved: bool = False
    all_images_approved: bool = False

    def add_prompt(self, prompt: ImagePrompt) -> None:
        """Add image prompt"""
        self.prompts[prompt.page_number] = prompt

    def add_image(self, image: GeneratedImage) -> None:
        """Add generated image"""
        self.images[image.page_number] = image

    def approve_all_prompts(self) -> None:
        """Approve all prompts at once"""
        for prompt in self.prompts.values():
            prompt.is_approved = True
        self.all_prompts_approved = True

    def approve_all_images(self) -> None:
        """Approve all images at once"""
        for image in self.images.values():
            image.is_approved = True
        self.all_images_approved = True
```

#### Vocabulary Models (`src/models/vocabulary.py`)

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class VocabularyEntry:
    """Single vocabulary word with translation"""
    word: str
    translation: str
    context: Optional[str] = None  # Sentence where it appears
    part_of_speech: Optional[str] = None  # noun, verb, adjective, etc.
    difficulty_level: Optional[str] = None

@dataclass
class VocabularyList:
    """Complete vocabulary list for a story"""
    source_language: str
    target_language: str  # Translation language (e.g., English)
    entries: List[VocabularyEntry] = field(default_factory=list)

    def add_entry(self, entry: VocabularyEntry) -> None:
        """Add vocabulary entry"""
        self.entries.append(entry)

    def get_words_only(self) -> List[str]:
        """Get list of words only"""
        return [entry.word for entry in self.entries]

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for easy lookup"""
        return {entry.word: entry.translation for entry in self.entries}
```

#### Configuration Models (`src/models/config.py`)

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class TextProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    CLAUDE = "claude"

class ImageProvider(Enum):
    DALLE3 = "dall-e-3"
    DALLE2 = "dall-e-2"
    STABLE_DIFFUSION = "stable-diffusion"

@dataclass
class OllamaConfig:
    """Ollama configuration"""
    base_url: str = "http://localhost:11434"
    model: str = "granite4:small-h"
    timeout: int = 120

@dataclass
class OpenAIConfig:
    """OpenAI configuration"""
    api_key: str
    text_model: str = "gpt-4"
    image_model: str = "dall-e-3"
    timeout: int = 120

@dataclass
class ClaudeConfig:
    """Anthropic Claude configuration"""
    api_key: str
    model: str = "claude-sonnet-4-5-20250929"
    timeout: int = 120

@dataclass
class AIProviderConfig:
    """AI provider configuration"""
    text_provider: TextProvider = TextProvider.OLLAMA
    image_provider: ImageProvider = ImageProvider.DALLE3
    ollama: Optional[OllamaConfig] = None
    openai: Optional[OpenAIConfig] = None
    claude: Optional[ClaudeConfig] = None

@dataclass
class StoryParameters:
    """Available story generation parameters (loaded from parameters.json)"""
    languages: List[str]  # Available languages
    complexities: List[str]  # Available complexity levels
    vocabulary_levels: List[str]  # Available vocabulary diversity levels
    age_groups: List[str]  # Available age groups
    page_counts: List[int]  # Available page count options
    genres: List[str]  # Available story genres

@dataclass
class DefaultValues:
    """Default values for story generation (loaded from defaults.json)"""
    language: str
    complexity: str
    vocabulary_diversity: str
    age_group: str
    num_pages: int
    genre: Optional[str] = None

@dataclass
class AppConfig:
    """Application configuration"""
    ai_providers: AIProviderConfig
    parameters: StoryParameters
    defaults: DefaultValues
    auto_save_interval: int = 120  # seconds
    data_directory: str = "./data"
```

#### Project Model (`src/models/project.py`)

```python
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from .story import Story
from .character import CharacterSet
from .image import ImageSet

@dataclass
class Project:
    """Complete story project with all data"""
    id: str
    story: Story
    characters: CharacterSet
    images: ImageSet
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    current_step: int = 1  # 1=story, 2=prompts, 3=images

    def update_timestamp(self) -> None:
        """Update the last modified timestamp"""
        self.updated_at = datetime.now()

    def advance_step(self) -> None:
        """Move to next step"""
        if self.current_step < 3:
            self.current_step += 1
            self.update_timestamp()

    def go_back_step(self) -> None:
        """Go back to previous step"""
        if self.current_step > 1:
            self.current_step -= 1
            self.update_timestamp()
```

---

## 4. Module Interfaces

### 4.1 Service Layer

#### Story Generator Service (`src/services/story_generator.py`)

```python
"""
Story generation orchestration service.
Coordinates AI text generation, vocabulary extraction, and story management.
"""

class StoryGeneratorService:
    def __init__(self, ai_client, vocabulary_analyzer, story_validator):
        """Initialize with dependencies"""

    def generate_story(self, metadata: StoryMetadata) -> Story:
        """
        Generate complete story from metadata.
        Returns Story object with all pages.
        """

    def regenerate_page(self, story: Story, page_number: int) -> Page:
        """
        Regenerate a specific page while maintaining story context.
        Returns updated Page.
        """

    def extract_vocabulary(self, story: Story) -> VocabularyList:
        """
        Extract vocabulary from story and generate translations.
        Returns VocabularyList.
        """
```

**Test File**: `tests/unit/test_services/test_story_generator.py`

#### Image Generator Service (`src/services/image_generator.py`)

```python
"""
Image generation orchestration service.
Coordinates character extraction, prompt generation, and image creation.
"""

class ImageGeneratorService:
    def __init__(self, ai_client, character_extractor, prompt_builder):
        """Initialize with dependencies"""

    def extract_characters(self, story: Story) -> CharacterSet:
        """
        Extract characters from story text.
        Returns CharacterSet with all character profiles.
        """

    def generate_image_prompts(
        self,
        story: Story,
        characters: CharacterSet,
        art_style: str
    ) -> ImageSet:
        """
        Generate image prompts for all pages with character consistency.
        Returns ImageSet with all prompts.
        """

    def regenerate_prompt(
        self,
        story: Story,
        characters: CharacterSet,
        page_number: int,
        art_style: str
    ) -> ImagePrompt:
        """
        Regenerate prompt for a specific page.
        Returns updated ImagePrompt.
        """

    def generate_images(
        self,
        image_set: ImageSet,
        batch_mode: bool = True
    ) -> ImageSet:
        """
        Generate images from prompts.
        Returns ImageSet with generated images.
        """

    def regenerate_image(
        self,
        image_set: ImageSet,
        page_number: int
    ) -> GeneratedImage:
        """
        Regenerate a specific image.
        Returns updated GeneratedImage.
        """
```

**Test File**: `tests/unit/test_services/test_image_generator.py`

### 4.2 Domain Layer

#### Character Extractor (`src/domain/character_extractor.py`)

```python
"""
Extracts character information from story text using AI.
"""

class CharacterExtractor:
    def __init__(self, ai_client):
        """Initialize with AI client"""

    def extract_from_story(self, story_text: str) -> CharacterSet:
        """
        Extract all characters and their descriptions from story.
        Returns CharacterSet with character profiles.
        """

    def create_character_profile(
        self,
        name: str,
        mentions: List[str]
    ) -> CharacterProfile:
        """
        Create detailed character profile from text mentions.
        Returns CharacterProfile.
        """
```

**Test File**: `tests/unit/test_domain/test_character_extractor.py`

#### Vocabulary Analyzer (`src/domain/vocabulary_analyzer.py`)

```python
"""
Analyzes text to extract vocabulary and generate translations.
"""

class VocabularyAnalyzer:
    def __init__(self, ai_client):
        """Initialize with AI client"""

    def extract_vocabulary(
        self,
        text: str,
        source_language: str,
        target_language: str,
        complexity: Complexity
    ) -> VocabularyList:
        """
        Extract key vocabulary from text and translate.
        Returns VocabularyList with translations.
        """

    def filter_by_difficulty(
        self,
        vocab_list: VocabularyList,
        complexity: Complexity
    ) -> VocabularyList:
        """
        Filter vocabulary based on complexity level.
        Returns filtered VocabularyList.
        """
```

**Test File**: `tests/unit/test_domain/test_vocabulary_analyzer.py`

#### Prompt Builder (`src/domain/prompt_builder.py`)

```python
"""
Builds consistent AI prompts for story and image generation.
"""

class PromptBuilder:
    def build_story_prompt(self, metadata: StoryMetadata) -> str:
        """
        Build prompt for story generation.
        Returns formatted prompt string.
        """

    def build_image_prompt(
        self,
        page_text: str,
        characters: Dict[str, str],
        art_style: str,
        page_number: int
    ) -> str:
        """
        Build prompt for image generation with character consistency.
        Returns formatted prompt string.
        """

    def build_character_extraction_prompt(self, story_text: str) -> str:
        """
        Build prompt for character extraction.
        Returns formatted prompt string.
        """

    def build_vocabulary_extraction_prompt(
        self,
        text: str,
        source_language: str,
        target_language: str,
        complexity: Complexity
    ) -> str:
        """
        Build prompt for vocabulary extraction and translation.
        Returns formatted prompt string.
        """
```

**Test File**: `tests/unit/test_domain/test_prompt_builder.py`

### 4.3 AI Integration Layer

#### Base AI Client (`src/ai/base.py`)

```python
"""
Abstract base class for AI clients.
"""

from abc import ABC, abstractmethod

class BaseTextClient(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass

class BaseImageClient(ABC):
    @abstractmethod
    def generate_image(self, prompt: str, **kwargs) -> str:
        """Generate image from prompt, returns image path"""
        pass
```

#### Ollama Client (`src/ai/ollama_client.py`)

```python
"""
Ollama local LLM client implementation.
"""

class OllamaClient(BaseTextClient):
    def __init__(self, config: OllamaConfig):
        """Initialize Ollama client"""

    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Ollama.
        Returns generated text.
        """

    def test_connection(self) -> bool:
        """
        Test connection to Ollama server.
        Returns True if successful.
        """
```

**Test File**: `tests/unit/test_ai/test_ollama_client.py`

#### OpenAI Client (`src/ai/openai_client.py`)

```python
"""
OpenAI API client for GPT (text) and DALL-E (images).
"""

class OpenAITextClient(BaseTextClient):
    def __init__(self, config: OpenAIConfig):
        """Initialize OpenAI text client"""

    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using GPT"""

class OpenAIImageClient(BaseImageClient):
    def __init__(self, config: OpenAIConfig):
        """Initialize OpenAI image client"""

    def generate_image(self, prompt: str, **kwargs) -> str:
        """
        Generate image using DALL-E.
        Returns local file path to saved image.
        """
```

**Test File**: `tests/unit/test_ai/test_openai_client.py`

---

## 5. Test-Driven Development (TDD) Workflow

### 5.1 TDD Principles

1. **Write test first** - Define expected behavior before implementation
2. **Run test (should fail)** - Verify test works and fails as expected
3. **Implement minimal code** - Write just enough to pass the test
4. **Run test (should pass)** - Verify implementation works
5. **Refactor** - Clean up code while keeping tests passing
6. **Repeat** - Continue with next feature

### 5.2 Test Structure

Each module should have corresponding test file with:
- **Unit tests** - Test individual functions/methods in isolation
- **Integration tests** - Test module interactions
- **Fixtures** - Reusable test data and mocks

### 5.3 Example Test Template

#### Test File: `tests/unit/test_models/test_story.py`

```python
"""
Unit tests for Story model.
Write these tests BEFORE implementing the Story class.
"""

import pytest
from datetime import datetime
from src.models.story import Story, Page, StoryMetadata, Complexity, VocabularyDiversity

class TestPage:
    """Test Page class"""

    def test_page_creation(self):
        """Test creating a new page"""
        page = Page(page_number=1, text="Once upon a time...")
        assert page.page_number == 1
        assert page.text == "Once upon a time..."
        assert page.is_approved == False
        assert page.edited == False

    def test_page_edit(self):
        """Test editing a page"""
        page = Page(page_number=1, text="Original text")
        page.edit("New text")
        assert page.text == "New text"
        assert page.original_text == "Original text"
        assert page.edited == True
        assert page.is_approved == False

    def test_page_edit_clears_approval(self):
        """Test that editing clears approval status"""
        page = Page(page_number=1, text="Original")
        page.is_approved = True
        page.edit("New")
        assert page.is_approved == False

class TestStory:
    """Test Story class"""

    @pytest.fixture
    def sample_metadata(self):
        """Fixture for sample story metadata"""
        return StoryMetadata(
            prompt="A brave girl explores a forest",
            language="Spanish",
            complexity=Complexity.BEGINNER,
            vocabulary_diversity=VocabularyDiversity.MEDIUM,
            target_age_group="4-7",
            num_pages=3
        )

    @pytest.fixture
    def sample_story(self, sample_metadata):
        """Fixture for sample story"""
        pages = [
            Page(page_number=1, text="Page 1 text"),
            Page(page_number=2, text="Page 2 text"),
            Page(page_number=3, text="Page 3 text")
        ]
        return Story(
            id="story-001",
            title="Luna's Adventure",
            metadata=sample_metadata,
            pages=pages
        )

    def test_story_creation(self, sample_story):
        """Test creating a story"""
        assert sample_story.id == "story-001"
        assert sample_story.title == "Luna's Adventure"
        assert len(sample_story.pages) == 3
        assert sample_story.all_pages_approved == False

    def test_approve_all_pages(self, sample_story):
        """Test approving all pages at once"""
        sample_story.approve_all_pages()
        assert sample_story.all_pages_approved == True
        for page in sample_story.pages:
            assert page.is_approved == True

    def test_get_page(self, sample_story):
        """Test retrieving specific page"""
        page = sample_story.get_page(2)
        assert page is not None
        assert page.page_number == 2
        assert page.text == "Page 2 text"

    def test_get_page_not_found(self, sample_story):
        """Test retrieving non-existent page"""
        page = sample_story.get_page(99)
        assert page is None

    def test_get_full_text(self, sample_story):
        """Test getting complete story text"""
        full_text = sample_story.get_full_text()
        assert "Page 1 text" in full_text
        assert "Page 2 text" in full_text
        assert "Page 3 text" in full_text
```

### 5.4 Testing Requirements by Module

#### Models (`src/models/`)
- **Test creation and initialization**
- **Test all methods and properties**
- **Test data validation**
- **Test edge cases**

**Priority**: HIGH - Models are foundation

#### Services (`src/services/`)
- **Mock AI clients and dependencies**
- **Test orchestration logic**
- **Test error handling**
- **Test business rules**

**Priority**: HIGH - Core business logic

#### Domain (`src/domain/`)
- **Mock AI interactions**
- **Test extraction/analysis logic**
- **Test prompt building**
- **Test validation rules**

**Priority**: HIGH - Critical functionality

#### AI Clients (`src/ai/`)
- **Mock external API calls**
- **Test request/response formatting**
- **Test error handling and retries**
- **Test configuration**

**Priority**: MEDIUM - Integration layer

#### Repositories (`src/repositories/`)
- **Test save/load operations**
- **Test file system operations (use temp directories)**
- **Test data serialization**
- **Test error handling**
- **Test JSON configuration loading/validation**

**Priority**: MEDIUM - Data persistence

---

## 6. Configuration Files (JSON)

### 6.1 Configuration File Structure

All configuration is stored in JSON files in the `data/config/` directory. This allows easy customization without modifying code.

#### `data/config/config.json` - AI Provider Configuration

```json
{
  "text_provider": "ollama",
  "image_provider": "dall-e-3",
  "ollama": {
    "base_url": "http://localhost:11434",
    "model": "granite4:small-h",
    "timeout": 120
  },
  "openai": {
    "api_key": "",
    "text_model": "gpt-4",
    "image_model": "dall-e-3",
    "timeout": 120
  },
  "claude": {
    "api_key": "",
    "model": "claude-sonnet-4-5-20250929",
    "timeout": 120
  }
}
```

#### `data/config/parameters.json` - Story Parameters

```json
{
  "languages": [
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese",
    "Mandarin",
    "Japanese",
    "Korean",
    "Arabic",
    "Russian",
    "English"
  ],
  "complexities": [
    "beginner",
    "intermediate",
    "advanced"
  ],
  "vocabulary_levels": [
    "low",
    "medium",
    "high"
  ],
  "age_groups": [
    "0-3 years",
    "4-7 years",
    "8-12 years",
    "13+ years"
  ],
  "page_counts": [
    3,
    5,
    8,
    10,
    15,
    20
  ],
  "genres": [
    "Adventure",
    "Fantasy",
    "Science Fiction",
    "Mystery",
    "Friendship",
    "Family",
    "Animals",
    "Nature",
    "Educational",
    "Bedtime Story"
  ],
  "art_styles": [
    "watercolor children's book illustration",
    "digital cartoon illustration",
    "pencil sketch style",
    "oil painting style",
    "anime/manga style",
    "realistic digital art",
    "whimsical illustration",
    "vintage storybook style"
  ]
}
```

#### `data/config/defaults.json` - Default Values

```json
{
  "language": "Spanish",
  "complexity": "beginner",
  "vocabulary_diversity": "medium",
  "age_group": "4-7 years",
  "num_pages": 5,
  "genre": "Adventure",
  "art_style": "watercolor children's book illustration"
}
```

### 6.2 Configuration Repository Interface

#### Config Repository (`src/repositories/config_repository.py`)

```python
"""
Configuration repository for loading/saving JSON configuration files.
"""

import json
import os
from typing import Dict, Any
from pathlib import Path
from src.models.config import (
    AppConfig,
    AIProviderConfig,
    StoryParameters,
    DefaultValues,
    OllamaConfig,
    OpenAIConfig,
    ClaudeConfig,
    TextProvider,
    ImageProvider
)

class ConfigRepository:
    def __init__(self, config_dir: str = "./data/config"):
        """Initialize with config directory path"""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "config.json"
        self.parameters_file = self.config_dir / "parameters.json"
        self.defaults_file = self.config_dir / "defaults.json"

    def load_app_config(self) -> AppConfig:
        """
        Load complete application configuration from JSON files.
        Returns AppConfig with all settings.
        """
        ai_config = self._load_ai_config()
        parameters = self._load_parameters()
        defaults = self._load_defaults()

        return AppConfig(
            ai_providers=ai_config,
            parameters=parameters,
            defaults=defaults
        )

    def save_app_config(self, config: AppConfig) -> None:
        """
        Save complete application configuration to JSON files.
        """
        self._save_ai_config(config.ai_providers)
        self._save_parameters(config.parameters)
        self._save_defaults(config.defaults)

    def _load_ai_config(self) -> AIProviderConfig:
        """Load AI provider configuration"""
        if not self.config_file.exists():
            return self._create_default_ai_config()

        with open(self.config_file, 'r') as f:
            data = json.load(f)

        return AIProviderConfig(
            text_provider=TextProvider(data.get("text_provider", "ollama")),
            image_provider=ImageProvider(data.get("image_provider", "dall-e-3")),
            ollama=OllamaConfig(**data["ollama"]) if "ollama" in data else None,
            openai=OpenAIConfig(**data["openai"]) if "openai" in data else None,
            claude=ClaudeConfig(**data["claude"]) if "claude" in data else None
        )

    def _load_parameters(self) -> StoryParameters:
        """Load story parameters"""
        if not self.parameters_file.exists():
            return self._create_default_parameters()

        with open(self.parameters_file, 'r') as f:
            data = json.load(f)

        return StoryParameters(**data)

    def _load_defaults(self) -> DefaultValues:
        """Load default values"""
        if not self.defaults_file.exists():
            return self._create_default_values()

        with open(self.defaults_file, 'r') as f:
            data = json.load(f)

        return DefaultValues(**data)

    def _create_default_ai_config(self) -> AIProviderConfig:
        """Create and save default AI configuration"""
        config = AIProviderConfig(
            text_provider=TextProvider.OLLAMA,
            image_provider=ImageProvider.DALLE3,
            ollama=OllamaConfig(),
            openai=OpenAIConfig(api_key=""),
            claude=ClaudeConfig(api_key="")
        )
        self._save_ai_config(config)
        return config

    def _create_default_parameters(self) -> StoryParameters:
        """Create and save default parameters"""
        params = StoryParameters(
            languages=["Spanish", "French", "German", "Italian", "Portuguese",
                      "Mandarin", "Japanese", "Korean", "Arabic", "Russian", "English"],
            complexities=["beginner", "intermediate", "advanced"],
            vocabulary_levels=["low", "medium", "high"],
            age_groups=["0-3 years", "4-7 years", "8-12 years", "13+ years"],
            page_counts=[3, 5, 8, 10, 15, 20],
            genres=["Adventure", "Fantasy", "Science Fiction", "Mystery",
                   "Friendship", "Family", "Animals", "Nature",
                   "Educational", "Bedtime Story"]
        )
        self._save_parameters(params)
        return params

    def _create_default_values(self) -> DefaultValues:
        """Create and save default values"""
        defaults = DefaultValues(
            language="Spanish",
            complexity="beginner",
            vocabulary_diversity="medium",
            age_group="4-7 years",
            num_pages=5,
            genre="Adventure"
        )
        self._save_defaults(defaults)
        return defaults

    def _save_ai_config(self, config: AIProviderConfig) -> None:
        """Save AI configuration to JSON"""
        data = {
            "text_provider": config.text_provider.value,
            "image_provider": config.image_provider.value
        }

        if config.ollama:
            data["ollama"] = {
                "base_url": config.ollama.base_url,
                "model": config.ollama.model,
                "timeout": config.ollama.timeout
            }

        if config.openai:
            data["openai"] = {
                "api_key": config.openai.api_key,
                "text_model": config.openai.text_model,
                "image_model": config.openai.image_model,
                "timeout": config.openai.timeout
            }

        if config.claude:
            data["claude"] = {
                "api_key": config.claude.api_key,
                "model": config.claude.model,
                "timeout": config.claude.timeout
            }

        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _save_parameters(self, params: StoryParameters) -> None:
        """Save parameters to JSON"""
        data = {
            "languages": params.languages,
            "complexities": params.complexities,
            "vocabulary_levels": params.vocabulary_levels,
            "age_groups": params.age_groups,
            "page_counts": params.page_counts,
            "genres": params.genres
        }

        with open(self.parameters_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _save_defaults(self, defaults: DefaultValues) -> None:
        """Save defaults to JSON"""
        data = {
            "language": defaults.language,
            "complexity": defaults.complexity,
            "vocabulary_diversity": defaults.vocabulary_diversity,
            "age_group": defaults.age_group,
            "num_pages": defaults.num_pages
        }

        if defaults.genre:
            data["genre"] = defaults.genre

        with open(self.defaults_file, 'w') as f:
            json.dump(data, f, indent=2)

    def update_api_key(self, provider: str, api_key: str) -> None:
        """
        Update API key for a specific provider.
        provider: 'openai' or 'claude'
        """
        config = self._load_ai_config()

        if provider == "openai" and config.openai:
            config.openai.api_key = api_key
        elif provider == "claude" and config.claude:
            config.claude.api_key = api_key
        else:
            raise ValueError(f"Unknown provider: {provider}")

        self._save_ai_config(config)

    def validate_configuration(self) -> Dict[str, bool]:
        """
        Validate configuration files exist and are valid.
        Returns dict with validation results.
        """
        results = {
            "config_exists": self.config_file.exists(),
            "parameters_exists": self.parameters_file.exists(),
            "defaults_exists": self.defaults_file.exists(),
            "config_valid": False,
            "parameters_valid": False,
            "defaults_valid": False
        }

        try:
            self._load_ai_config()
            results["config_valid"] = True
        except Exception:
            pass

        try:
            self._load_parameters()
            results["parameters_valid"] = True
        except Exception:
            pass

        try:
            self._load_defaults()
            results["defaults_valid"] = True
        except Exception:
            pass

        return results
```

**Test File**: `tests/unit/test_repositories/test_config_repository.py`

```python
"""
Unit tests for ConfigRepository.
Write these tests BEFORE implementing the ConfigRepository class.
"""

import pytest
import json
from pathlib import Path
from src.repositories.config_repository import ConfigRepository
from src.models.config import (
    AppConfig,
    StoryParameters,
    DefaultValues,
    TextProvider,
    ImageProvider
)

class TestConfigRepository:
    """Test ConfigRepository class"""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Fixture for temporary config directory"""
        return tmp_path / "config"

    @pytest.fixture
    def config_repo(self, temp_config_dir):
        """Fixture for ConfigRepository"""
        return ConfigRepository(str(temp_config_dir))

    def test_initialization_creates_directory(self, temp_config_dir):
        """Test that initialization creates config directory"""
        repo = ConfigRepository(str(temp_config_dir))
        assert temp_config_dir.exists()

    def test_load_creates_defaults_if_missing(self, config_repo):
        """Test loading creates default configs if files don't exist"""
        config = config_repo.load_app_config()

        assert config is not None
        assert config.ai_providers is not None
        assert config.parameters is not None
        assert config.defaults is not None

    def test_save_and_load_ai_config(self, config_repo):
        """Test saving and loading AI configuration"""
        config = config_repo.load_app_config()

        # Modify configuration
        if config.ai_providers.openai:
            config.ai_providers.openai.api_key = "test-key-123"

        # Save and reload
        config_repo.save_app_config(config)
        reloaded = config_repo.load_app_config()

        assert reloaded.ai_providers.openai.api_key == "test-key-123"

    def test_save_and_load_parameters(self, config_repo, temp_config_dir):
        """Test saving and loading story parameters"""
        params = StoryParameters(
            languages=["Spanish", "French"],
            complexities=["beginner", "advanced"],
            vocabulary_levels=["low", "high"],
            age_groups=["4-7 years"],
            page_counts=[5, 10],
            genres=["Adventure"]
        )

        config = AppConfig(
            ai_providers=config_repo._create_default_ai_config(),
            parameters=params,
            defaults=config_repo._create_default_values()
        )

        config_repo.save_app_config(config)
        reloaded = config_repo.load_app_config()

        assert reloaded.parameters.languages == ["Spanish", "French"]
        assert reloaded.parameters.page_counts == [5, 10]

    def test_update_api_key(self, config_repo):
        """Test updating API key"""
        config_repo.update_api_key("openai", "new-api-key")

        config = config_repo.load_app_config()
        assert config.ai_providers.openai.api_key == "new-api-key"

    def test_validate_configuration(self, config_repo):
        """Test configuration validation"""
        # Create configs
        config_repo.load_app_config()

        results = config_repo.validate_configuration()

        assert results["config_exists"] is True
        assert results["parameters_exists"] is True
        assert results["defaults_exists"] is True
        assert results["config_valid"] is True
        assert results["parameters_valid"] is True
        assert results["defaults_valid"] is True

    def test_invalid_json_handling(self, config_repo, temp_config_dir):
        """Test handling of invalid JSON files"""
        # Create invalid JSON file
        config_file = temp_config_dir / "config" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text("{invalid json}")

        results = config_repo.validate_configuration()
        assert results["config_valid"] is False
```

### 6.3 Benefits of JSON Configuration

**Advantages:**
1. **No Code Changes**: Update languages, parameters without touching code
2. **User Customization**: Users can easily customize options
3. **Version Control**: Easy to track configuration changes
4. **Deployment**: Different configs for dev/test/prod
5. **Backup**: Easy to backup/restore configurations
6. **Validation**: Can validate configs at startup

**Configuration Loading:**
```python
# At application startup (app.py)
config_repo = ConfigRepository("./data/config")
app_config = config_repo.load_app_config()

# Use config throughout application
story_service = StoryGeneratorService(
    ai_client=ai_factory.create_text_client(app_config.ai_providers),
    available_languages=app_config.parameters.languages,
    defaults=app_config.defaults
)
```

---

## 7. Module Dependencies

### 6.1 Dependency Graph

```
Web Routes
    ↓
Services (story_generator, image_generator, export_service)
    ↓
Domain (character_extractor, vocabulary_analyzer, prompt_builder)
    ↓
AI Clients (ollama_client, openai_client)
    ↓
Repositories (project_repository, config_repository, image_storage)
```

### 6.2 Dependency Injection

Use constructor injection for all dependencies:

```python
# Good - Dependencies injected
class StoryGeneratorService:
    def __init__(self, ai_client: BaseTextClient, vocabulary_analyzer: VocabularyAnalyzer):
        self.ai_client = ai_client
        self.vocabulary_analyzer = vocabulary_analyzer

# Bad - Hard-coded dependencies
class StoryGeneratorService:
    def __init__(self):
        self.ai_client = OllamaClient()  # Hard to test!
```

### 6.3 Factory Pattern for AI Clients

```python
# src/ai/ai_factory.py

class AIClientFactory:
    """Factory for creating AI clients based on configuration"""

    @staticmethod
    def create_text_client(config: AIProviderConfig) -> BaseTextClient:
        """Create text generation client"""
        if config.text_provider == TextProvider.OLLAMA:
            return OllamaClient(config.ollama)
        elif config.text_provider == TextProvider.OPENAI:
            return OpenAITextClient(config.openai)
        elif config.text_provider == TextProvider.CLAUDE:
            return ClaudeClient(config.claude)
        else:
            raise ValueError(f"Unknown text provider: {config.text_provider}")

    @staticmethod
    def create_image_client(config: AIProviderConfig) -> BaseImageClient:
        """Create image generation client"""
        if config.image_provider == ImageProvider.DALLE3:
            return OpenAIImageClient(config.openai)
        # Add other image providers...
        else:
            raise ValueError(f"Unknown image provider: {config.image_provider}")
```

---

## 7. Development Phases

### Phase 1: Foundation (Week 1)
1. **Set up project structure**
2. **Define all data models** (`src/models/`)
3. **Write model tests** (`tests/unit/test_models/`)
4. **Implement models** (make tests pass)
5. **Set up configuration management**

**Deliverable**: All data structures defined and tested

### Phase 2: AI Integration (Week 2)
1. **Write AI client tests** (`tests/unit/test_ai/`)
2. **Implement Ollama client**
3. **Implement OpenAI clients** (text + image)
4. **Implement AI factory**
5. **Test with real APIs** (integration tests)

**Deliverable**: Working AI integrations

### Phase 3: Domain Logic (Week 2-3)
1. **Write domain tests** (`tests/unit/test_domain/`)
2. **Implement character extractor**
3. **Implement vocabulary analyzer**
4. **Implement prompt builder**
5. **Implement story validator**

**Deliverable**: Core domain logic working

### Phase 4: Services (Week 3-4)
1. **Write service tests** (`tests/unit/test_services/`)
2. **Implement story generator service**
3. **Implement image generator service**
4. **Implement export service**
5. **Implement project manager**

**Deliverable**: Complete business logic layer

### Phase 5: Persistence (Week 4)
1. **Write repository tests**
2. **Implement project repository**
3. **Implement config repository**
4. **Implement image storage**

**Deliverable**: Data persistence working

### Phase 6: Web Interface (Week 5)
1. **Create Flask/FastAPI routes**
2. **Create HTML templates**
3. **Add JavaScript for interactivity**
4. **Integrate all components**

**Deliverable**: Working web application

### Phase 7: Testing & Polish (Week 6)
1. **Integration tests**
2. **End-to-end tests**
3. **Bug fixes**
4. **Performance optimization**
5. **Documentation**

**Deliverable**: Production-ready application

---

## 8. Key Design Decisions

### 8.1 Why Modular Approach?
- **Testability**: Each module can be tested in isolation
- **Maintainability**: Clear boundaries and responsibilities
- **Flexibility**: Easy to swap implementations (e.g., different AI providers)
- **Reusability**: Modules can be used independently

### 8.2 Why Direct Module Calls (No APIs)?
- **Simplicity**: No network overhead for local communication
- **Performance**: Direct function calls are faster
- **Type Safety**: Python type hints work across modules
- **Debugging**: Easier to trace execution flow

### 8.3 Why Test-Driven Development?
- **Better Design**: Writing tests first leads to better API design
- **Confidence**: Tests verify functionality works as expected
- **Refactoring Safety**: Can refactor with confidence
- **Documentation**: Tests serve as usage examples

### 8.4 Why Dataclasses for Models?
- **Immutability Options**: Can make fields frozen if needed
- **Type Safety**: Built-in type checking
- **Clean Syntax**: Less boilerplate than regular classes
- **Serialization**: Easy to convert to/from JSON

---

## 9. Running Tests

### 9.1 Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_models/test_story.py

# Run specific test class
pytest tests/unit/test_models/test_story.py::TestStory

# Run specific test method
pytest tests/unit/test_models/test_story.py::TestStory::test_story_creation

# Run tests with verbose output
pytest -v

# Run tests in parallel (faster)
pytest -n auto
```

### 9.2 Pytest Configuration (`pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

### 9.3 Test Fixtures (`tests/conftest.py`)

```python
"""
Shared pytest fixtures for all tests.
"""

import pytest
from src.models.config import OllamaConfig, OpenAIConfig, AIProviderConfig
from src.ai.ollama_client import OllamaClient
from src.ai.openai_client import OpenAITextClient, OpenAIImageClient

@pytest.fixture
def ollama_config():
    """Fixture for Ollama configuration"""
    return OllamaConfig(
        base_url="http://localhost:11434",
        model="granite4:small-h"
    )

@pytest.fixture
def openai_config():
    """Fixture for OpenAI configuration"""
    return OpenAIConfig(
        api_key="test-api-key",
        text_model="gpt-4",
        image_model="dall-e-3"
    )

@pytest.fixture
def mock_ollama_client(mocker, ollama_config):
    """Fixture for mocked Ollama client"""
    client = OllamaClient(ollama_config)
    mocker.patch.object(client, 'generate_text', return_value="Mocked response")
    return client

@pytest.fixture
def temp_data_dir(tmp_path):
    """Fixture for temporary data directory"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return str(data_dir)
```

---

## 10. Next Steps

1. **Review this architecture** with stakeholders
2. **Set up project structure** (create directories and files)
3. **Install dependencies** (create requirements.txt)
4. **Start Phase 1** (define and test data models)
5. **Follow TDD workflow** for each module

---

**Document Version:** 1.0
**Last Updated:** 2026-01-12
**Status:** Ready for Implementation
