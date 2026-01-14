"""
Unit tests for Story Models.
Write these tests BEFORE implementing the models (TDD approach).
"""

import pytest
from datetime import datetime
from typing import List, Optional


class TestStoryMetadata:
    """Test StoryMetadata dataclass"""

    def test_story_metadata_creation(self):
        """Test creating StoryMetadata with all fields"""
        from src.models.story import StoryMetadata

        metadata = StoryMetadata(
            title="The Magic Forest",
            language="Spanish",
            complexity="beginner",
            vocabulary_diversity="medium",
            age_group="4-7 years",
            num_pages=5,
            genre="Adventure",
            art_style="watercolor children's book illustration",
            user_prompt="A story about a brave squirrel"
        )

        assert metadata.title == "The Magic Forest"
        assert metadata.language == "Spanish"
        assert metadata.complexity == "beginner"
        assert metadata.vocabulary_diversity == "medium"
        assert metadata.age_group == "4-7 years"
        assert metadata.num_pages == 5
        assert metadata.genre == "Adventure"
        assert metadata.art_style == "watercolor children's book illustration"
        assert metadata.user_prompt == "A story about a brave squirrel"

    def test_story_metadata_optional_genre(self):
        """Test StoryMetadata with optional genre"""
        from src.models.story import StoryMetadata

        metadata = StoryMetadata(
            title="Simple Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="0-3 years",
            num_pages=3,
            user_prompt="A bedtime story"
        )

        assert metadata.genre is None
        assert metadata.art_style is None

    def test_story_metadata_optional_user_prompt(self):
        """Test StoryMetadata with optional user_prompt"""
        from src.models.story import StoryMetadata

        metadata = StoryMetadata(
            title="Auto Story",
            language="French",
            complexity="intermediate",
            vocabulary_diversity="high",
            age_group="8-12 years",
            num_pages=10,
            genre="Fantasy"
        )

        assert metadata.user_prompt is None


class TestStoryPage:
    """Test StoryPage dataclass"""

    def test_story_page_creation(self):
        """Test creating StoryPage with all fields"""
        from src.models.story import StoryPage

        page = StoryPage(
            page_number=1,
            text="Once upon a time in a magical forest...",
            image_url="/data/images/story123/page1.png",
            image_prompt="A magical forest with tall trees"
        )

        assert page.page_number == 1
        assert page.text == "Once upon a time in a magical forest..."
        assert page.image_url == "/data/images/story123/page1.png"
        assert page.image_prompt == "A magical forest with tall trees"

    def test_story_page_without_image(self):
        """Test StoryPage without image (not yet generated)"""
        from src.models.story import StoryPage

        page = StoryPage(
            page_number=2,
            text="The brave squirrel climbed the tree."
        )

        assert page.page_number == 2
        assert page.text == "The brave squirrel climbed the tree."
        assert page.image_url is None
        assert page.image_prompt is None

    def test_story_page_with_prompt_no_image(self):
        """Test StoryPage with prompt but no image yet"""
        from src.models.story import StoryPage

        page = StoryPage(
            page_number=3,
            text="She found a golden acorn.",
            image_prompt="A squirrel holding a shiny golden acorn"
        )

        assert page.image_url is None
        assert page.image_prompt == "A squirrel holding a shiny golden acorn"


class TestStory:
    """Test Story dataclass"""

    def test_story_creation(self):
        """Test creating a complete Story"""
        from src.models.story import Story, StoryMetadata, StoryPage

        metadata = StoryMetadata(
            title="The Magic Forest",
            language="Spanish",
            complexity="beginner",
            vocabulary_diversity="medium",
            age_group="4-7 years",
            num_pages=3,
            genre="Adventure",
            user_prompt="A story about a brave squirrel"
        )

        pages = [
            StoryPage(
                page_number=1,
                text="Había una vez un bosque mágico.",
                image_url="/images/page1.png",
                image_prompt="A magical forest"
            ),
            StoryPage(
                page_number=2,
                text="Una ardilla valiente vivía allí.",
                image_url="/images/page2.png",
                image_prompt="A brave squirrel"
            ),
            StoryPage(
                page_number=3,
                text="Ella encontró una bellota dorada.",
                image_url="/images/page3.png",
                image_prompt="A golden acorn"
            ),
        ]

        story = Story(
            id="story-123",
            metadata=metadata,
            pages=pages,
            vocabulary=["bosque", "ardilla", "valiente", "bellota", "dorada"],
            characters=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        assert story.id == "story-123"
        assert story.metadata == metadata
        assert len(story.pages) == 3
        assert len(story.vocabulary) == 5
        assert story.characters is None
        assert isinstance(story.created_at, datetime)
        assert isinstance(story.updated_at, datetime)

    def test_story_minimal(self):
        """Test Story with minimal required fields"""
        from src.models.story import Story, StoryMetadata, StoryPage

        metadata = StoryMetadata(
            title="Simple Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="0-3 years",
            num_pages=1,
            user_prompt="A simple story"
        )

        page = StoryPage(
            page_number=1,
            text="The end."
        )

        story = Story(
            id="story-456",
            metadata=metadata,
            pages=[page]
        )

        assert story.id == "story-456"
        assert story.metadata == metadata
        assert len(story.pages) == 1
        assert story.vocabulary == []
        assert story.characters is None
        assert isinstance(story.created_at, datetime)
        assert isinstance(story.updated_at, datetime)

    def test_story_with_characters(self):
        """Test Story with character list"""
        from src.models.story import Story, StoryMetadata, StoryPage

        metadata = StoryMetadata(
            title="Character Story",
            language="English",
            complexity="intermediate",
            vocabulary_diversity="medium",
            age_group="4-7 years",
            num_pages=2,
            user_prompt="A story with characters"
        )

        pages = [
            StoryPage(page_number=1, text="Page 1"),
            StoryPage(page_number=2, text="Page 2"),
        ]

        # Character objects will be defined in test_character.py
        # For now, just test that characters field can hold a list
        story = Story(
            id="story-789",
            metadata=metadata,
            pages=pages,
            characters=[]  # Empty list for now
        )

        assert story.characters == []

    def test_story_pages_ordered(self):
        """Test that story pages maintain order"""
        from src.models.story import Story, StoryMetadata, StoryPage

        metadata = StoryMetadata(
            title="Ordered Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=5,
            user_prompt="Test story"
        )

        pages = [
            StoryPage(page_number=1, text="First"),
            StoryPage(page_number=2, text="Second"),
            StoryPage(page_number=3, text="Third"),
            StoryPage(page_number=4, text="Fourth"),
            StoryPage(page_number=5, text="Fifth"),
        ]

        story = Story(
            id="story-order",
            metadata=metadata,
            pages=pages
        )

        assert story.pages[0].page_number == 1
        assert story.pages[0].text == "First"
        assert story.pages[4].page_number == 5
        assert story.pages[4].text == "Fifth"

    def test_story_empty_pages_list(self):
        """Test Story can be created with empty pages (during generation)"""
        from src.models.story import Story, StoryMetadata

        metadata = StoryMetadata(
            title="New Story",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=5,
            user_prompt="Generate story"
        )

        story = Story(
            id="story-new",
            metadata=metadata,
            pages=[]
        )

        assert len(story.pages) == 0

    def test_story_timestamps_default(self):
        """Test that timestamps are auto-generated if not provided"""
        from src.models.story import Story, StoryMetadata

        metadata = StoryMetadata(
            title="Timestamp Test",
            language="English",
            complexity="beginner",
            vocabulary_diversity="low",
            age_group="4-7 years",
            num_pages=1,
            user_prompt="Test"
        )

        story = Story(
            id="story-time",
            metadata=metadata,
            pages=[]
        )

        # Should have auto-generated timestamps
        assert story.created_at is not None
        assert story.updated_at is not None
        assert isinstance(story.created_at, datetime)
        assert isinstance(story.updated_at, datetime)

    def test_story_vocabulary_unique(self):
        """Test that vocabulary list can contain unique words"""
        from src.models.story import Story, StoryMetadata, StoryPage

        metadata = StoryMetadata(
            title="Vocab Story",
            language="Spanish",
            complexity="intermediate",
            vocabulary_diversity="high",
            age_group="8-12 years",
            num_pages=2,
            user_prompt="Vocabulary test"
        )

        pages = [
            StoryPage(page_number=1, text="El gato negro."),
            StoryPage(page_number=2, text="El gato grande."),
        ]

        # Should contain unique words (el, gato, negro, grande)
        story = Story(
            id="story-vocab",
            metadata=metadata,
            pages=pages,
            vocabulary=["el", "gato", "negro", "grande"]
        )

        assert len(story.vocabulary) == 4
        assert "gato" in story.vocabulary
        assert "negro" in story.vocabulary
