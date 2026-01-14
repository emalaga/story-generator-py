"""
Unit tests for ImagePrompt Models.
Write these tests BEFORE implementing the models (TDD approach).
"""

import pytest


class TestImagePrompt:
    """Test ImagePrompt dataclass"""

    def test_image_prompt_creation_minimal(self):
        """Test creating ImagePrompt with minimal required fields"""
        from src.models.image_prompt import ImagePrompt

        prompt = ImagePrompt(
            page_number=1,
            scene_description="A magical forest with tall trees",
            art_style="watercolor children's book illustration"
        )

        assert prompt.page_number == 1
        assert prompt.scene_description == "A magical forest with tall trees"
        assert prompt.art_style == "watercolor children's book illustration"
        assert prompt.characters == []
        assert prompt.lighting is None
        assert prompt.mood is None
        assert prompt.additional_details is None

    def test_image_prompt_creation_full(self):
        """Test creating ImagePrompt with all fields"""
        from src.models.image_prompt import ImagePrompt
        from src.models.character import CharacterProfile

        luna = CharacterProfile(
            name="Luna",
            species="squirrel",
            physical_description="small brown squirrel with bushy tail",
            clothing="tiny green backpack"
        )

        prompt = ImagePrompt(
            page_number=1,
            scene_description="A magical forest clearing with ancient oak trees",
            art_style="watercolor children's book illustration",
            characters=[luna],
            lighting="soft morning sunlight filtering through leaves",
            mood="whimsical and peaceful",
            additional_details="scattered acorns on the ground, small mushrooms"
        )

        assert prompt.page_number == 1
        assert prompt.scene_description == "A magical forest clearing with ancient oak trees"
        assert prompt.art_style == "watercolor children's book illustration"
        assert len(prompt.characters) == 1
        assert prompt.characters[0].name == "Luna"
        assert prompt.lighting == "soft morning sunlight filtering through leaves"
        assert prompt.mood == "whimsical and peaceful"
        assert prompt.additional_details == "scattered acorns on the ground, small mushrooms"

    def test_image_prompt_with_multiple_characters(self):
        """Test ImagePrompt with multiple characters for consistency"""
        from src.models.image_prompt import ImagePrompt
        from src.models.character import CharacterProfile

        luna = CharacterProfile(
            name="Luna",
            species="squirrel",
            physical_description="small brown squirrel with bushy tail",
            clothing="tiny green backpack"
        )

        max = CharacterProfile(
            name="Max",
            species="owl",
            physical_description="wise old owl with gray feathers",
            distinctive_features="wears tiny round spectacles"
        )

        prompt = ImagePrompt(
            page_number=5,
            scene_description="Luna and Max meet under the ancient tree",
            art_style="watercolor children's book illustration",
            characters=[luna, max]
        )

        assert len(prompt.characters) == 2
        assert prompt.characters[0].name == "Luna"
        assert prompt.characters[1].name == "Max"

    def test_image_prompt_without_characters(self):
        """Test ImagePrompt for scene without characters (landscape, etc.)"""
        from src.models.image_prompt import ImagePrompt

        prompt = ImagePrompt(
            page_number=2,
            scene_description="A vast mountain range at sunset",
            art_style="digital painting",
            lighting="golden sunset glow",
            mood="majestic and peaceful"
        )

        assert prompt.characters == []
        assert prompt.scene_description == "A vast mountain range at sunset"

    def test_image_prompt_with_lighting_only(self):
        """Test ImagePrompt with lighting but no mood"""
        from src.models.image_prompt import ImagePrompt

        prompt = ImagePrompt(
            page_number=3,
            scene_description="A dark cave entrance",
            art_style="pencil sketch style",
            lighting="dim torch light casting shadows"
        )

        assert prompt.lighting == "dim torch light casting shadows"
        assert prompt.mood is None

    def test_image_prompt_with_mood_only(self):
        """Test ImagePrompt with mood but no lighting"""
        from src.models.image_prompt import ImagePrompt

        prompt = ImagePrompt(
            page_number=4,
            scene_description="A cozy bedroom at night",
            art_style="soft pastel illustration",
            mood="calm and sleepy"
        )

        assert prompt.mood == "calm and sleepy"
        assert prompt.lighting is None

    def test_image_prompt_to_string_conversion(self):
        """Test that ImagePrompt can be converted to a prompt string"""
        from src.models.image_prompt import ImagePrompt
        from src.models.character import CharacterProfile

        character = CharacterProfile(
            name="Tommy",
            species="turtle",
            physical_description="green turtle with brown shell",
            clothing="red bandana"
        )

        prompt = ImagePrompt(
            page_number=1,
            scene_description="Tommy swimming in a clear pond",
            art_style="watercolor children's book illustration",
            characters=[character],
            lighting="bright sunny day",
            mood="joyful and energetic"
        )

        # Should be able to build a complete prompt string
        prompt_string = f"{prompt.scene_description}, "
        prompt_string += f"art style: {prompt.art_style}"

        if prompt.characters:
            for char in prompt.characters:
                prompt_string += f", {char.species}: {char.physical_description}"
                if char.clothing:
                    prompt_string += f", wearing {char.clothing}"

        if prompt.lighting:
            prompt_string += f", lighting: {prompt.lighting}"

        if prompt.mood:
            prompt_string += f", mood: {prompt.mood}"

        assert "Tommy swimming" in prompt_string
        assert "watercolor" in prompt_string
        assert "green turtle" in prompt_string
        assert "red bandana" in prompt_string
        assert "bright sunny day" in prompt_string

    def test_image_prompt_consistency_across_pages(self):
        """Test that same character appears consistently across multiple prompts"""
        from src.models.image_prompt import ImagePrompt
        from src.models.character import CharacterProfile

        # Define character once
        bella = CharacterProfile(
            name="Bella",
            species="bird",
            physical_description="blue jay with bright blue feathers",
            distinctive_features="white stripe on head"
        )

        # Use in multiple pages
        prompt1 = ImagePrompt(
            page_number=1,
            scene_description="Bella perched on a branch",
            art_style="watercolor children's book illustration",
            characters=[bella]
        )

        prompt2 = ImagePrompt(
            page_number=3,
            scene_description="Bella flying through the sky",
            art_style="watercolor children's book illustration",
            characters=[bella]
        )

        prompt5 = ImagePrompt(
            page_number=5,
            scene_description="Bella singing a song",
            art_style="watercolor children's book illustration",
            characters=[bella]
        )

        # All prompts reference the same character profile
        assert prompt1.characters[0] == bella
        assert prompt2.characters[0] == bella
        assert prompt5.characters[0] == bella
        assert prompt1.characters[0].distinctive_features == "white stripe on head"

    def test_image_prompt_different_art_styles(self):
        """Test ImagePrompt with different art styles"""
        from src.models.image_prompt import ImagePrompt

        watercolor = ImagePrompt(
            page_number=1,
            scene_description="A gentle scene",
            art_style="watercolor children's book illustration"
        )

        digital = ImagePrompt(
            page_number=2,
            scene_description="A vibrant scene",
            art_style="digital cartoon illustration"
        )

        pencil = ImagePrompt(
            page_number=3,
            scene_description="A detailed scene",
            art_style="pencil sketch style"
        )

        assert watercolor.art_style == "watercolor children's book illustration"
        assert digital.art_style == "digital cartoon illustration"
        assert pencil.art_style == "pencil sketch style"

    def test_image_prompt_page_numbering(self):
        """Test ImagePrompt page numbers are correctly assigned"""
        from src.models.image_prompt import ImagePrompt

        prompts = []
        for i in range(1, 11):
            prompt = ImagePrompt(
                page_number=i,
                scene_description=f"Scene {i}",
                art_style="watercolor children's book illustration"
            )
            prompts.append(prompt)

        assert len(prompts) == 10
        assert prompts[0].page_number == 1
        assert prompts[4].page_number == 5
        assert prompts[9].page_number == 10

    def test_image_prompt_with_additional_details(self):
        """Test ImagePrompt with additional environmental details"""
        from src.models.image_prompt import ImagePrompt

        prompt = ImagePrompt(
            page_number=1,
            scene_description="A garden in full bloom",
            art_style="watercolor children's book illustration",
            additional_details="butterflies, roses, tulips, a small fountain in the background"
        )

        assert prompt.additional_details == "butterflies, roses, tulips, a small fountain in the background"

    def test_image_prompt_empty_vs_none_characters(self):
        """Test that empty character list is handled correctly"""
        from src.models.image_prompt import ImagePrompt

        # Explicitly empty list
        prompt1 = ImagePrompt(
            page_number=1,
            scene_description="Empty scene",
            art_style="watercolor children's book illustration",
            characters=[]
        )

        # Default empty list
        prompt2 = ImagePrompt(
            page_number=2,
            scene_description="Another empty scene",
            art_style="watercolor children's book illustration"
        )

        assert prompt1.characters == []
        assert prompt2.characters == []
        assert len(prompt1.characters) == 0
        assert len(prompt2.characters) == 0
