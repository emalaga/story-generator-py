"""
Project data models for the story generator application.

These models define the structure for complete story projects including
story content, character profiles, image prompts, and project status.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List

from src.models.story import Story
from src.models.character import CharacterProfile
from src.models.image_prompt import ImagePrompt


class ProjectStatus(str, Enum):
    """Project workflow status"""
    DRAFT = "draft"
    STORY_GENERATED = "story_generated"
    PROMPTS_GENERATED = "prompts_generated"
    IMAGES_GENERATED = "images_generated"
    COMPLETED = "completed"


@dataclass
class Project:
    """
    A complete story generation project.

    This model represents the entire project lifecycle from draft to completion,
    including the story, character profiles for consistency, and image prompts.
    """
    id: str
    name: str
    story: Story
    status: ProjectStatus
    character_profiles: List[CharacterProfile] = field(default_factory=list)
    image_prompts: List[ImagePrompt] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
