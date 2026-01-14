"""
Unit tests for Prompt Builder.
Write these tests BEFORE implementing the builder (TDD approach).

The prompt builder creates prompts for AI text and image generation,
using story parameters and character profiles.
"""

import pytest


class TestPromptBuilder:
    """Test PromptBuilder for creating AI prompts"""

    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance for testing"""
        from src.domain.prompt_builder import PromptBuilder
        return PromptBuilder()

    @pytest.fixture
    def story_metadata(self):
        """Create sample story metadata for testing"""
        from src.models.story import StoryMetadata
        return StoryMetadata(
            title="Test Story",
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=3,
            genre="adventure",
            art_style="cartoon"
        )

    def test_prompt_builder_initialization(self):
        """Test creating PromptBuilder"""
        from src.domain.prompt_builder import PromptBuilder

        builder = PromptBuilder()
        assert builder is not None

    def test_build_story_prompt_basic(self, prompt_builder, story_metadata):
        """Test building basic story generation prompt"""
        prompt = prompt_builder.build_story_prompt(story_metadata)

        # Verify prompt contains key metadata
        assert "English" in prompt
        assert "simple" in prompt
        assert "3-5" in prompt or "3" in prompt
        assert "3" in prompt  # num_pages
        assert "adventure" in prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_build_story_prompt_with_theme(self, prompt_builder, story_metadata):
        """Test building story prompt with optional theme"""
        prompt = prompt_builder.build_story_prompt(
            story_metadata,
            theme="friendship and bravery"
        )

        assert "friendship" in prompt.lower()
        assert "bravery" in prompt.lower()

    def test_build_story_prompt_with_custom_prompt(self, prompt_builder, story_metadata):
        """Test building story prompt with user's custom prompt"""
        custom_prompt = "A story about a dragon who learns to read"

        prompt = prompt_builder.build_story_prompt(
            story_metadata,
            custom_prompt=custom_prompt
        )

        assert "dragon" in prompt.lower()
        assert "read" in prompt.lower()

    def test_build_story_prompt_different_age_groups(self, prompt_builder):
        """Test that prompts adapt to different age groups"""
        from src.models.story import StoryMetadata

        metadata_young = StoryMetadata(
            title="Young Story",
            language="English",
            complexity="very simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=3
        )

        metadata_older = StoryMetadata(
            title="Older Story",
            language="English",
            complexity="complex",
            vocabulary_diversity="advanced",
            age_group="8-10",
            num_pages=8
        )

        prompt_young = prompt_builder.build_story_prompt(metadata_young)
        prompt_older = prompt_builder.build_story_prompt(metadata_older)

        # Prompts should be different
        assert prompt_young != prompt_older
        assert "3-5" in prompt_young or "young" in prompt_young.lower()
        assert "8-10" in prompt_older or "older" in prompt_older.lower()

    def test_build_image_prompt_with_character_profile(self, prompt_builder):
        """Test building image prompt with character profile"""
        from src.models.character import CharacterProfile

        profile = CharacterProfile(
            name="Luna",
            species="fox",
            physical_description="Small orange fox with bright green eyes and bushy tail",
            clothing="Wearing a blue scarf",
            distinctive_features="White-tipped tail, one ear slightly bent",
            personality_traits="Curious and friendly"
        )

        scene_description = "Luna exploring a magical forest with glowing mushrooms"

        prompt = prompt_builder.build_image_prompt(
            scene_description,
            [profile],
            art_style="cartoon"
        )

        # Verify character details are included
        assert "Luna" in prompt
        assert "fox" in prompt.lower()
        assert "orange" in prompt.lower()
        assert "green eyes" in prompt.lower()
        assert "blue scarf" in prompt.lower()

        # Verify scene is included
        assert "magical forest" in prompt.lower()
        assert "mushrooms" in prompt.lower()

        # Verify art style is included
        assert "cartoon" in prompt.lower()

    def test_build_image_prompt_multiple_characters(self, prompt_builder):
        """Test building image prompt with multiple characters"""
        from src.models.character import CharacterProfile

        profiles = [
            CharacterProfile(
                name="Max",
                species="dog",
                physical_description="Golden retriever with fluffy fur",
                clothing="Red collar"
            ),
            CharacterProfile(
                name="Bella",
                species="cat",
                physical_description="Small gray tabby cat",
                clothing="Pink bow"
            )
        ]

        scene = "Max and Bella playing in the park"

        prompt = prompt_builder.build_image_prompt(scene, profiles, "realistic")

        assert "Max" in prompt
        assert "Bella" in prompt
        assert "dog" in prompt.lower()
        assert "cat" in prompt.lower()
        assert "golden retriever" in prompt.lower()
        assert "gray tabby" in prompt.lower()
        assert "park" in prompt.lower()

    def test_build_image_prompt_without_characters(self, prompt_builder):
        """Test building image prompt for scene without characters"""
        scene = "A beautiful sunset over the ocean with seagulls flying"

        prompt = prompt_builder.build_image_prompt(
            scene,
            [],
            art_style="watercolor"
        )

        assert "sunset" in prompt.lower()
        assert "ocean" in prompt.lower()
        assert "seagulls" in prompt.lower()
        assert "watercolor" in prompt.lower()
        assert isinstance(prompt, str)

    def test_build_image_prompt_includes_style_keywords(self, prompt_builder):
        """Test that image prompts include proper style keywords"""
        from src.models.character import CharacterProfile

        profile = CharacterProfile(
            name="Test",
            species="human",
            physical_description="Test character"
        )

        scene = "Test scene"

        # Test different art styles
        styles = ["cartoon", "realistic", "watercolor", "digital art"]

        for style in styles:
            prompt = prompt_builder.build_image_prompt(scene, [profile], style)
            assert style.lower() in prompt.lower()

    def test_build_story_prompt_includes_formatting_instructions(self, prompt_builder, story_metadata):
        """Test that story prompts include formatting instructions"""
        prompt = prompt_builder.build_story_prompt(story_metadata)

        # Should mention page structure
        assert "page" in prompt.lower()

    def test_build_image_prompt_for_children_appropriate(self, prompt_builder):
        """Test that image prompts emphasize child-appropriate content"""
        from src.models.character import CharacterProfile

        profile = CharacterProfile(
            name="Hero",
            species="human",
            physical_description="Brave young adventurer"
        )

        scene = "Hero facing a challenge"

        prompt = prompt_builder.build_image_prompt(scene, [profile], "cartoon")

        # Should mention child-friendly or similar
        assert "child" in prompt.lower() or "friendly" in prompt.lower() or "appropriate" in prompt.lower()

    def test_build_story_prompt_with_all_optional_parameters(self, prompt_builder, story_metadata):
        """Test building story prompt with all optional parameters"""
        prompt = prompt_builder.build_story_prompt(
            story_metadata,
            theme="courage and friendship",
            custom_prompt="A story about a shy turtle who becomes a hero"
        )

        assert "courage" in prompt.lower()
        assert "friendship" in prompt.lower()
        assert "turtle" in prompt.lower()
        assert "hero" in prompt.lower()
        assert len(prompt) > 0

    def test_build_image_prompt_maintains_character_consistency(self, prompt_builder):
        """Test that image prompts emphasize character consistency"""
        from src.models.character import CharacterProfile

        profile = CharacterProfile(
            name="Spark",
            species="dragon",
            physical_description="Small purple dragon with silver wings",
            distinctive_features="Star-shaped mark on forehead"
        )

        scene = "Spark flying through clouds"

        prompt = prompt_builder.build_image_prompt(scene, [profile], "digital art")

        # Should include distinctive features for consistency
        assert "star" in prompt.lower() or "mark" in prompt.lower()
        assert "purple" in prompt.lower()
        assert "silver" in prompt.lower()

    def test_build_story_prompt_different_languages(self, prompt_builder):
        """Test building prompts for different languages"""
        from src.models.story import StoryMetadata

        metadata_spanish = StoryMetadata(
            title="Spanish Story",
            language="Spanish",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=3
        )

        prompt = prompt_builder.build_story_prompt(metadata_spanish)

        assert "Spanish" in prompt

    def test_build_image_prompt_includes_character_personality(self, prompt_builder):
        """Test that character personality traits are reflected in image prompts"""
        from src.models.character import CharacterProfile

        profile = CharacterProfile(
            name="Joy",
            species="rabbit",
            physical_description="Small white rabbit",
            personality_traits="Happy, energetic, always smiling"
        )

        scene = "Joy hopping through a meadow"

        prompt = prompt_builder.build_image_prompt(scene, [profile], "cartoon")

        # Personality should influence the prompt
        assert "happy" in prompt.lower() or "smiling" in prompt.lower() or "joyful" in prompt.lower()
