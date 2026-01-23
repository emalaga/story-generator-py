"""
Prompt Builder for creating AI prompts for story and image generation.

This module builds prompts for AI text generation (stories) and image generation,
incorporating story parameters, character profiles, and formatting requirements.
"""

from typing import List, Optional, TYPE_CHECKING

from src.models.character import CharacterProfile
from src.models.story import StoryMetadata

if TYPE_CHECKING:
    from src.models.art_bible import ArtBible, CharacterReference


class PromptBuilder:
    """
    Builds prompts for AI text and image generation.

    This class creates well-structured prompts that incorporate story parameters,
    character details, and artistic style requirements for consistent generation.
    """

    def __init__(self, ai_client=None):
        """
        Initialize the prompt builder.

        Args:
            ai_client: Optional AI client for intelligent scene summarization
        """
        self.ai_client = ai_client

    def build_story_prompt(
        self,
        metadata: StoryMetadata,
        theme: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> str:
        """
        Build a prompt for AI story generation.

        Creates a detailed prompt that specifies story parameters, formatting,
        and content requirements for the AI to generate an appropriate story.

        Args:
            metadata: Story metadata with language, complexity, age group, etc.
            theme: Optional theme or moral for the story
            custom_prompt: Optional custom story idea from the user

        Returns:
            Formatted prompt string for AI story generation
        """
        prompt_parts = []

        # Story type and requirements
        prompt_parts.append(
            f"Write a {metadata.complexity} children's story in {metadata.language} "
            f"for ages {metadata.age_group}."
        )

        # Number of pages and words per page
        words_per_page = metadata.words_per_page or 50
        prompt_parts.append(
            f"The story should have exactly {metadata.num_pages} pages, "
            f"with each page containing approximately {words_per_page} words."
        )

        # Genre if specified
        if metadata.genre:
            prompt_parts.append(f"Genre: {metadata.genre}.")

        # Theme if provided
        if theme:
            prompt_parts.append(f"Theme: {theme}.")

        # Custom prompt if provided
        if custom_prompt:
            prompt_parts.append(f"Story idea: {custom_prompt}.")

        # Vocabulary requirements
        prompt_parts.append(
            f"Use {metadata.vocabulary_diversity} vocabulary appropriate for "
            f"the {metadata.age_group} age group."
        )

        # Formatting instructions
        prompt_parts.append(
            "\n\nFormat the story with clear page breaks. "
            "For each page, write:\n"
            "Page X:\n[Story text for that page]\n\n"
            "Make the story engaging, age-appropriate, and complete within the specified number of pages."
        )

        return " ".join(prompt_parts)

    @staticmethod
    def _smart_truncate(text: str, max_length: int) -> str:
        """
        Truncate text to max_length without cutting words.

        Args:
            text: Text to truncate
            max_length: Maximum length in characters

        Returns:
            Truncated text that doesn't end mid-word
        """
        if not text or len(text) <= max_length:
            return text

        # Find the last space before max_length
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')

        if last_space > 0:
            return truncated[:last_space]
        else:
            # No spaces found, just truncate at max_length
            return truncated

    @staticmethod
    def _is_valid_short_word(word: str) -> bool:
        """
        Check if a short word (1-3 chars) is a valid English/Spanish word.

        Used to detect truncated words like "sc" or "att" that end with punctuation
        but are clearly incomplete.

        Args:
            word: The word to check (lowercase, no punctuation)

        Returns:
            True if it's a valid short word, False if likely truncated
        """
        # Common valid 1-3 letter words in English and Spanish
        valid_short_words = {
            # English
            'a', 'i', 'an', 'as', 'at', 'be', 'by', 'do', 'go', 'he', 'if', 'in',
            'is', 'it', 'me', 'my', 'no', 'of', 'on', 'or', 'so', 'to', 'up', 'us',
            'we', 'am', 'are', 'was', 'has', 'had', 'can', 'did', 'get', 'got',
            'her', 'him', 'his', 'its', 'let', 'may', 'new', 'now', 'old', 'one',
            'our', 'out', 'own', 'put', 'ran', 'run', 'saw', 'say', 'see', 'set',
            'she', 'sit', 'the', 'too', 'try', 'two', 'use', 'way', 'who', 'why',
            'win', 'won', 'yes', 'yet', 'you', 'all', 'any', 'big', 'but', 'day',
            'end', 'far', 'few', 'for', 'fun', 'how', 'lot', 'man', 'men', 'not',
            'off', 'red', 'sad', 'ten', 'top', 'boy', 'cup', 'dog', 'eat', 'eye',
            'fly', 'hot', 'ice', 'job', 'joy', 'key', 'kid', 'leg', 'map', 'mom',
            'dad', 'sun', 'sky', 'sea', 'air', 'bed', 'car', 'hat', 'arm', 'bag',
            # Spanish common words
            'el', 'la', 'lo', 'le', 'un', 'de', 'en', 'es', 'se', 'no', 'me', 'te',
            'ya', 'ni', 'si', 'yo', 'tu', 'su', 'al', 'mi', 'que', 'con', 'por',
            'una', 'los', 'las', 'del', 'mas', 'muy', 'era', 'fue', 'ser', 'son',
            'hay', 'tan', 'vez', 'sin', 'hoy', 'esa', 'ese', 'eso', 'dia', 'sol',
            # Numbers
            'one', 'two', 'six', 'ten', 'uno', 'dos', 'tre', 'mil',
        }
        return word.lower() in valid_short_words

    @staticmethod
    def _has_truncated_word(text: str) -> bool:
        """
        Check if text ends with a truncated word (incomplete word before punctuation).

        Detects patterns like "He attempts to sc." where "sc" is clearly truncated.

        Args:
            text: Text to check

        Returns:
            True if the text appears to end with a truncated word
        """
        if not text or len(text) < 3:
            return False

        # Remove trailing whitespace
        text = text.rstrip()

        # Check if ends with sentence punctuation
        if not text[-1] in '.!?':
            return False

        # Get the last word (before the punctuation)
        text_without_punct = text[:-1].rstrip()
        if not text_without_punct:
            return False

        # Find the last word
        last_space = text_without_punct.rfind(' ')
        if last_space == -1:
            last_word = text_without_punct
        else:
            last_word = text_without_punct[last_space + 1:]

        # Clean the word (remove any remaining punctuation)
        last_word = ''.join(c for c in last_word if c.isalnum())

        if not last_word:
            return False

        # If the word is very short (1-3 chars) and not a valid short word,
        # it's likely truncated
        if len(last_word) <= 3:
            return not PromptBuilder._is_valid_short_word(last_word)

        return False

    @staticmethod
    def _smart_truncate_sentences(text: str, max_length: int) -> str:
        """
        Truncate text to max_length at sentence boundaries to avoid mid-sentence cuts.

        Args:
            text: Text to truncate
            max_length: Maximum length in characters

        Returns:
            Truncated text that ends at a complete sentence when possible
        """
        if not text or len(text) <= max_length:
            return text

        # Look for the last sentence-ending punctuation before max_length
        truncated = text[:max_length]

        # Find the last sentence-ending punctuation
        sentence_enders = ['.', '!', '?']
        last_sentence_end = -1

        for ender in sentence_enders:
            pos = truncated.rfind(ender)
            if pos > last_sentence_end:
                # Make sure it's not part of an abbreviation (e.g., "Mr." or "Dr.")
                # by checking if the next character is a space or end of string
                if pos == len(truncated) - 1 or (pos < len(truncated) - 1 and truncated[pos + 1] in ' \n\t'):
                    last_sentence_end = pos

        if last_sentence_end > max_length // 3:  # Only use sentence boundary if it's not too short
            return truncated[:last_sentence_end + 1].strip()
        else:
            # Fall back to word boundary truncation
            last_space = truncated.rfind(' ')
            if last_space > 0:
                return truncated[:last_space]
            return truncated

    async def summarize_scene(
        self,
        scene_text: str,
        character_profiles: Optional[List[CharacterProfile]] = None
    ) -> str:
        """
        Use AI to create a concise scene summary for image generation.

        Takes a full page of story text and extracts the main visual scene
        that should be illustrated, removing narrative elements and focusing
        on the key visual moment.

        Args:
            scene_text: Full story page text
            character_profiles: Optional list of characters to maintain consistency

        Returns:
            Concise scene description (30-50 words) focusing on visual elements
        """
        if not self.ai_client:
            # Fallback: sentence-aware truncation if no AI client available
            return self._smart_truncate_sentences(scene_text, 300)

        # Build character context if provided
        character_context = ""
        if character_profiles:
            chars = []
            for profile in character_profiles[:3]:  # Include up to 3 main characters
                char_info = f"{profile.name} (a {profile.species})"
                chars.append(char_info)
            if chars:
                character_context = f"\n\nMain characters in this story: {', '.join(chars)}"

        system_message = """You are an expert at analyzing children's story text and identifying the main visual scene to illustrate.
Your task is to extract the KEY VISUAL MOMENT from the story page that should be drawn.

Focus on:
- Main action or event happening
- Character positions and activities (use the exact character names and species provided)
- Setting and environment
- Emotional tone

CRITICAL REQUIREMENTS:
- Use ONLY the character information provided - do not make assumptions about gender, appearance, or other details
- Refer to characters by their exact names and species
- Do not add details not present in the story text
- EVERY sentence MUST be grammatically complete - never end mid-sentence or with incomplete phrases
- Always end with proper punctuation (period, exclamation mark, or question mark)

Ignore:
- Narrative commentary
- Internal thoughts
- Abstract concepts that can't be visualized

Return ONLY a concise scene description (40-60 words) that an illustrator could draw. Ensure all sentences are complete."""

        prompt = f"""Analyze this children's story page and describe the main scene to illustrate:{character_context}

Story page text:
{scene_text}

Write a complete scene description with no incomplete sentences. Return only the scene description."""

        try:
            summary = await self.ai_client.generate_text(
                prompt,
                system_message=system_message,
                temperature=0.3,
                max_tokens=200  # Ensure enough tokens for a complete 40-60 word summary
            )
            summary = summary.strip()

            # Validate the summary - check for incomplete sentences
            # If the last sentence doesn't end with proper punctuation, it might be truncated
            if summary and not summary[-1] in '.!?':
                # Try to find the last complete sentence
                last_complete = max(
                    summary.rfind('.'),
                    summary.rfind('!'),
                    summary.rfind('?')
                )
                if last_complete > len(summary) // 2:
                    summary = summary[:last_complete + 1]
                else:
                    # Summary is too incomplete, fall back to smart truncation
                    return self._smart_truncate_sentences(scene_text, 300)

            # Check for truncated words (e.g., "He attempts to sc.")
            # This happens when the AI output ends with punctuation but the last word is incomplete
            if self._has_truncated_word(summary):
                # Find the last complete sentence (second-to-last sentence ending)
                # by removing the truncated sentence
                summary_without_last = summary[:-1].rstrip()  # Remove final punctuation
                last_complete = max(
                    summary_without_last.rfind('.'),
                    summary_without_last.rfind('!'),
                    summary_without_last.rfind('?')
                )
                if last_complete > len(summary) // 3:
                    summary = summary_without_last[:last_complete + 1]
                else:
                    # Can't salvage, fall back to smart truncation of original
                    return self._smart_truncate_sentences(scene_text, 300)

            return summary
        except Exception:
            # Fallback to sentence-aware truncation if AI fails
            return self._smart_truncate_sentences(scene_text, 300)

    def build_image_prompt(
        self,
        scene_description: str,
        character_profiles: List[CharacterProfile],
        art_style: str,
        art_bible: Optional["ArtBible"] = None,
        character_references: Optional[List["CharacterReference"]] = None
    ) -> str:
        """
        Build a prompt for AI image generation with art bible and character reference guidance.

        Creates a detailed prompt optimized for GPT-Image and DALL-E, incorporating
        character profiles, art bible style constraints, and character references to ensure
        visual consistency across all illustrations.

        Args:
            scene_description: Description of the scene to illustrate
            character_profiles: List of character profiles for consistency
            art_style: Artistic style (e.g., "cartoon", "watercolor", "realistic")
            art_bible: Optional art bible with style guidelines (color, lighting, technique)
            character_references: Optional character references with detailed appearance info

        Returns:
            Formatted prompt string for AI image generation (optimized for GPT-Image/DALL-E)
        """
        prompt_parts = []

        # Art style with explicit art bible constraints if available
        if art_bible:
            style_details = []
            style_details.append(f"{art_style} style")

            # Add all available art bible details for maximum consistency
            if art_bible.color_palette:
                style_details.append(f"color palette: {self._smart_truncate(art_bible.color_palette, 80)}")
            if art_bible.lighting_style:
                style_details.append(f"lighting: {self._smart_truncate(art_bible.lighting_style, 60)}")
            if art_bible.brush_technique:
                style_details.append(f"technique: {self._smart_truncate(art_bible.brush_technique, 60)}")
            if art_bible.style_notes:
                style_details.append(f"{self._smart_truncate(art_bible.style_notes, 100)}")

            prompt_parts.append(
                f"CRITICAL: Create a children's book illustration in EXACTLY this style - " +
                ", ".join(style_details) +
                ". This MUST match the established visual style perfectly with consistent line weight, shading, and colors throughout the entire book."
            )
        else:
            prompt_parts.append(f"A {art_style} style children's book illustration")

        # Add main characters with character reference constraints if available
        # Only include characters that are mentioned in the scene description
        if character_profiles:
            character_descriptions = []
            scene_lower = scene_description.lower()
            # Filter to only characters mentioned in the scene
            characters_in_scene = [
                profile for profile in character_profiles
                if profile.name and profile.name.lower() in scene_lower
            ]
            for profile in characters_in_scene[:2]:  # Limit to 2 characters max
                # Try to find matching character reference for this character
                char_ref = None
                if character_references:
                    char_ref = next(
                        (ref for ref in character_references if ref.character_name == profile.name),
                        None
                    )

                if profile.name and profile.species and profile.physical_description:
                    # Create VERY detailed character description for maximum consistency
                    char_details = []

                    # Always include species and physical description
                    char_details.append(f"a {profile.species}")
                    char_details.append(self._smart_truncate(profile.physical_description, 120))

                    # Add distinctive features (these are critical for consistency)
                    if profile.distinctive_features:
                        char_details.append(self._smart_truncate(profile.distinctive_features, 80))

                    # Add clothing details
                    if profile.clothing:
                        char_details.append(f"wearing {self._smart_truncate(profile.clothing, 80)}")

                    # Add personality for expression/pose
                    if profile.personality_traits:
                        char_details.append(f"with {self._smart_truncate(profile.personality_traits, 60)} demeanor")

                    if char_ref:
                        char_desc = (
                            f"{profile.name} (CRITICAL - MUST be drawn EXACTLY THE SAME in every image: " +
                            ", ".join(char_details) +
                            ". Draw this character with IDENTICAL appearance in EVERY illustration)"
                        )
                    else:
                        char_desc = f"{profile.name} (" + ", ".join(char_details) + ")"

                    character_descriptions.append(char_desc)
                elif profile.species and profile.physical_description:
                    # Character without name but has species and description
                    phys_desc = self._smart_truncate(profile.physical_description, 100)
                    char_desc = f"a {profile.species} ({phys_desc}"
                    if profile.distinctive_features:
                        char_desc += f", {self._smart_truncate(profile.distinctive_features, 60)}"
                    if profile.clothing:
                        char_desc += f", {self._smart_truncate(profile.clothing, 60)}"
                    char_desc += ")"
                    character_descriptions.append(char_desc)

            if character_descriptions:
                prompt_parts.append("showing " + " and ".join(character_descriptions))

        # Scene description - extract key elements without cutting mid-sentence
        scene_summary = self._smart_truncate_sentences(scene_description, 300)

        # Add the scene action/setting
        prompt_parts.append(f"in this scene: {scene_summary}")

        # Add final quality and consistency instructions
        if art_bible or character_references:
            prompt_parts.append(
                "CRITICAL REQUIREMENTS FOR CONSISTENCY: "
                "1) Use EXACTLY the same art style, colors, line weight, and shading as described above in EVERY detail. "
                "2) Draw characters with IDENTICAL features, proportions, colors, and clothing in EVERY scene. "
                "3) Maintain the EXACT same visual aesthetic throughout - this is part of a series that must look cohesive. "
                "Professional, vibrant, child-friendly children's book illustration."
            )
        else:
            prompt_parts.append("Vibrant colors, child-friendly, professional children's book illustration style.")

        # Join with spaces
        full_prompt = " ".join(prompt_parts)

        # If prompt is too long, prioritize art bible and character reference constraints
        # by shortening the scene summary (not character details)
        if len(full_prompt) > 1500:
            # Use sentence-aware truncation to avoid cutting mid-word or mid-sentence
            scene_summary_short = self._smart_truncate_sentences(scene_description, 120)
            # Rebuild with shorter summary
            summary_idx = None
            for i, part in enumerate(prompt_parts):
                if "in this scene:" in part:
                    summary_idx = i
                    break
            if summary_idx is not None:
                prompt_parts[summary_idx] = f"in this scene: {scene_summary_short}"
                full_prompt = " ".join(prompt_parts)

        return full_prompt

    def build_art_bible_prompt(
        self,
        art_style: str,
        genre: Optional[str] = None,
        story_title: Optional[str] = None,
        additional_notes: Optional[str] = None
    ) -> str:
        """
        Build a prompt for generating an art bible reference image.

        The art bible image establishes the visual style, color palette,
        lighting, and artistic direction for all story illustrations.

        Args:
            art_style: Primary art style (e.g., "cartoon", "watercolor", "realistic")
            genre: Optional story genre to inform the visual style
            story_title: Optional story title for context
            additional_notes: Optional user-provided style notes

        Returns:
            Formatted prompt for art bible image generation
        """
        prompt_parts = []

        # Base instruction - create a sample scene that demonstrates the visual style
        prompt_parts.append(
            f"Create a sample scene illustration in {art_style} style for a children's book."
        )

        # Genre context if provided
        if genre:
            prompt_parts.append(
                f"The scene should fit a {genre} story for children."
            )

        # Story context if provided
        if story_title:
            prompt_parts.append(
                f"This is a reference illustration for a story titled '{story_title}'."
            )

        # Additional style notes
        if additional_notes:
            prompt_parts.append(f"Style notes: {additional_notes}")

        # Simple scene instruction
        prompt_parts.append(
            "The scene should showcase the visual style, colors, lighting, and artistic approach "
            "that will be used throughout the book. No text, labels, color swatches, or technical diagrams. "
            "Just a beautiful example illustration that demonstrates the artistic direction."
        )

        return " ".join(prompt_parts)

    def build_character_reference_prompt(
        self,
        character: CharacterProfile,
        art_style: str,
        include_turnaround: bool = True
    ) -> str:
        """
        Build a prompt for generating a character reference image.

        The character reference shows a single, clear portrait of the character
        to maintain visual consistency across all story illustrations.

        Args:
            character: Character profile with physical description
            art_style: Art style to match the story's visual direction
            include_turnaround: Whether to include multiple angles (default: True)
                               Note: This parameter is kept for backwards compatibility but is now ignored

        Returns:
            Formatted prompt for character reference image generation
        """
        prompt_parts = []

        # Base instruction - single character portrait with explicit restrictions
        prompt_parts.append(
            f"A {art_style} style illustration of {character.name}"
        )

        # Species and basic description
        if character.species:
            prompt_parts.append(f"who is a {character.species}")

        # Physical description
        if character.physical_description:
            prompt_parts.append(
                f"with this appearance: {self._smart_truncate(character.physical_description, 150)}"
            )

        # Clothing
        if character.clothing:
            prompt_parts.append(
                f"wearing {self._smart_truncate(character.clothing, 100)}"
            )

        # Distinctive features
        if character.distinctive_features:
            prompt_parts.append(
                f"with distinctive features: {self._smart_truncate(character.distinctive_features, 100)}"
            )

        # Personality traits (for expression/pose)
        if character.personality_traits:
            prompt_parts.append(
                f"showing a {self._smart_truncate(character.personality_traits, 80)} expression"
            )

        # Critical restrictions - be very explicit
        prompt_parts.append(
            "Create a single image of the character in a natural standing or sitting pose with a plain white background. No text, No lines, No other elements."
        )

        return " ".join(prompt_parts)

    def create_art_bible(
        self,
        art_style: str,
        genre: Optional[str] = None,
        story_title: Optional[str] = None,
        additional_notes: Optional[str] = None
    ) -> "ArtBible":
        """
        Create an ArtBible object with a generated prompt.

        Args:
            art_style: Primary art style
            genre: Optional story genre
            story_title: Optional story title
            additional_notes: Optional user-provided style notes

        Returns:
            ArtBible object with generated prompt
        """
        from src.models.art_bible import ArtBible

        prompt = self.build_art_bible_prompt(art_style, genre, story_title, additional_notes)

        return ArtBible(
            prompt=prompt,
            art_style=art_style,
            style_notes=additional_notes
        )

    def create_character_reference(
        self,
        character: CharacterProfile,
        art_style: str,
        include_turnaround: bool = True
    ) -> "CharacterReference":
        """
        Create a CharacterReference object with a generated prompt.

        Args:
            character: Character profile
            art_style: Art style to match the story
            include_turnaround: Whether to include multiple angles

        Returns:
            CharacterReference object with generated prompt
        """
        from src.models.art_bible import CharacterReference

        prompt = self.build_character_reference_prompt(character, art_style, include_turnaround)

        return CharacterReference(
            character_name=character.name,
            prompt=prompt,
            species=character.species,
            physical_description=character.physical_description,
            clothing=character.clothing,
            distinctive_features=character.distinctive_features
        )

    def build_conversation_prompt(
        self,
        scene_description: str,
        character_profiles: List[CharacterProfile],
        art_style: str
    ) -> str:
        """
        Build a simplified prompt for conversation-based image generation.

        This prompt assumes the conversation context already contains the art bible
        and character reference information, so it only needs to describe the scene
        and reference previously established elements.

        Only characters that are mentioned in the scene description will be included
        in the prompt to avoid adding characters that don't belong in the scene.

        Args:
            scene_description: Description of the scene to illustrate
            character_profiles: List of character profiles (for reference by name)
            art_style: Artistic style (e.g., "cartoon", "watercolor")

        Returns:
            Simplified prompt that leverages conversation context
        """
        prompt_parts = []

        # Reference the established style
        prompt_parts.append(
            f"Generate the next illustration for this children's book using the {art_style} "
            "style we established in the art bible."
        )

        # Filter characters to only those mentioned in the scene description
        scene_lower = scene_description.lower()
        characters_in_scene = []
        if character_profiles:
            for profile in character_profiles:
                if profile.name and profile.name.lower() in scene_lower:
                    characters_in_scene.append(profile.name)

        # Reference only characters that appear in this scene
        if characters_in_scene:
            if len(characters_in_scene) == 1:
                prompt_parts.append(
                    f"Include {characters_in_scene[0]} exactly as we designed them in the character reference."
                )
            else:
                names_str = ", ".join(characters_in_scene[:-1]) + f" and {characters_in_scene[-1]}"
                prompt_parts.append(
                    f"Include {names_str} exactly as we designed them in the character references."
                )

        # Scene description - the main content, truncated at sentence boundaries
        scene_summary = self._smart_truncate_sentences(scene_description, 400)
        prompt_parts.append(f"Scene: {scene_summary}")

        # Brief quality reminder
        prompt_parts.append(
            "Maintain perfect visual consistency with all previous illustrations in this story."
        )

        return " ".join(prompt_parts)
