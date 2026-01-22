"""
Art Bible data model for maintaining visual consistency across story illustrations.

The Art Bible defines the overall visual style, color palette, lighting, and
brush techniques that should be used consistently throughout the story.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ArtBible:
    """
    Art Bible defines the visual style guidelines for a story.

    This includes reference images and prompts that establish the artistic
    direction for all illustrations in the story.
    """

    # Generated prompt for creating the art bible reference image
    prompt: str

    # URL or path to the generated art bible reference image
    image_url: Optional[str] = None

    # Local file path if image has been saved (relative to storage directory)
    local_image_path: Optional[str] = None

    # Style description (extracted from story metadata)
    art_style: str = "cartoon"

    # Additional style notes (optional, user-editable)
    style_notes: Optional[str] = None

    # Color palette description
    color_palette: Optional[str] = None

    # Lighting style description
    lighting_style: Optional[str] = None

    # Brush/texture description
    brush_technique: Optional[str] = None


@dataclass
class CharacterReference:
    """
    Character Reference image for maintaining character consistency.

    Each character gets a dedicated reference image that shows their
    appearance, which is used to ensure consistency across all story pages.
    """

    # Character name (must match character profile name)
    character_name: str

    # Generated prompt for creating the character reference image
    prompt: str

    # URL or path to the generated character reference image
    image_url: Optional[str] = None

    # Local file path if image has been saved (relative to storage directory)
    local_image_path: Optional[str] = None

    # Character species (from character profile)
    species: Optional[str] = None

    # Physical description (from character profile)
    physical_description: Optional[str] = None

    # Clothing description (from character profile)
    clothing: Optional[str] = None

    # Distinctive features (from character profile)
    distinctive_features: Optional[str] = None
