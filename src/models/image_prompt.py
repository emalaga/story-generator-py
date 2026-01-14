"""
Image prompt data models for the story generator application.

These models define the structure for image generation prompts that ensure
visual consistency across all story illustrations, especially for characters.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from src.models.character import CharacterProfile


@dataclass
class ImagePrompt:
    """
    A complete image generation prompt for a story page.

    This model combines scene description, art style, character profiles,
    and atmospheric details to generate consistent illustrations.
    """
    page_number: int
    scene_description: str
    art_style: str
    characters: List[CharacterProfile] = field(default_factory=list)
    lighting: Optional[str] = None
    mood: Optional[str] = None
    additional_details: Optional[str] = None
