"""
Story data models for the story generator application.

These models define the structure for story metadata, pages, and complete stories.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.character import CharacterProfile
    from src.models.art_bible import ArtBible, CharacterReference


@dataclass
class PDFOptions:
    """Options for PDF export"""
    font: str = "Helvetica"
    font_size: int = 12
    layout: str = "portrait"  # portrait or landscape
    page_size: str = "letter"  # letter, a4, a5
    image_placement: str = "top"  # top, bottom, left, right, inner, outer
    image_size: str = "medium"  # small, medium, large, full
    include_title_page: bool = True
    show_page_numbers: bool = True


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
    words_per_page: Optional[int] = 50


@dataclass
class StoryPage:
    """A single page in a story"""
    page_number: int
    text: str
    image_url: Optional[str] = None
    image_prompt: Optional[str] = None
    local_image_path: Optional[str] = None


@dataclass
class CoverPage:
    """Cover page for a story book"""
    image_prompt: Optional[str] = None
    image_url: Optional[str] = None
    local_image_path: Optional[str] = None


@dataclass
class Story:
    """Complete story with metadata and pages"""
    id: str
    metadata: StoryMetadata
    pages: List[StoryPage]
    vocabulary: List[str] = field(default_factory=list)
    characters: Optional[List["CharacterProfile"]] = None
    art_bible: Optional["ArtBible"] = None
    character_references: Optional[List["CharacterReference"]] = None
    cover_page: Optional[CoverPage] = None  # Optional cover page for the book
    image_session_id: Optional[str] = None  # OpenAI response ID for conversation continuity
    pdf_options: Optional[PDFOptions] = None  # PDF export options
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
