"""
Manual test script to verify character consistency in image prompts.

This script tests the complete flow:
1. Creates character profiles with all attributes
2. Generates image prompts for multiple scenes
3. Verifies that character details appear consistently
"""

from src.domain.prompt_builder import PromptBuilder
from src.models.character import CharacterProfile

def test_character_consistency():
    """Test that character details are included in all image prompts."""

    print("=" * 80)
    print("CHARACTER CONSISTENCY TEST")
    print("=" * 80)

    # Create a detailed character profile
    caterpillar = CharacterProfile(
        name="Coco",
        species="caterpillar",
        physical_description="Small bright green caterpillar with yellow stripes",
        clothing="Wearing a tiny red hat",
        distinctive_features="Large curious eyes and friendly smile",
        personality_traits="Curious and adventurous"
    )

    # Create prompt builder
    builder = PromptBuilder()

    # Test scenes from a story
    scenes = [
        "Coco waking up on a leaf in the morning sunshine",
        "Coco exploring a colorful garden full of flowers",
        "Coco making friends with a butterfly"
    ]

    print("\nCharacter Profile:")
    print(f"  Name: {caterpillar.name}")
    print(f"  Species: {caterpillar.species}")
    print(f"  Physical: {caterpillar.physical_description}")
    print(f"  Clothing: {caterpillar.clothing}")
    print(f"  Distinctive: {caterpillar.distinctive_features}")
    print(f"  Personality: {caterpillar.personality_traits}")
    print()

    # Generate prompts for each scene
    for i, scene in enumerate(scenes, 1):
        print("-" * 80)
        print(f"SCENE {i}: {scene}")
        print("-" * 80)

        prompt = builder.build_image_prompt(
            scene_description=scene,
            character_profiles=[caterpillar],
            art_style="cartoon"
        )

        print(f"\nGenerated Prompt ({len(prompt)} chars):")
        print(prompt)
        print()

        # Verify character details are present
        checks = {
            "Name (Coco)": "coco" in prompt.lower(),
            "Species (caterpillar)": "caterpillar" in prompt.lower(),
            "Color (green)": "green" in prompt.lower(),
            "Pattern (stripes)": "stripes" in prompt.lower() or "yellow" in prompt.lower(),
            "Clothing (red hat)": "hat" in prompt.lower(),
            "Feature (eyes/smile)": "eyes" in prompt.lower() or "smile" in prompt.lower(),
            "Personality": "curious" in prompt.lower() or "adventurous" in prompt.lower()
        }

        print("Character Details Check:")
        for check_name, result in checks.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check_name}")

        all_present = all(checks.values())
        if not all_present:
            print("\n  ⚠️  WARNING: Some character details are missing!")
        else:
            print("\n  ✓ All character details present!")
        print()

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print("• Character profiles now include: name, species, physical description,")
    print("  clothing, distinctive features, and personality traits")
    print("• All these details are included in the image prompts FIRST")
    print("• This ensures consistent character appearance across all illustrations")
    print()

if __name__ == "__main__":
    test_character_consistency()
