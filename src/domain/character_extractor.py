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

CRITICAL: Return your response as valid JSON in this EXACT format:
{
    "characters": [
        {
            "name": "Character Name",
            "description": "Brief physical description"
        }
    ]
}

IMPORTANT FIELD REQUIREMENTS:
- The field MUST be called "name" (not "character_name" or anything else)
- The field MUST be called "description" (not "physical_description" or anything else)
- Both fields are REQUIRED for every character

Guidelines:
- Include ALL characters mentioned in the story
- Keep descriptions concise but visually descriptive
- Focus on physical appearance (species, color, size, distinctive features)
- Maintain the order characters appear in the story
- Use the exact names from the story"""

        prompt = f"""Extract all characters from this story:

{full_story}

Return ONLY valid JSON with "characters" array containing objects with "name" and "description" fields. No other text."""

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
            # Get name with fallbacks for alternative field names
            name = char_data.get("name") or char_data.get("character_name") or char_data.get("character") or "Unknown"

            # Get description with fallbacks for alternative field names
            description = (
                char_data.get("description") or
                char_data.get("physical_description") or
                char_data.get("brief_description") or
                char_data.get("desc") or
                "No description provided"
            )

            character = Character(
                name=name,
                description=description
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
    "species": "The exact species or type",
    "physical_description": "Detailed physical description with colors, sizes, and proportions",
    "clothing": "Description of what the character wears",
    "distinctive_features": "Unique visual features that make this character recognizable",
    "personality_traits": "Key personality traits that affect appearance"
}

CRITICAL - Species field requirements:
- The "species" field MUST be a specific species name, NOT a generic term
- NEVER use generic terms like "character", "creature", "being", or "figure"
- For humans: use "human", "boy", "girl", "man", "woman", "child"
- For animals: use the specific animal name like "dog", "cat", "rabbit", "fox", "bear", "lion", "mouse", "bird", "owl", "elephant"
- For fantasy creatures: use "dragon", "unicorn", "fairy", "mermaid", "giant", "troll", "elf"
- For insects: use "butterfly", "bee", "ant", "caterpillar", "ladybug", "dragonfly"

Examples of CORRECT species values: "human", "dog", "cat", "rabbit", "dragon", "butterfly", "fox", "bear"
Examples of WRONG species values: "character", "creature", "protagonist", "main character", "being"

CRITICAL - Clothing field requirements:
- ALWAYS provide a clothing description, even if you need to invent appropriate attire
- For humans: describe shirt, pants, dress, shoes, accessories, colors
- For animals: describe any accessories like collars, bows, hats, or say "no clothing, natural fur/feathers"
- NEVER leave this field empty or null

CRITICAL - Distinctive features requirements:
- ALWAYS identify at least one distinctive visual feature
- Examples: "bright blue eyes", "curly red hair", "spotted fur pattern", "crooked smile", "long bushy tail"
- Think about what makes this character visually unique and recognizable
- NEVER leave this field empty or null

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

        prompt += """
IMPORTANT REQUIREMENTS:
1. For "species": Use a specific species name like "human", "dog", "cat", "rabbit", "dragon". Do NOT use "character" or "creature".
2. For "clothing": Describe what they wear (or "no clothing, natural fur/feathers" for animals). Do NOT leave empty.
3. For "distinctive_features": Identify at least one unique visual feature (eyes, hair, markings, etc.). Do NOT leave empty.

Return ONLY the JSON response with no additional text."""

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
        species = data.get("species", "").strip().lower() if data.get("species") else ""

        # List of generic/invalid species values that should be rejected
        invalid_species = ["character", "creature", "being", "figure", "protagonist",
                          "main character", "personaje", "criatura", "ser", ""]

        # If species is missing or generic, try to extract from description
        if not species or species in invalid_species:
            print(f"[CHARACTER PROFILE] Species '{species}' is invalid/generic, extracting from description")
            # Try to extract species from the character description
            # Look for common patterns like "a cat", "an elephant", etc.
            import re
            desc_lower = character.description.lower()
            # Common species patterns (English and Spanish) - expanded list
            species_patterns = [
                # Humans
                r'\b(human|boy|girl|man|woman|child|baby|kid|person|people|adult|teenager|elder|grandmother|grandfather|mother|father|sister|brother|niño|niña|hombre|mujer|bebé|persona|adulto|anciano|abuela|abuelo|madre|padre|hermana|hermano)\b',
                # Common animals
                r'\b(cat|dog|bird|fox|rabbit|mouse|elephant|lion|tiger|bear|wolf|deer|horse|fish|cow|pig|sheep|goat|chicken|duck|rooster|squirrel|raccoon|skunk|hedgehog|hamster|guinea pig|gato|perro|pájaro|zorro|conejo|ratón|elefante|león|tigre|oso|lobo|ciervo|caballo|pez|vaca|cerdo|oveja|cabra|gallina|pato|gallo|ardilla|mapache|mofeta|erizo|hámster)\b',
                # Fantasy creatures
                r'\b(dragon|unicorn|fairy|mermaid|giant|troll|elf|wizard|witch|goblin|ogre|phoenix|griffin|centaur|pegasus|dragón|unicornio|hada|sirena|gigante|duende|elfo|mago|bruja|fénix|grifo|centauro)\b',
                # Insects and small creatures
                r'\b(butterfly|bee|ant|spider|snake|frog|turtle|snail|worm|caterpillar|ladybug|dragonfly|grasshopper|cricket|firefly|beetle|fly|mosquito|mariposa|abeja|hormiga|araña|serpiente|rana|tortuga|caracol|gusano|oruga|mariquita|libélula|saltamontes|grillo|luciérnaga|escarabajo|mosca)\b',
                # Birds
                r'\b(owl|eagle|penguin|parrot|sparrow|crow|raven|swan|flamingo|peacock|toucan|pelican|seagull|pigeon|dove|hummingbird|búho|águila|pingüino|loro|gorrión|cuervo|cisne|flamenco|pavo real|tucán|pelícano|gaviota|paloma|colibrí)\b',
                # Sea creatures
                r'\b(dolphin|whale|shark|octopus|crab|jellyfish|starfish|seahorse|seal|walrus|otter|delfín|ballena|tiburón|pulpo|cangrejo|medusa|estrella de mar|caballito de mar|foca|morsa|nutria)\b',
                # Primates
                r'\b(monkey|ape|gorilla|chimpanzee|orangutan|mono|simio|gorila|chimpancé|orangután)\b'
            ]

            species_found = None
            for pattern in species_patterns:
                species_match = re.search(pattern, desc_lower)
                if species_match:
                    species_found = species_match.group(1)
                    break

            if species_found:
                species = species_found
                print(f"[CHARACTER PROFILE] Extracted species from description: {species}")
            else:
                # Last resort: check the name for species hints
                name_lower = character.name.lower()
                for pattern in species_patterns:
                    species_match = re.search(pattern, name_lower)
                    if species_match:
                        species_found = species_match.group(1)
                        break

                if species_found:
                    species = species_found
                    print(f"[CHARACTER PROFILE] Extracted species from name: {species}")
                else:
                    # Default to "human" as most stories feature human characters
                    species = "human"
                    print(f"[CHARACTER PROFILE] Could not determine species, defaulting to: {species}")

        # Create CharacterProfile with fallbacks for missing fields
        # Capitalize species for better display (e.g., "dog" -> "Dog")
        profile = CharacterProfile(
            name=character.name,
            species=species.capitalize() if species else "Human",
            physical_description=data.get("physical_description") or character.description,
            clothing=data.get("clothing"),
            distinctive_features=data.get("distinctive_features"),
            personality_traits=data.get("personality_traits")
        )

        print(f"[CHARACTER PROFILE] Created profile: {profile.name} ({profile.species})")
        return profile
