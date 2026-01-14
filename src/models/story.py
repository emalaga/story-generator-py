"""
Story data models for the story generator application.

These models define the structure for story metadata, pages, and complete stories.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.character import Character


@dataclass
class StoryMetadata:
    """Metadata for a story"""
    title: str
    language: str
    complexity: str
    vocabulary_diversity: str
    age_group: str
    num_pages: int
    genre: Optional[str] = None
    art_style: Optional[str] = None
    user_prompt: Optional[str] = None


@dataclass
class StoryPage:
    """A single page in a story"""
    page_number: int
    text: str
    image_url: Optional[str] = None
    image_prompt: Optional[str] = None


@dataclass
class Story:
    """Complete story with metadata and pages"""
    id: str
    metadata: StoryMetadata
    pages: List[StoryPage]
    vocabulary: List[str] = field(default_factory=list)
    characters: Optional[List["Character"]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
