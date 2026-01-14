"""
Character Extractor for extracting characters from story text.

This module uses AI to analyze story text and extract character information,
creating consistent character profiles for image generation.
"""

import json
from typing import List, Optional

from src.ai.base_client import BaseAIClient
from src.models.character import Character, CharacterProfile
from src.models.story import StoryPage


class CharacterExtractor:
    """
    Extracts character information from story text using AI.

    This class analyzes story pages to identify characters and their
    descriptions, then creates detailed character profiles for
    consistent image generation across all story pages.
    """

    def __init__(self, ai_client: BaseAIClient):
        """
        Initialize the character extractor.

        Args:
            ai_client: AI client for text generation (Ollama, OpenAI, etc.)
        """
        self.ai_client = ai_client

    async def extract_characters(self, story_pages: List[StoryPage]) -> List[Character]:
        """
        Extract characters from story pages.

        Analyzes the complete story text to identify all characters
        and their basic descriptions.

        Args:
            story_pages: List of story pages with text content

        Returns:
            List of Character objects with names and descriptions

        Raises:
            ValueError: If story is empty or AI response is invalid
        """
        if not story_pages:
            raise ValueError("Cannot extract characters from empty story")

        # Combine all story text
        full_story = "\n\n".join([
            f"Page {page.page_number}: {page.text}"
            for page in story_pages
        ])

        # Create prompt for character extraction
        system_message = """You are a character extraction specialist for children's stories.
Your task is to identify all characters in the story and provide a brief description of each.
Return your response as valid JSON in this exact format:
{
    "characters": [
        {
            "name": "Character Name",
            "description": "Brief physical description"
        }
    ]
}

Guidelines:
- Include ALL characters mentioned in the story
- Keep descriptions concise but visually descriptive
- Focus on physical appearance (species, color, size, distinctive features)
- Maintain the order characters appear in the story
- Use the exact names from the story"""

        prompt = f"""Extract all characters from this story:

{full_story}

Return ONLY the JSON response with no additional text."""

        # Get AI response
        response = await self.ai_client.generate_text(
            prompt,
            system_message=system_message,
            temperature=0.3  # Lower temperature for more consistent extraction
        )

        # Debug logging
        print(f"[CHARACTER EXTRACTION] AI Response length: {len(response)} chars")
        print(f"[CHARACTER EXTRACTION] AI Response preview: {response[:500]}")

        # Parse JSON response
        try:
            # Clean response (remove markdown code blocks if present)
            clean_response = response.strip()
            if clean_response.startswith("```"):
                # Extract JSON from code block
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1]) if len(lines) > 2 else clean_response

            data = json.loads(clean_response)
            print(f"[CHARACTER EXTRACTION] Parsed JSON successfully: {len(data.get('characters', []))} characters found")
        except json.JSONDecodeError as e:
            print(f"[CHARACTER EXTRACTION] JSON Parse Error: {e}")
            print(f"[CHARACTER EXTRACTION] Failed response: {clean_response[:1000]}")
            raise ValueError(f"Failed to parse JSON response from AI: {e}")

        # Validate response structure
        if "characters" not in data:
            print(f"[CHARACTER EXTRACTION] ERROR: Missing 'characters' field in response")
            raise ValueError("AI response missing 'characters' field")

        # Create Character objects
        characters = []
        for char_data in data["characters"]:
            character = Character(
                name=char_data["name"],
                description=char_data["description"]
            )
            characters.append(character)
            print(f"[CHARACTER EXTRACTION] Extracted character: {character.name}")

        print(f"[CHARACTER EXTRACTION] Total characters extracted: {len(characters)}")
        return characters

    async def create_character_profile(
        self,
        character: Character,
        story_context: Optional[str] = None
    ) -> CharacterProfile:
        """
        Create a detailed character profile for image generation.

        Takes a basic character and creates a comprehensive profile
        with detailed physical descriptions, clothing, and features
        for consistent image generation.

        Args:
            character: Basic character with name and description
            story_context: Optional story context for better profile generation

        Returns:
            CharacterProfile with detailed visual information

        Raises:
            ValueError: If AI response is invalid
        """
        system_message = """You are a character profile specialist for children's book illustrations.
Your task is to create detailed visual descriptions for consistent character illustration.
Return your response as valid JSON in this exact format:
{
    "species": "Species or type of character (e.g., dog, human, dragon, etc.)",
    "physical_description": "Detailed physical description with colors, sizes, and proportions",
    "clothing": "What the character wears (if applicable, or null)",
    "distinctive_features": "Unique features for recognition (or null)",
    "personality_traits": "Key personality traits visible in appearance (or null)"
}

Guidelines:
- Be highly specific about colors, sizes, and proportions
- Include details that would help an artist draw the character consistently
- Focus on visual elements that can be illustrated
- Keep descriptions child-appropriate
- Ensure all features are consistent with the character type"""

        prompt = f"""Create a detailed character profile for illustration:

Character Name: {character.name}
Basic Description: {character.description}
"""

        if story_context:
            prompt += f"\nStory Context: {story_context}\n"

        prompt += "\nReturn ONLY the JSON response with no additional text."

        # Get AI response
        response = await self.ai_client.generate_text(
            prompt,
            system_message=system_message,
            temperature=0.3  # Lower temperature for consistency
        )

        # Debug logging
        print(f"[CHARACTER PROFILE] AI Response for {character.name}:")
        print(f"[CHARACTER PROFILE] Length: {len(response)} chars")
        print(f"[CHARACTER PROFILE] Response: {response[:500]}")

        # Parse JSON response
        try:
            # Clean response (remove markdown code blocks if present)
            clean_response = response.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                clean_response = "\n".join(lines[1:-1]) if len(lines) > 2 else clean_response

            data = json.loads(clean_response)
            print(f"[CHARACTER PROFILE] Parsed JSON successfully")
        except json.JSONDecodeError as e:
            print(f"[CHARACTER PROFILE] JSON Parse Error: {e}")
            print(f"[CHARACTER PROFILE] Failed response: {clean_response[:1000]}")
            raise ValueError(f"Failed to parse JSON response from AI: {e}")

        # Extract species from the data or fallback to description
        species = data.get("species")
        if not species:
            # Try to extract species from the character description
            # Look for common patterns like "a cat", "an elephant", etc.
            import re
            desc_lower = character.description.lower()
            # Common species patterns (English and Spanish)
            species_match = re.search(r'\b(cat|dog|bird|fox|rabbit|mouse|elephant|lion|tiger|bear|wolf|deer|dragon|unicorn|horse|fish|butterfly|bee|ant|spider|snake|frog|turtle|owl|eagle|penguin|dolphin|whale|shark|octopus|crab|snail|worm|caterpillar|oruga|ladybug|dragonfly|grasshopper|cricket|firefly|gato|perro|pájaro|zorro|conejo|ratón|elefante|león|tigre|oso|lobo|ciervo|dragón|unicornio|caballo|pez|mariposa|abeja|hormiga|araña|serpiente|rana|tortuga|búho|águila|pingüino|delfín|ballena|tiburón|pulpo|cangrejo|caracol|gusano|mariquita|libélula|saltamontes|grillo|luciérnaga)\b', desc_lower)
            if species_match:
                species = species_match.group(1)
                print(f"[CHARACTER PROFILE] Extracted species from description: {species}")
            else:
                # Default to generic "character"
                species = "character"
                print(f"[CHARACTER PROFILE] Could not determine species, using default: {species}")

        # Create CharacterProfile with fallbacks for missing fields
        profile = CharacterProfile(
            name=character.name,
            species=species,
            physical_description=data.get("physical_description") or character.description,
            clothing=data.get("clothing"),
            distinctive_features=data.get("distinctive_features"),
            personality_traits=data.get("personality_traits")
        )

        print(f"[CHARACTER PROFILE] Created profile: {profile.name} ({profile.species})")
        return profile
