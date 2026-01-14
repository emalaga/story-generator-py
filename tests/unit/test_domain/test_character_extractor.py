"""
Unit tests for Character Extractor.
Write these tests BEFORE implementing the extractor (TDD approach).

The character extractor uses AI to extract character information from story text
and create consistent character profiles for image generation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestCharacterExtractor:
    """Test CharacterExtractor for extracting characters from stories"""

    @pytest.fixture
    def mock_ai_client(self):
        """Create mock AI client for testing"""
        mock_client = AsyncMock()
        mock_client.generate_text = AsyncMock()
        return mock_client

    @pytest.fixture
    def character_extractor(self, mock_ai_client):
        """Create CharacterExtractor instance for testing"""
        from src.domain.character_extractor import CharacterExtractor
        return CharacterExtractor(mock_ai_client)

    def test_character_extractor_initialization(self, mock_ai_client):
        """Test creating CharacterExtractor with AI client"""
        from src.domain.character_extractor import CharacterExtractor

        extractor = CharacterExtractor(mock_ai_client)

        assert extractor.ai_client == mock_ai_client

    @pytest.mark.asyncio
    async def test_extract_characters_from_single_page_story(self, character_extractor, mock_ai_client):
        """Test extracting characters from a simple story"""
        from src.models.story import StoryPage

        # Mock AI response with character information
        mock_ai_client.generate_text.return_value = """
        {
            "characters": [
                {
                    "name": "Luna",
                    "description": "A curious young fox with bright orange fur and sparkling green eyes"
                },
                {
                    "name": "Oliver",
                    "description": "A wise old owl with gray feathers and golden eyes"
                }
            ]
        }
        """

        story_pages = [
            StoryPage(
                page_number=1,
                text="Luna the fox met Oliver the owl in the enchanted forest."
            )
        ]

        characters = await character_extractor.extract_characters(story_pages)

        # Verify AI was called
        assert mock_ai_client.generate_text.called

        # Verify we got 2 characters
        assert len(characters) == 2

        # Verify character details
        assert characters[0].name == "Luna"
        assert "fox" in characters[0].description.lower()
        assert characters[1].name == "Oliver"
        assert "owl" in characters[1].description.lower()

    @pytest.mark.asyncio
    async def test_extract_characters_from_multi_page_story(self, character_extractor, mock_ai_client):
        """Test extracting characters from multiple pages"""
        from src.models.story import StoryPage

        mock_ai_client.generate_text.return_value = """
        {
            "characters": [
                {
                    "name": "Mia",
                    "description": "A brave young girl with brown hair and blue eyes, wearing a red cape"
                },
                {
                    "name": "Dragon",
                    "description": "A friendly green dragon with purple scales on its wings"
                }
            ]
        }
        """

        story_pages = [
            StoryPage(page_number=1, text="Mia lived in a small village."),
            StoryPage(page_number=2, text="One day, she met a friendly dragon."),
            StoryPage(page_number=3, text="They became best friends.")
        ]

        characters = await character_extractor.extract_characters(story_pages)

        # Verify all pages were included in the prompt
        call_args = mock_ai_client.generate_text.call_args[0][0]
        assert "Mia lived in a small village" in call_args
        assert "she met a friendly dragon" in call_args
        assert "They became best friends" in call_args

        assert len(characters) == 2
        assert characters[0].name == "Mia"
        assert characters[1].name == "Dragon"

    @pytest.mark.asyncio
    async def test_extract_characters_returns_character_objects(self, character_extractor, mock_ai_client):
        """Test that extracted characters are Character objects"""
        from src.models.character import Character
        from src.models.story import StoryPage

        mock_ai_client.generate_text.return_value = """
        {
            "characters": [
                {
                    "name": "Bella",
                    "description": "A small brown bunny with long ears"
                }
            ]
        }
        """

        story_pages = [StoryPage(page_number=1, text="Bella the bunny hopped.")]
        characters = await character_extractor.extract_characters(story_pages)

        assert len(characters) == 1
        assert isinstance(characters[0], Character)
        assert characters[0].name == "Bella"
        assert characters[0].description == "A small brown bunny with long ears"

    @pytest.mark.asyncio
    async def test_extract_characters_empty_story(self, character_extractor, mock_ai_client):
        """Test handling of empty story"""
        with pytest.raises(ValueError) as exc_info:
            await character_extractor.extract_characters([])

        assert "story" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_extract_characters_handles_malformed_json(self, character_extractor, mock_ai_client):
        """Test handling of malformed JSON response from AI"""
        from src.models.story import StoryPage

        mock_ai_client.generate_text.return_value = "This is not valid JSON"

        story_pages = [StoryPage(page_number=1, text="Test story")]

        with pytest.raises(ValueError) as exc_info:
            await character_extractor.extract_characters(story_pages)

        assert "json" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_extract_characters_handles_missing_characters_field(self, character_extractor, mock_ai_client):
        """Test handling when JSON doesn't contain 'characters' field"""
        from src.models.story import StoryPage

        mock_ai_client.generate_text.return_value = '{"other_field": "value"}'

        story_pages = [StoryPage(page_number=1, text="Test story")]

        with pytest.raises(ValueError) as exc_info:
            await character_extractor.extract_characters(story_pages)

        assert "characters" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_character_profile_single_character(self, character_extractor, mock_ai_client):
        """Test creating detailed character profile"""
        from src.models.character import Character

        character = Character(
            name="Max",
            description="A playful golden retriever puppy"
        )

        mock_ai_client.generate_text.return_value = """
        {
            "species": "dog",
            "physical_description": "Golden retriever puppy with fluffy golden fur, floppy ears, and big brown eyes",
            "clothing": "Wearing a red collar with a bone-shaped tag",
            "distinctive_features": "Has a white patch on chest, always wagging tail",
            "personality_traits": "Playful, energetic, friendly, curious"
        }
        """

        profile = await character_extractor.create_character_profile(character)

        # Verify AI was called with character info
        call_args = mock_ai_client.generate_text.call_args[0][0]
        assert "Max" in call_args
        assert "golden retriever" in call_args.lower()

        # Verify profile object
        from src.models.character import CharacterProfile
        assert isinstance(profile, CharacterProfile)
        assert profile.name == "Max"
        assert profile.species == "dog"
        assert "golden fur" in profile.physical_description.lower()
        assert "red collar" in profile.clothing.lower()
        assert "white patch" in profile.distinctive_features.lower()

    @pytest.mark.asyncio
    async def test_create_character_profile_with_context(self, character_extractor, mock_ai_client):
        """Test creating profile with story context"""
        from src.models.character import Character

        character = Character(
            name="Princess Lily",
            description="A kind princess with long blonde hair"
        )

        story_context = "A fairy tale about a princess who helps animals in the forest."

        mock_ai_client.generate_text.return_value = """
        {
            "species": "human",
            "physical_description": "Young woman with long flowing blonde hair, kind blue eyes, fair skin",
            "clothing": "Elegant blue gown with silver embroidery, small silver tiara",
            "distinctive_features": "Gentle smile, flower crown made of lilies",
            "personality_traits": "Kind, compassionate, loves animals, helpful"
        }
        """

        profile = await character_extractor.create_character_profile(character, story_context)

        # Verify context was included
        call_args = mock_ai_client.generate_text.call_args[0][0]
        assert "fairy tale" in call_args.lower()
        assert "helps animals" in call_args.lower()

        assert profile.name == "Princess Lily"
        assert profile.species == "human"
        assert "blonde hair" in profile.physical_description.lower()

    @pytest.mark.asyncio
    async def test_create_character_profile_handles_malformed_json(self, character_extractor, mock_ai_client):
        """Test handling malformed JSON in profile creation"""
        from src.models.character import Character

        character = Character(name="Test", description="Test character")
        mock_ai_client.generate_text.return_value = "Invalid JSON"

        with pytest.raises(ValueError) as exc_info:
            await character_extractor.create_character_profile(character)

        assert "json" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_extract_characters_preserves_order(self, character_extractor, mock_ai_client):
        """Test that character order is preserved"""
        from src.models.story import StoryPage

        mock_ai_client.generate_text.return_value = """
        {
            "characters": [
                {"name": "Alice", "description": "First character"},
                {"name": "Bob", "description": "Second character"},
                {"name": "Charlie", "description": "Third character"}
            ]
        }
        """

        story_pages = [StoryPage(page_number=1, text="Test")]
        characters = await character_extractor.extract_characters(story_pages)

        assert characters[0].name == "Alice"
        assert characters[1].name == "Bob"
        assert characters[2].name == "Charlie"

    @pytest.mark.asyncio
    async def test_extract_characters_with_special_characters_in_names(self, character_extractor, mock_ai_client):
        """Test handling special characters in character names"""
        from src.models.story import StoryPage

        mock_ai_client.generate_text.return_value = """
        {
            "characters": [
                {"name": "José", "description": "A brave knight"},
                {"name": "Zoë", "description": "A clever wizard"},
                {"name": "Mr. O'Brien", "description": "A wise teacher"}
            ]
        }
        """

        story_pages = [StoryPage(page_number=1, text="Test")]
        characters = await character_extractor.extract_characters(story_pages)

        assert len(characters) == 3
        assert characters[0].name == "José"
        assert characters[1].name == "Zoë"
        assert characters[2].name == "Mr. O'Brien"

    @pytest.mark.asyncio
    async def test_extract_characters_uses_system_message(self, character_extractor, mock_ai_client):
        """Test that extraction uses appropriate system message for AI"""
        from src.models.story import StoryPage

        mock_ai_client.generate_text.return_value = """
        {
            "characters": [{"name": "Test", "description": "Test char"}]
        }
        """

        story_pages = [StoryPage(page_number=1, text="Test")]
        await character_extractor.extract_characters(story_pages)

        # Verify system_message was passed to AI client
        call_kwargs = mock_ai_client.generate_text.call_args[1]
        assert 'system_message' in call_kwargs
        assert "character" in call_kwargs['system_message'].lower()

    @pytest.mark.asyncio
    async def test_create_character_profile_uses_system_message(self, character_extractor, mock_ai_client):
        """Test that profile creation uses appropriate system message"""
        from src.models.character import Character

        character = Character(name="Test", description="Test")
        mock_ai_client.generate_text.return_value = """
        {
            "species": "Test",
            "physical_description": "Test",
            "clothing": "Test",
            "distinctive_features": "Test",
            "personality_traits": "Test"
        }
        """

        await character_extractor.create_character_profile(character)

        # Verify system_message was passed
        call_kwargs = mock_ai_client.generate_text.call_args[1]
        assert 'system_message' in call_kwargs
        assert "profile" in call_kwargs['system_message'].lower()
