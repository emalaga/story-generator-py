"""
Unit tests for Character Models.
Write these tests BEFORE implementing the models (TDD approach).
"""

import pytest


class TestCharacter:
    """Test Character dataclass"""

    def test_character_creation_minimal(self):
        """Test creating Character with minimal fields"""
        from src.models.character import Character

        character = Character(
            name="Luna",
            description="A brave squirrel"
        )

        assert character.name == "Luna"
        assert character.description == "A brave squirrel"
        assert character.role is None

    def test_character_creation_with_role(self):
        """Test creating Character with role"""
        from src.models.character import Character

        character = Character(
            name="Max",
            description="A wise old owl",
            role="mentor"
        )

        assert character.name == "Max"
        assert character.description == "A wise old owl"
        assert character.role == "mentor"

    def test_character_multiple_roles(self):
        """Test Character with different role types"""
        from src.models.character import Character

        protagonist = Character(
            name="Hero",
            description="The main character",
            role="protagonist"
        )

        antagonist = Character(
            name="Villain",
            description="The bad guy",
            role="antagonist"
        )

        supporting = Character(
            name="Friend",
            description="A helpful friend",
            role="supporting"
        )

        assert protagonist.role == "protagonist"
        assert antagonist.role == "antagonist"
        assert supporting.role == "supporting"


class TestCharacterProfile:
    """Test CharacterProfile dataclass"""

    def test_character_profile_minimal(self):
        """Test creating CharacterProfile with minimal fields"""
        from src.models.character import CharacterProfile

        profile = CharacterProfile(
            name="Luna",
            species="squirrel",
            physical_description="small, brown fur, bright eyes"
        )

        assert profile.name == "Luna"
        assert profile.species == "squirrel"
        assert profile.physical_description == "small, brown fur, bright eyes"
        assert profile.clothing is None
        assert profile.distinctive_features is None
        assert profile.personality_traits is None

    def test_character_profile_full(self):
        """Test creating CharacterProfile with all fields"""
        from src.models.character import CharacterProfile

        profile = CharacterProfile(
            name="Captain Whiskers",
            species="cat",
            physical_description="large orange tabby with green eyes",
            clothing="blue sailor hat and red scarf",
            distinctive_features="has a small scar above left eye",
            personality_traits="brave, curious, kind-hearted"
        )

        assert profile.name == "Captain Whiskers"
        assert profile.species == "cat"
        assert profile.physical_description == "large orange tabby with green eyes"
        assert profile.clothing == "blue sailor hat and red scarf"
        assert profile.distinctive_features == "has a small scar above left eye"
        assert profile.personality_traits == "brave, curious, kind-hearted"

    def test_character_profile_with_clothing_only(self):
        """Test CharacterProfile with clothing but no distinctive features"""
        from src.models.character import CharacterProfile

        profile = CharacterProfile(
            name="Princess Pearl",
            species="rabbit",
            physical_description="white rabbit with pink nose",
            clothing="sparkly pink dress with crown"
        )

        assert profile.clothing == "sparkly pink dress with crown"
        assert profile.distinctive_features is None
        assert profile.personality_traits is None

    def test_character_profile_with_features_only(self):
        """Test CharacterProfile with distinctive features but no clothing"""
        from src.models.character import CharacterProfile

        profile = CharacterProfile(
            name="Spike",
            species="hedgehog",
            physical_description="small hedgehog with brown spikes",
            distinctive_features="extra long spikes on back"
        )

        assert profile.distinctive_features == "extra long spikes on back"
        assert profile.clothing is None

    def test_character_profile_consistency_key(self):
        """Test that CharacterProfile can be used for consistency checks"""
        from src.models.character import CharacterProfile

        # This profile should be consistent across all images
        profile = CharacterProfile(
            name="Tommy",
            species="turtle",
            physical_description="green turtle with brown shell",
            clothing="red bandana",
            distinctive_features="crack in shell"
        )

        # All key attributes present for image prompt generation
        assert profile.name is not None
        assert profile.species is not None
        assert profile.physical_description is not None
        assert len(profile.physical_description) > 0

    def test_character_profile_multiple_characters(self):
        """Test creating multiple distinct CharacterProfiles"""
        from src.models.character import CharacterProfile

        char1 = CharacterProfile(
            name="Bella",
            species="bird",
            physical_description="blue jay with bright blue feathers"
        )

        char2 = CharacterProfile(
            name="Oscar",
            species="bear",
            physical_description="large brown bear with friendly face"
        )

        char3 = CharacterProfile(
            name="Daisy",
            species="deer",
            physical_description="young deer with white spots"
        )

        # All characters are distinct
        assert char1.name != char2.name != char3.name
        assert char1.species != char2.species != char3.species

    def test_character_profile_for_image_prompt(self):
        """Test CharacterProfile contains all info needed for image prompts"""
        from src.models.character import CharacterProfile

        profile = CharacterProfile(
            name="Rex",
            species="dog",
            physical_description="golden retriever with fluffy fur",
            clothing="blue collar with silver tag",
            distinctive_features="one ear is slightly floppy",
            personality_traits="playful and energetic"
        )

        # Should be able to build a consistent image prompt from this
        image_description = f"{profile.species}: {profile.physical_description}"
        if profile.clothing:
            image_description += f", wearing {profile.clothing}"
        if profile.distinctive_features:
            image_description += f", {profile.distinctive_features}"

        assert "golden retriever" in image_description
        assert "blue collar" in image_description
        assert "floppy" in image_description


class TestCharacterIntegration:
    """Test Character and CharacterProfile working together"""

    def test_character_with_profile_reference(self):
        """Test that Character and CharacterProfile represent the same entity"""
        from src.models.character import Character, CharacterProfile

        # Simple Character reference in story
        character = Character(
            name="Luna",
            description="A brave squirrel who loves adventures",
            role="protagonist"
        )

        # Detailed CharacterProfile for image generation
        profile = CharacterProfile(
            name="Luna",  # Same name as Character
            species="squirrel",
            physical_description="small brown squirrel with bushy tail and bright eyes",
            clothing="tiny green backpack",
            distinctive_features="white patch on chest",
            personality_traits="brave, curious, adventurous"
        )

        # Names should match
        assert character.name == profile.name

    def test_multiple_characters_with_profiles(self):
        """Test story with multiple characters and their profiles"""
        from src.models.character import Character, CharacterProfile

        # Story characters
        hero = Character(
            name="Finn",
            description="A curious fox",
            role="protagonist"
        )

        mentor = Character(
            name="Old Oak",
            description="A wise tree",
            role="mentor"
        )

        # Corresponding profiles for image generation
        finn_profile = CharacterProfile(
            name="Finn",
            species="fox",
            physical_description="young red fox with white-tipped tail",
            clothing="explorer's vest"
        )

        oak_profile = CharacterProfile(
            name="Old Oak",
            species="tree",
            physical_description="ancient oak tree with kind face in bark",
            distinctive_features="leaves that glow golden"
        )

        # Names match
        assert hero.name == finn_profile.name
        assert mentor.name == oak_profile.name

        # Roles are different
        assert hero.role == "protagonist"
        assert mentor.role == "mentor"
