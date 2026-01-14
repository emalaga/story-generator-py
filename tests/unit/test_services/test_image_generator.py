"""
Unit tests for Image Generator Service.
Write these tests BEFORE implementing the service (TDD approach).

The image generator service orchestrates image generation workflow,
coordinating image clients, prompt building, and character consistency.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestImageGeneratorService:
    """Test ImageGeneratorService for orchestrating image generation"""

    @pytest.fixture
    def mock_image_client(self):
        """Create mock image AI client for testing"""
        mock_client = AsyncMock()
        mock_client.generate_image = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_prompt_builder(self):
        """Create mock PromptBuilder for testing"""
        from src.domain.prompt_builder import PromptBuilder
        return PromptBuilder()

    @pytest.fixture
    def image_generator(self, mock_image_client, mock_prompt_builder):
        """Create ImageGeneratorService instance for testing"""
        from src.services.image_generator import ImageGeneratorService
        return ImageGeneratorService(
            image_client=mock_image_client,
            prompt_builder=mock_prompt_builder
        )

    @pytest.fixture
    def character_profiles(self):
        """Create sample character profiles for testing"""
        from src.models.character import CharacterProfile
        return [
            CharacterProfile(
                name="Luna",
                species="fox",
                physical_description="Small orange fox with bright green eyes",
                clothing="Blue scarf",
                distinctive_features="White-tipped tail",
                personality_traits="Curious and friendly"
            )
        ]

    def test_image_generator_initialization(self, mock_image_client, mock_prompt_builder):
        """Test creating ImageGeneratorService with dependencies"""
        from src.services.image_generator import ImageGeneratorService

        service = ImageGeneratorService(
            image_client=mock_image_client,
            prompt_builder=mock_prompt_builder
        )

        assert service.image_client == mock_image_client
        assert service.prompt_builder == mock_prompt_builder

    @pytest.mark.asyncio
    async def test_generate_image_for_page_basic(
        self,
        image_generator,
        character_profiles,
        mock_image_client
    ):
        """Test basic image generation for a story page"""
        scene_description = "Luna exploring a magical forest with glowing mushrooms"
        art_style = "cartoon"

        mock_image_client.generate_image.return_value = "https://example.com/image1.png"

        image_url = await image_generator.generate_image_for_page(
            scene_description,
            character_profiles,
            art_style
        )

        # Verify image client was called
        assert mock_image_client.generate_image.called

        # Verify returned URL
        assert image_url == "https://example.com/image1.png"

    @pytest.mark.asyncio
    async def test_generate_image_uses_prompt_builder(
        self,
        image_generator,
        character_profiles,
        mock_image_client
    ):
        """Test that image generation uses prompt builder"""
        scene = "Test scene"
        art_style = "watercolor"

        mock_image_client.generate_image.return_value = "https://example.com/image.png"

        await image_generator.generate_image_for_page(scene, character_profiles, art_style)

        # Verify prompt was passed to image client
        call_args = mock_image_client.generate_image.call_args[0][0]

        # Prompt should contain scene description
        assert "Test scene" in call_args

        # Prompt should contain character details
        assert "Luna" in call_args
        assert "fox" in call_args.lower()

        # Prompt should contain art style
        assert "watercolor" in call_args.lower()

    @pytest.mark.asyncio
    async def test_generate_image_without_characters(
        self,
        image_generator,
        mock_image_client
    ):
        """Test generating image for scene without characters"""
        scene = "A beautiful sunset over the ocean"
        art_style = "realistic"

        mock_image_client.generate_image.return_value = "https://example.com/image.png"

        image_url = await image_generator.generate_image_for_page(
            scene,
            [],
            art_style
        )

        assert mock_image_client.generate_image.called
        assert image_url == "https://example.com/image.png"

        # Verify prompt was created for scene-only image
        call_args = mock_image_client.generate_image.call_args[0][0]
        assert "sunset" in call_args.lower()
        assert "ocean" in call_args.lower()

    @pytest.mark.asyncio
    async def test_generate_image_with_multiple_characters(
        self,
        image_generator,
        mock_image_client
    ):
        """Test generating image with multiple characters"""
        from src.models.character import CharacterProfile

        profiles = [
            CharacterProfile(
                name="Max",
                species="dog",
                physical_description="Golden retriever with fluffy fur"
            ),
            CharacterProfile(
                name="Bella",
                species="cat",
                physical_description="Small gray tabby cat"
            )
        ]

        scene = "Max and Bella playing in the park"
        art_style = "cartoon"

        mock_image_client.generate_image.return_value = "https://example.com/image.png"

        await image_generator.generate_image_for_page(scene, profiles, art_style)

        # Verify both characters are in prompt
        call_args = mock_image_client.generate_image.call_args[0][0]
        assert "Max" in call_args
        assert "Bella" in call_args
        assert "dog" in call_args.lower()
        assert "cat" in call_args.lower()

    @pytest.mark.asyncio
    async def test_generate_images_for_story(
        self,
        image_generator,
        character_profiles,
        mock_image_client
    ):
        """Test generating images for all pages in a story"""
        from src.models.story import Story, StoryMetadata, StoryPage

        # Create test story
        metadata = StoryMetadata(
            title="Test Story",
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=2,
            art_style="cartoon"
        )

        pages = [
            StoryPage(
                page_number=1,
                text="Luna explored the forest."
            ),
            StoryPage(
                page_number=2,
                text="She found magical mushrooms."
            )
        ]

        story = Story(
            id="test-id",
            metadata=metadata,
            pages=pages,
            characters=character_profiles
        )

        # Mock image generation
        mock_image_client.generate_image.side_effect = [
            "https://example.com/image1.png",
            "https://example.com/image2.png"
        ]

        updated_story = await image_generator.generate_images_for_story(story)

        # Verify image client was called twice
        assert mock_image_client.generate_image.call_count == 2

        # Verify pages were updated with image URLs
        assert updated_story.pages[0].image_url == "https://example.com/image1.png"
        assert updated_story.pages[1].image_url == "https://example.com/image2.png"

        # Verify image prompts were stored
        assert updated_story.pages[0].image_prompt is not None
        assert updated_story.pages[1].image_prompt is not None

    @pytest.mark.asyncio
    async def test_generate_images_uses_page_text_as_scene(
        self,
        image_generator,
        character_profiles,
        mock_image_client
    ):
        """Test that page text is used as scene description"""
        from src.models.story import Story, StoryMetadata, StoryPage

        metadata = StoryMetadata(
            title="Test",
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=1,
            art_style="cartoon"
        )

        pages = [
            StoryPage(
                page_number=1,
                text="The brave knight entered the dark castle."
            )
        ]

        story = Story(
            id="test-id",
            metadata=metadata,
            pages=pages,
            characters=[]
        )

        mock_image_client.generate_image.return_value = "https://example.com/image.png"

        await image_generator.generate_images_for_story(story)

        # Verify page text was used in prompt
        call_args = mock_image_client.generate_image.call_args[0][0]
        assert "knight" in call_args.lower()
        assert "castle" in call_args.lower()

    @pytest.mark.asyncio
    async def test_generate_images_uses_story_art_style(
        self,
        image_generator,
        character_profiles,
        mock_image_client
    ):
        """Test that story's art style is used for all images"""
        from src.models.story import Story, StoryMetadata, StoryPage

        metadata = StoryMetadata(
            title="Test",
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=2,
            art_style="watercolor"
        )

        pages = [
            StoryPage(page_number=1, text="Page 1"),
            StoryPage(page_number=2, text="Page 2")
        ]

        story = Story(
            id="test-id",
            metadata=metadata,
            pages=pages,
            characters=[]
        )

        mock_image_client.generate_image.return_value = "https://example.com/image.png"

        await image_generator.generate_images_for_story(story)

        # Verify all calls used watercolor style
        for call in mock_image_client.generate_image.call_args_list:
            prompt = call[0][0]
            assert "watercolor" in prompt.lower()

    @pytest.mark.asyncio
    async def test_generate_images_handles_client_error(
        self,
        image_generator,
        character_profiles,
        mock_image_client
    ):
        """Test handling of image client errors"""
        mock_image_client.generate_image.side_effect = Exception("API error")

        with pytest.raises(Exception) as exc_info:
            await image_generator.generate_image_for_page(
                "Test scene",
                character_profiles,
                "cartoon"
            )

        assert "API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_images_for_story_preserves_existing_data(
        self,
        image_generator,
        character_profiles,
        mock_image_client
    ):
        """Test that generating images preserves existing story data"""
        from src.models.story import Story, StoryMetadata, StoryPage

        metadata = StoryMetadata(
            title="Original Title",
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=1,
            art_style="cartoon"
        )

        pages = [
            StoryPage(page_number=1, text="Original text")
        ]

        story = Story(
            id="original-id",
            metadata=metadata,
            pages=pages,
            characters=character_profiles
        )

        mock_image_client.generate_image.return_value = "https://example.com/image.png"

        updated_story = await image_generator.generate_images_for_story(story)

        # Verify original data is preserved
        assert updated_story.id == "original-id"
        assert updated_story.metadata.title == "Original Title"
        assert updated_story.pages[0].text == "Original text"
        assert len(updated_story.characters) == 1

    @pytest.mark.asyncio
    async def test_generate_images_stores_prompts_on_pages(
        self,
        image_generator,
        character_profiles,
        mock_image_client
    ):
        """Test that generated prompts are stored on story pages"""
        from src.models.story import Story, StoryMetadata, StoryPage

        metadata = StoryMetadata(
            title="Test",
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=1,
            art_style="cartoon"
        )

        pages = [
            StoryPage(page_number=1, text="Test scene")
        ]

        story = Story(
            id="test-id",
            metadata=metadata,
            pages=pages,
            characters=character_profiles
        )

        mock_image_client.generate_image.return_value = "https://example.com/image.png"

        updated_story = await image_generator.generate_images_for_story(story)

        # Verify image prompt was stored
        assert updated_story.pages[0].image_prompt is not None
        assert len(updated_story.pages[0].image_prompt) > 0

        # Verify prompt contains expected elements
        prompt = updated_story.pages[0].image_prompt
        assert "Test scene" in prompt
        assert "Luna" in prompt
        assert "cartoon" in prompt.lower()

    @pytest.mark.asyncio
    async def test_generate_images_with_partial_failures(
        self,
        image_generator,
        character_profiles,
        mock_image_client
    ):
        """Test handling when some images fail but others succeed"""
        from src.models.story import Story, StoryMetadata, StoryPage

        metadata = StoryMetadata(
            title="Test",
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=3,
            art_style="cartoon"
        )

        pages = [
            StoryPage(page_number=1, text="Page 1"),
            StoryPage(page_number=2, text="Page 2"),
            StoryPage(page_number=3, text="Page 3")
        ]

        story = Story(
            id="test-id",
            metadata=metadata,
            pages=pages,
            characters=[]
        )

        # First succeeds, second fails, third succeeds
        mock_image_client.generate_image.side_effect = [
            "https://example.com/image1.png",
            Exception("API error"),
            "https://example.com/image3.png"
        ]

        updated_story = await image_generator.generate_images_for_story(story)

        # Verify successful images were added
        assert updated_story.pages[0].image_url == "https://example.com/image1.png"
        assert updated_story.pages[2].image_url == "https://example.com/image3.png"

        # Verify failed page has no image URL
        assert updated_story.pages[1].image_url is None

    @pytest.mark.asyncio
    async def test_generate_image_for_page_returns_url(
        self,
        image_generator,
        mock_image_client
    ):
        """Test that generate_image_for_page returns the image URL"""
        mock_image_client.generate_image.return_value = "https://example.com/test.png"

        url = await image_generator.generate_image_for_page(
            "Test scene",
            [],
            "cartoon"
        )

        assert url == "https://example.com/test.png"
        assert isinstance(url, str)
