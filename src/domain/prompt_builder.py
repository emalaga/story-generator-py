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

        # Calculate word requirements
        words_per_page = metadata.words_per_page or 50
        min_words = int(words_per_page * 0.9)
        total_words = metadata.num_pages * words_per_page

        # Estimate sentences per page (average ~12-15 words per sentence)
        sentences_per_page = max(8, words_per_page // 12)

        # CRITICAL: Word count as PRIMARY instruction at the very beginning
        prompt_parts.append(
            f"MANDATORY WORD COUNT: Write a story with EXACTLY {metadata.num_pages} pages. "
            f"Each page MUST have AT LEAST {min_words} words (target: {words_per_page} words). "
            f"This means each page needs approximately {sentences_per_page}-{sentences_per_page + 3} full sentences. "
            f"Total story length: approximately {total_words} words."
        )

        # Story type and requirements
        prompt_parts.append(
            f"\n\nWrite a {metadata.complexity} children's story in {metadata.language} "
            f"for ages {metadata.age_group}."
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

        # Formatting instructions with word count reminder
        prompt_parts.append(
            f"\n\nFORMATTING RULES:\n"
            f"1. Write exactly {metadata.num_pages} pages\n"
            f"2. Each page MUST have {min_words}-{words_per_page + 20} words (NOT 50 words - that is TOO SHORT)\n"
            f"3. Use this format:\n"
            f"Page 1:\n[Write {words_per_page} words of story here - multiple paragraphs, rich detail]\n\n"
            f"Page 2:\n[Write {words_per_page} words of story here]\n\n"
            f"...and so on.\n\n"
            f"CRITICAL: Do NOT write short pages. Each page needs {sentences_per_page}+ sentences with descriptive details, "
            f"dialogue, character emotions, and scene-setting. Expand the narrative - do not summarize."
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
        Use AI to identify the single most exciting, dramatic moment from the page text.

        Takes a full page of story text and extracts the ONE KEY MOMENT that would
        make the most compelling illustration - the climax, turning point, or most
        visually exciting action in that part of the story.

        Args:
            scene_text: Full story page text
            character_profiles: Optional list of characters to maintain consistency

        Returns:
            Concise scene description (40-60 words) focusing on the single most exciting moment
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

        system_message = """You are an expert children's book illustrator choosing THE SINGLE MOST EXCITING MOMENT to illustrate from a story page.

Your task is to identify the ONE DRAMATIC MOMENT that would make the most compelling illustration - not a summary of the page, but the PEAK MOMENT that captures:
- The most exciting action (a kick, a fall, a discovery, a hug, a confrontation)
- The emotional climax (triumph, despair, surprise, joy)
- The turning point or pivotal instant

Think like an illustrator: What single frozen moment would a reader remember? What captures the drama?

Examples of what to look for:
- "The ball flew toward the goal" NOT "Pablo practiced soccer every day"
- "Maria's eyes widened as she opened the treasure chest" NOT "Maria went on an adventure"
- "The dragon breathed fire as the knight raised his shield" NOT "The knight fought the dragon"

CRITICAL REQUIREMENTS:
- Describe ONE SPECIFIC MOMENT, not a sequence of events
- Include the specific ACTION happening at that instant
- Use the exact character names provided - no assumptions about gender or appearance
- Every sentence must be grammatically complete
- Always end with proper punctuation

DO NOT include:
- General summaries ("Pablo loved soccer")
- Multiple events ("First... then... finally...")
- Abstract feelings without visible action
- Narrative commentary

Return ONLY a vivid description (40-60 words) of that single dramatic moment an illustrator should capture."""

        prompt = f"""Read this story page and identify THE SINGLE MOST EXCITING MOMENT to illustrate:{character_context}

Story page text:
{scene_text}

What is the ONE DRAMATIC MOMENT that would make the best illustration? Describe that specific instant with vivid, visual detail. Focus on the action, not a summary."""

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
        Build a prompt for AI image generation that references session context.

        This prompt assumes the conversation session already contains:
        - The art bible image and style definition
        - Character reference images and descriptions

        The prompt references these by name rather than repeating all details,
        focusing primarily on the scene description.

        Args:
            scene_description: Description of the scene to illustrate
            character_profiles: List of character profiles (for identifying characters in scene)
            art_style: Artistic style (e.g., "cartoon", "watercolor", "realistic")
            art_bible: Optional art bible (used to check if art bible exists)
            character_references: Optional character references (used to check which characters have references)

        Returns:
            Formatted prompt string for AI image generation that leverages session context
        """
        prompt_parts = []

        # Reference the art bible from the conversation session
        if art_bible:
            prompt_parts.append(
                f"CRITICAL: Generate the next illustration for this children's book. "
                f"You MUST strictly follow the {art_style} visual style defined in the art bible image "
                "we established earlier in this conversation. Match the exact same colors, line weight, "
                "shading technique, and overall aesthetic."
            )
        else:
            prompt_parts.append(
                f"Create a {art_style} style children's book illustration."
            )

        # Identify characters in this scene (by name only - descriptions are in session)
        if character_profiles:
            scene_lower = scene_description.lower()
            characters_in_scene = [
                profile.name for profile in character_profiles
                if profile.name and profile.name.lower() in scene_lower
            ]

            if characters_in_scene and character_references:
                # Check which characters have references in the session
                chars_with_refs = [
                    name for name in characters_in_scene
                    if any(ref.character_name == name for ref in character_references)
                ]

                if chars_with_refs:
                    if len(chars_with_refs) == 1:
                        prompt_parts.append(
                            f"Include {chars_with_refs[0]} in this scene, drawing them EXACTLY as shown "
                            "in the character reference image we created earlier. "
                            "The character's appearance, proportions, colors, and clothing must be identical."
                        )
                    else:
                        names_str = ", ".join(chars_with_refs[:-1]) + f" and {chars_with_refs[-1]}"
                        prompt_parts.append(
                            f"Include {names_str} in this scene, drawing each character EXACTLY as shown "
                            "in their character reference images we created earlier. "
                            "Each character's appearance, proportions, colors, and clothing must be identical."
                        )
            elif characters_in_scene:
                # Characters exist but no references - just mention them
                if len(characters_in_scene) == 1:
                    prompt_parts.append(f"Show {characters_in_scene[0]} in this scene.")
                else:
                    names_str = ", ".join(characters_in_scene[:-1]) + f" and {characters_in_scene[-1]}"
                    prompt_parts.append(f"Show {names_str} in this scene.")

        # Scene description - the main focus of this prompt
        scene_summary = self._smart_truncate_sentences(scene_description, 400)
        prompt_parts.append(f"Scene: {scene_summary}")

        # Final consistency reminder
        prompt_parts.append(
            "Maintain perfect visual consistency with all previous illustrations in this story. "
            "Professional, vibrant, child-friendly children's book illustration."
        )

        return " ".join(prompt_parts)

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

        # Physical description - use sentence-aware truncation to avoid mid-sentence cuts
        if character.physical_description:
            prompt_parts.append(
                f"with this appearance: {self._smart_truncate_sentences(character.physical_description, 300)}"
            )

        # Clothing - use sentence-aware truncation for multi-sentence descriptions
        if character.clothing:
            prompt_parts.append(
                f"wearing {self._smart_truncate_sentences(character.clothing, 200)}"
            )

        # Distinctive features
        if character.distinctive_features:
            prompt_parts.append(
                f"with distinctive features: {self._smart_truncate_sentences(character.distinctive_features, 200)}"
            )

        # Personality traits (for expression/pose)
        if character.personality_traits:
            prompt_parts.append(
                f"showing a {self._smart_truncate_sentences(character.personality_traits, 150)} expression"
            )

        # Critical restrictions - be VERY explicit to avoid character sheets/grids
        prompt_parts.append(
            "IMPORTANT: Create ONE SINGLE full-color illustration showing the character ONCE in a natural standing or sitting pose. "
            "Use vibrant, rich colors appropriate for a children's book. "
            "Plain white background. "
            "DO NOT create a character sheet, model sheet, turnaround, reference sheet, or grid. "
            "DO NOT show multiple views, angles, or copies of the character. "
            "DO NOT use black and white or grayscale. "
            "Just ONE colorful illustration of the character."
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

    async def build_cover_prompt(
        self,
        story_title: str,
        story_summary: str,
        main_character: Optional[dict] = None,
        characters: Optional[List[dict]] = None,
        art_style: str = "cartoon",
        genre: str = ""
    ) -> str:
        """
        Build a prompt for generating a book cover image.

        Uses AI to create a compelling, movie-poster-style cover prompt that:
        - Features the main character in an important story moment
        - Is eye-catching and dramatic
        - Doesn't reveal the ending
        - Is suitable for a book cover

        Args:
            story_title: Title of the story
            story_summary: Summary or concatenated text from story pages
            main_character: Optional dict with main character details
            characters: Optional list of all characters
            art_style: Art style (e.g., "cartoon", "watercolor")
            genre: Story genre

        Returns:
            Generated cover prompt
        """
        if not self.ai_client:
            # Fallback without AI - create a basic prompt
            return self._build_basic_cover_prompt(story_title, main_character, art_style, genre)

        # Build character context
        character_context = ""
        if main_character:
            char_name = main_character.get('name', 'the protagonist')
            char_species = main_character.get('species', '')
            char_desc = main_character.get('physical_description', '')
            character_context = f"\n\nMain character: {char_name}"
            if char_species:
                character_context += f" (a {char_species})"
            if char_desc:
                character_context += f" - {char_desc[:200]}"
        elif characters and len(characters) > 0:
            char = characters[0]
            char_name = char.get('name', 'the protagonist')
            char_species = char.get('species', '')
            character_context = f"\n\nMain character: {char_name}"
            if char_species:
                character_context += f" (a {char_species})"

        system_message = """You are an expert children's book cover designer. Your task is to create a compelling cover image prompt that:

1. Features the main character in a DRAMATIC, EYE-CATCHING pose or moment
2. Captures a PIVOTAL moment from the story (but NOT the ending)
3. Has the visual impact of a MOVIE POSTER - bold, exciting, memorable
4. Is APPROPRIATE for children while still being exciting
5. Would make a child want to pick up the book immediately

Think about:
- What makes blockbuster movie posters compelling
- The "hero shot" - showing the protagonist in their most impressive light
- Dynamic composition that draws the eye
- A moment of adventure, discovery, or courage

DO NOT:
- Describe multiple scenes or a sequence of events
- Reveal the ending or resolution
- Include text, title, or credits in the image description
- Make it boring or static

Return ONLY a vivid, detailed image prompt (60-100 words) describing the cover scene."""

        prompt = f"""Create a compelling book cover image prompt for:

Title: "{story_title}"
Genre: {genre or 'children\'s fiction'}
Art Style: {art_style}
{character_context}

Story summary (for context - do NOT summarize, use it to identify the best cover moment):
{story_summary[:1500]}

What single dramatic moment or heroic pose would make the most compelling, movie-poster-style cover for this children's book? Describe that scene vividly."""

        try:
            cover_prompt = await self.ai_client.generate_text(
                prompt,
                system_message=system_message,
                temperature=0.7,
                max_tokens=300
            )
            cover_prompt = cover_prompt.strip()

            # Add art style and technical requirements
            final_prompt = (
                f"Create a {art_style} style children's book cover illustration. "
                f"{cover_prompt} "
                "This should look like a professional book cover - bold, dynamic composition with "
                "rich colors and dramatic lighting. Movie-poster quality. Child-friendly but exciting. "
                "No text, title, or credits - just the illustration."
            )

            return final_prompt

        except Exception:
            # Fallback to basic prompt if AI fails
            return self._build_basic_cover_prompt(story_title, main_character, art_style, genre)

    def _build_basic_cover_prompt(
        self,
        story_title: str,
        main_character: Optional[dict] = None,
        art_style: str = "cartoon",
        genre: str = ""
    ) -> str:
        """
        Build a basic cover prompt without AI assistance.

        Used as a fallback when AI client is not available.
        """
        prompt_parts = [
            f"Create a {art_style} style children's book cover illustration for '{story_title}'."
        ]

        if main_character:
            char_name = main_character.get('name', 'the protagonist')
            char_species = main_character.get('species', '')
            if char_species:
                prompt_parts.append(f"Feature {char_name}, a {char_species}, in a heroic or adventurous pose.")
            else:
                prompt_parts.append(f"Feature {char_name} in a heroic or adventurous pose.")

        if genre:
            prompt_parts.append(f"The style should fit a {genre} story.")

        prompt_parts.append(
            "This should look like a professional book cover - bold, dynamic composition with "
            "rich colors and dramatic lighting. Movie-poster quality. Child-friendly but exciting. "
            "No text, title, or credits - just the illustration."
        )

        return " ".join(prompt_parts)
