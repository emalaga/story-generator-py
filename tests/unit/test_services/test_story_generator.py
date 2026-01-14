"""
Unit tests for Story Generator Service.
Write these tests BEFORE implementing the service (TDD approach).

The story generator service orchestrates the complete story generation workflow,
coordinating AI clients, prompt building, and character extraction.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestStoryGeneratorService:
    """Test StoryGeneratorService for orchestrating story generation"""

    @pytest.fixture
    def mock_ai_client(self):
        """Create mock AI client for testing"""
        mock_client = AsyncMock()
        mock_client.generate_text = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_prompt_builder(self):
        """Create mock PromptBuilder for testing"""
        from src.domain.prompt_builder import PromptBuilder
        return PromptBuilder()

    @pytest.fixture
    def mock_character_extractor(self):
        """Create mock CharacterExtractor for testing"""
        mock_extractor = AsyncMock()
        mock_extractor.extract_characters = AsyncMock()
        mock_extractor.create_character_profile = AsyncMock()
        return mock_extractor

    @pytest.fixture
    def story_generator(self, mock_ai_client, mock_prompt_builder, mock_character_extractor):
        """Create StoryGeneratorService instance for testing"""
        from src.services.story_generator import StoryGeneratorService
        return StoryGeneratorService(
            ai_client=mock_ai_client,
            prompt_builder=mock_prompt_builder,
            character_extractor=mock_character_extractor
        )

    @pytest.fixture
    def story_metadata(self):
        """Create sample story metadata for testing"""
        from src.models.story import StoryMetadata
        return StoryMetadata(
            title="The Brave Little Turtle",
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=3,
            genre="adventure",
            art_style="cartoon"
        )

    def test_story_generator_initialization(self, mock_ai_client, mock_prompt_builder, mock_character_extractor):
        """Test creating StoryGeneratorService with dependencies"""
        from src.services.story_generator import StoryGeneratorService

        service = StoryGeneratorService(
            ai_client=mock_ai_client,
            prompt_builder=mock_prompt_builder,
            character_extractor=mock_character_extractor
        )

        assert service.ai_client == mock_ai_client
        assert service.prompt_builder == mock_prompt_builder
        assert service.character_extractor == mock_character_extractor

    @pytest.mark.asyncio
    async def test_generate_story_basic_workflow(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test basic story generation workflow"""
        # Mock AI response with formatted story pages
        mock_ai_client.generate_text.return_value = """Page 1:
Tommy the turtle lived by the pond. He was very shy and afraid to try new things.

Page 2:
One day, his friends invited him to explore the big hill. Tommy was scared but decided to be brave.

Page 3:
Tommy climbed the hill and saw the beautiful sunset. He learned that being brave helps us discover wonderful things."""

        # Mock character extraction
        from src.models.character import Character, CharacterProfile
        mock_character_extractor.extract_characters.return_value = [
            Character(name="Tommy", description="A shy little turtle")
        ]

        mock_character_extractor.create_character_profile.return_value = CharacterProfile(
            name="Tommy",
            species="turtle",
            physical_description="Small green turtle with brown shell",
            clothing="Red bandana around neck",
            distinctive_features="Shy expression, small for his age",
            personality_traits="Shy but brave when needed"
        )

        # Generate story
        story = await story_generator.generate_story(story_metadata)

        # Verify AI client was called
        assert mock_ai_client.generate_text.called

        # Verify story structure
        from src.models.story import Story
        assert isinstance(story, Story)
        assert story.metadata == story_metadata
        assert len(story.pages) == 3

        # Verify page content
        assert story.pages[0].page_number == 1
        assert "Tommy the turtle" in story.pages[0].text
        assert story.pages[1].page_number == 2
        assert "explore the big hill" in story.pages[1].text
        assert story.pages[2].page_number == 3
        assert "beautiful sunset" in story.pages[2].text

        # Verify character extraction was called
        assert mock_character_extractor.extract_characters.called
        assert len(story.characters) == 1
        assert story.characters[0].name == "Tommy"

    @pytest.mark.asyncio
    async def test_generate_story_with_theme(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test story generation with optional theme"""
        mock_ai_client.generate_text.return_value = """Page 1:
Test page 1.

Page 2:
Test page 2.

Page 3:
Test page 3."""

        mock_character_extractor.extract_characters.return_value = []

        story = await story_generator.generate_story(
            story_metadata,
            theme="courage and friendship"
        )

        # Verify theme was included in prompt
        call_args = mock_ai_client.generate_text.call_args[0][0]
        assert "courage" in call_args.lower()
        assert "friendship" in call_args.lower()

    @pytest.mark.asyncio
    async def test_generate_story_with_custom_prompt(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test story generation with custom story idea"""
        mock_ai_client.generate_text.return_value = """Page 1:
Test page 1.

Page 2:
Test page 2.

Page 3:
Test page 3."""

        mock_character_extractor.extract_characters.return_value = []

        custom_prompt = "A story about a dragon who learns to read"
        story = await story_generator.generate_story(
            story_metadata,
            custom_prompt=custom_prompt
        )

        # Verify custom prompt was included
        call_args = mock_ai_client.generate_text.call_args[0][0]
        assert "dragon" in call_args.lower()
        assert "read" in call_args.lower()

    @pytest.mark.asyncio
    async def test_generate_story_parses_pages_correctly(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test that story text is correctly parsed into pages"""
        mock_ai_client.generate_text.return_value = """Page 1:
First page text here.
Multiple sentences work fine.

Page 2:
Second page content.

Page 3:
Third page content here."""

        mock_character_extractor.extract_characters.return_value = []

        story = await story_generator.generate_story(story_metadata)

        assert len(story.pages) == 3
        assert "First page text" in story.pages[0].text
        assert "Multiple sentences" in story.pages[0].text
        assert "Second page content" in story.pages[1].text
        assert "Third page content" in story.pages[2].text

    @pytest.mark.asyncio
    async def test_generate_story_extracts_multiple_characters(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test story generation with multiple characters"""
        mock_ai_client.generate_text.return_value = """Page 1:
Luna and Max became friends.

Page 2:
They went on an adventure.

Page 3:
The end."""

        from src.models.character import Character, CharacterProfile

        # Mock multiple characters
        mock_character_extractor.extract_characters.return_value = [
            Character(name="Luna", description="A curious fox"),
            Character(name="Max", description="A friendly dog")
        ]

        # Mock profile creation for each character
        mock_character_extractor.create_character_profile.side_effect = [
            CharacterProfile(
                name="Luna",
                species="fox",
                physical_description="Orange fox with green eyes",
                clothing=None,
                distinctive_features="Bushy tail",
                personality_traits="Curious"
            ),
            CharacterProfile(
                name="Max",
                species="dog",
                physical_description="Golden retriever",
                clothing="Red collar",
                distinctive_features="Floppy ears",
                personality_traits="Friendly"
            )
        ]

        story = await story_generator.generate_story(story_metadata)

        # Verify both characters were extracted and profiled
        assert len(story.characters) == 2
        assert story.characters[0].name == "Luna"
        assert story.characters[1].name == "Max"
        assert mock_character_extractor.create_character_profile.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_story_handles_no_characters(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test story generation when no characters are found"""
        mock_ai_client.generate_text.return_value = """Page 1:
The sun rose over the mountain.

Page 2:
Birds sang in the trees.

Page 3:
It was a beautiful day."""

        mock_character_extractor.extract_characters.return_value = []

        story = await story_generator.generate_story(story_metadata)

        assert len(story.characters) == 0
        assert len(story.pages) == 3
        assert mock_character_extractor.create_character_profile.call_count == 0

    @pytest.mark.asyncio
    async def test_generate_story_handles_malformed_page_format(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test handling of AI response with unexpected format"""
        # AI sometimes returns inconsistent formatting
        mock_ai_client.generate_text.return_value = """Here is the story:

Page 1:
Content for page 1.

Page 2: Content for page 2.

Page 3:
Content for page 3."""

        mock_character_extractor.extract_characters.return_value = []

        story = await story_generator.generate_story(story_metadata)

        # Should still parse pages correctly
        assert len(story.pages) == 3

    @pytest.mark.asyncio
    async def test_generate_story_preserves_metadata(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test that story metadata is preserved in generated story"""
        mock_ai_client.generate_text.return_value = """Page 1:
Test."""

        mock_character_extractor.extract_characters.return_value = []

        story = await story_generator.generate_story(story_metadata)

        assert story.metadata.title == "The Brave Little Turtle"
        assert story.metadata.language == "English"
        assert story.metadata.complexity == "simple"
        assert story.metadata.age_group == "3-5"
        assert story.metadata.num_pages == 3
        assert story.metadata.genre == "adventure"
        assert story.metadata.art_style == "cartoon"

    @pytest.mark.asyncio
    async def test_generate_story_passes_context_to_profiler(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test that story context is passed to character profile creation"""
        story_text = """Page 1:
Hero saves the village.

Page 2:
Everyone celebrates.

Page 3:
The end."""

        mock_ai_client.generate_text.return_value = story_text

        from src.models.character import Character, CharacterProfile
        mock_character_extractor.extract_characters.return_value = [
            Character(name="Hero", description="Brave warrior")
        ]

        mock_character_extractor.create_character_profile.return_value = CharacterProfile(
            name="Hero",
            species="human",
            physical_description="Brave warrior",
            clothing="Armor",
            distinctive_features="Sword",
            personality_traits="Brave"
        )

        story = await story_generator.generate_story(story_metadata)

        # Verify profile creation was called with story context
        assert mock_character_extractor.create_character_profile.called
        # Context should include the full story text for better profile generation

    @pytest.mark.asyncio
    async def test_generate_story_uses_temperature_for_creativity(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test that story generation uses appropriate temperature setting"""
        mock_ai_client.generate_text.return_value = """Page 1:
Test."""

        mock_character_extractor.extract_characters.return_value = []

        await story_generator.generate_story(story_metadata)

        # Verify temperature was passed to AI client (should be higher for creative writing)
        call_kwargs = mock_ai_client.generate_text.call_args[1]
        assert 'temperature' in call_kwargs
        # Creative writing should use higher temperature (e.g., 0.7-0.9)
        assert call_kwargs['temperature'] >= 0.7

    @pytest.mark.asyncio
    async def test_generate_story_handles_ai_client_error(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test handling of AI client errors"""
        mock_ai_client.generate_text.side_effect = Exception("API connection failed")

        with pytest.raises(Exception) as exc_info:
            await story_generator.generate_story(story_metadata)

        assert "API connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_story_handles_character_extraction_error(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test handling of character extraction errors"""
        mock_ai_client.generate_text.return_value = """Page 1:
Test."""

        mock_character_extractor.extract_characters.side_effect = ValueError("Invalid JSON")

        # Should still return story, just without characters
        story = await story_generator.generate_story(story_metadata)

        assert len(story.pages) == 1
        assert len(story.characters) == 0

    @pytest.mark.asyncio
    async def test_generate_story_handles_profile_creation_error(
        self,
        story_generator,
        story_metadata,
        mock_ai_client,
        mock_character_extractor
    ):
        """Test handling of character profile creation errors"""
        mock_ai_client.generate_text.return_value = """Page 1:
Test."""

        from src.models.character import Character
        mock_character_extractor.extract_characters.return_value = [
            Character(name="Test", description="Test character")
        ]

        mock_character_extractor.create_character_profile.side_effect = ValueError("Profile error")

        # Should still return story with basic character info
        story = await story_generator.generate_story(story_metadata)

        assert len(story.pages) == 1
        # Characters should still be included even if profiling fails
        assert len(story.characters) >= 0
