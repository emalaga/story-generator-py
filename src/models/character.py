"""
Character data models for the story generator application.

These models define the structure for characters in stories and their
detailed profiles used for maintaining visual consistency in images.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Character:
    """
    A character that appears in a story.

    This is a simple reference to a character with basic information
    used within the story text.
    """
    name: str
    description: str
    role: Optional[str] = None  # e.g., "protagonist", "antagonist", "supporting", "mentor"


@dataclass
class CharacterProfile:
    """
    Detailed character profile for image generation consistency.

    This profile contains all the visual details needed to ensure
    the character appears consistently across all story illustrations.
    """
    name: str
    species: str
    physical_description: str
    clothing: Optional[str] = None
    distinctive_features: Optional[str] = None
    personality_traits: Optional[str] = None
