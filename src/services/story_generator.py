"""
Story Generator Service for orchestrating story generation workflow.

This service coordinates the complete story generation process, including:
- Building prompts with story parameters
- Generating story text using AI
- Parsing story pages
- Extracting characters
- Creating character profiles
"""

import re
import uuid
from typing import List, Optional, Tuple

from src.ai.base_client import BaseAIClient
from src.domain.character_extractor import CharacterExtractor
from src.domain.prompt_builder import PromptBuilder
from src.models.character import CharacterProfile
from src.models.story import Story, StoryMetadata, StoryPage


class StoryGeneratorService:
    """
    Orchestrates the complete story generation workflow.

    This service integrates AI text generation, prompt building, and character
    extraction to create complete stories with character profiles.
    """

    def __init__(
        self,
        ai_client: BaseAIClient,
        prompt_builder: PromptBuilder,
        character_extractor: CharacterExtractor
    ):
        """
        Initialize the story generator service.

        Args:
            ai_client: AI client for text generation
            prompt_builder: Builder for creating AI prompts
            character_extractor: Extractor for character analysis
        """
        self.ai_client = ai_client
        self.prompt_builder = prompt_builder
        self.character_extractor = character_extractor
        self._last_cost = 0.0

    async def generate_story(
        self,
        metadata: StoryMetadata,
        theme: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> Story:
        """
        Generate a complete story with characters.

        Orchestrates the full workflow:
        1. Build story generation prompt
        2. Generate story text using AI
        3. Parse story into pages
        4. Extract characters from story
        5. Create detailed character profiles

        Args:
            metadata: Story metadata with parameters
            theme: Optional theme or moral for the story
            custom_prompt: Optional custom story idea

        Returns:
            Complete Story with pages and character profiles

        Raises:
            Exception: If AI generation fails
        """
        # Step 1: Build prompt
        prompt = self.prompt_builder.build_story_prompt(
            metadata,
            theme=theme,
            custom_prompt=custom_prompt
        )

        # Step 2: Generate story text using AI
        # Use higher temperature for creative writing
        # Calculate max_tokens to ensure enough room for the full story
        # ~2 tokens per word (conservative estimate) + generous buffer
        words_per_page = metadata.words_per_page or 50
        total_words_needed = metadata.num_pages * words_per_page
        # Use 2 tokens per word and double it for safety margin
        max_tokens = int(total_words_needed * 2 * 2)
        # Ensure minimum of 2000 tokens and cap at 16000
        max_tokens = max(2000, min(max_tokens, 16000))

        print(f"[STORY GENERATOR] Requesting {metadata.num_pages} pages x {words_per_page} words = {total_words_needed} total words")
        print(f"[STORY GENERATOR] Setting max_tokens to {max_tokens}")

        # System message for complete story generation with structure
        system_message = f"""You are an expert children's story writer who creates engaging, well-structured stories.

YOUR TASK: Write a complete children's story of approximately {total_words_needed} words.

***** MANDATORY LANGUAGE REQUIREMENT *****
YOU MUST WRITE THE ENTIRE STORY IN {metadata.language.upper()}.
- ALL narrative text must be in {metadata.language}
- ALL dialogue must be in {metadata.language}
- ALL descriptions must be in {metadata.language}
- Do NOT mix languages. Do NOT write in English if the language is not English.
- If the language is Spanish, write EVERYTHING in Spanish.
- If the language is French, write EVERYTHING in French.
- This is a strict requirement with NO exceptions.
******************************************

STORY STRUCTURE:
- Plan a clear three-act structure before writing
- Create a protagonist with a goal and an arc (they should change or learn something)
- Include key turning points: inciting incident, midpoint challenge, climax, resolution
- Build appropriate tension and pacing for young readers

WRITING STYLE:
- Use {metadata.vocabulary_diversity} vocabulary for ages {metadata.age_group}
- Include vivid descriptions, dialogue, and character emotions
- Show character feelings through actions and reactions
- Write continuously as flowing prose - NO page markers or chapter breaks

CRITICAL REQUIREMENTS:
- Write the COMPLETE story from beginning to end IN {metadata.language.upper()} ONLY
- Do NOT stop mid-story or leave it incomplete
- Do NOT include "Page 1:", "Chapter 1:", or similar markers
- The story MUST have a satisfying conclusion
- Target approximately {total_words_needed} words total"""

        result = await self.ai_client.generate_text(
            prompt,
            temperature=0.8,
            max_tokens=max_tokens,
            system_message=system_message
        )
        story_text = result['text']
        self._last_cost = result.get('cost', 0.0)

        # Debug: Show generated story text
        print("="*80)
        print("[STORY GENERATOR] AI Generated Story Text:")
        print("="*80)
        print(f"Length: {len(story_text)} characters")
        word_count = len(story_text.split())
        print(f"Word count: {word_count} words (target: {total_words_needed})")
        print(f"First 500 chars: {story_text[:500]}")
        print("="*80)

        # Step 3: Split continuous story into pages at sentence boundaries
        pages = self._split_into_pages(story_text, metadata.num_pages, words_per_page)

        # Debug: Show splitting results
        print(f"[STORY GENERATOR] Split story into {len(pages)} pages")
        if len(pages) == 0:
            print("[STORY GENERATOR] WARNING: No pages were created!")
            print("[STORY GENERATOR] Story text may have been empty or splitting failed")
        for i, page in enumerate(pages[:3]):
            word_count = len(page.text.split())
            print(f"[STORY GENERATOR] Page {page.page_number}: {word_count} words - {page.text[:80]}...")

        # Characters are now extracted on-demand via the Characters tab
        # Return story without characters - they'll be added later when user requests

        # Create and return complete story
        return Story(
            id=str(uuid.uuid4()),
            metadata=metadata,
            pages=pages,
            characters=[]
        )

    def _split_into_pages(
        self,
        story_text: str,
        num_pages: int,
        words_per_page: int
    ) -> List[StoryPage]:
        """
        Split continuous story text into pages at sentence boundaries.

        Prioritizes not breaking sentences over exact word counts.
        Each page will end at a sentence boundary (., !, ?) and the
        word count may vary slightly between pages to achieve this.
        Preserves paragraph breaks within pages.

        Args:
            story_text: Continuous story text from AI
            num_pages: Target number of pages
            words_per_page: Target words per page

        Returns:
            List of StoryPage objects
        """
        pages = []

        # Clean up the story text - remove any page markers if AI included them
        # despite our instructions
        clean_text = re.sub(r'(?:Page|Página|Chapter|Capítulo)\s+\d+:?\s*', '', story_text, flags=re.IGNORECASE)
        clean_text = clean_text.strip()

        if not clean_text:
            print("[SPLIT PAGES] WARNING: Story text is empty after cleaning")
            return pages

        # Split into paragraphs first (preserve paragraph structure)
        # Paragraphs are separated by double newlines or multiple newlines
        paragraphs = re.split(r'\n\s*\n', clean_text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # Now split each paragraph into sentences, keeping track of paragraph boundaries
        # Each element is a tuple: (sentence_text, is_paragraph_end)
        sentence_units = []
        sentence_pattern = r'([^.!?]*[.!?]+)'

        for para in paragraphs:
            # Split paragraph into sentences
            para_sentences = re.findall(sentence_pattern, para)

            if not para_sentences:
                # No sentence endings found in this paragraph, treat whole paragraph as one unit
                para_sentences = [para]

            # Clean up sentences in this paragraph
            para_sentences = [s.strip() for s in para_sentences if s.strip()]

            # Add sentences, marking the last one as paragraph end
            for i, sentence in enumerate(para_sentences):
                is_para_end = (i == len(para_sentences) - 1)
                sentence_units.append((sentence, is_para_end))

        if not sentence_units:
            print("[SPLIT PAGES] WARNING: No sentences found after parsing")
            return pages

        total_words = sum(len(s[0].split()) for s in sentence_units)
        print(f"[SPLIT PAGES] Total words: {total_words}, sentences: {len(sentence_units)}, paragraphs: {len(paragraphs)}, target pages: {num_pages}")

        # Calculate ideal words per page based on actual content
        ideal_words_per_page = max(1, total_words // num_pages)
        print(f"[SPLIT PAGES] Ideal words per page: {ideal_words_per_page}")

        current_page_units = []  # List of (sentence, is_para_end) tuples
        current_word_count = 0
        page_number = 1

        for idx, (sentence, is_para_end) in enumerate(sentence_units):
            sentence_words = len(sentence.split())
            current_page_units.append((sentence, is_para_end))
            current_word_count += sentence_words

            # Check if we should start a new page
            pages_remaining = num_pages - page_number
            sentences_remaining = len(sentence_units) - idx - 1

            should_break = False

            if pages_remaining > 0 and sentences_remaining > 0:
                # We need more pages and have more content
                if current_word_count >= ideal_words_per_page:
                    should_break = True
                # Also break if we're way over (150% of ideal) to prevent huge pages
                elif current_word_count >= ideal_words_per_page * 1.5:
                    should_break = True

            if should_break:
                # Create page with accumulated sentences, preserving paragraph breaks
                page_text = self._join_sentences_with_paragraphs(current_page_units)
                pages.append(StoryPage(
                    page_number=page_number,
                    text=page_text
                ))
                print(f"[SPLIT PAGES] Page {page_number}: {current_word_count} words")

                # Reset for next page
                page_number += 1
                current_page_units = []
                current_word_count = 0

                # Recalculate ideal words for remaining pages
                remaining_words = sum(len(s[0].split()) for s in sentence_units[idx+1:])
                if pages_remaining > 0:
                    ideal_words_per_page = max(1, remaining_words // pages_remaining)

        # Don't forget the last page with remaining content
        if current_page_units:
            page_text = self._join_sentences_with_paragraphs(current_page_units)
            pages.append(StoryPage(
                page_number=page_number,
                text=page_text
            ))
            print(f"[SPLIT PAGES] Page {page_number}: {current_word_count} words (final page)")

        print(f"[SPLIT PAGES] Created {len(pages)} pages total")

        # Log word distribution
        for page in pages:
            word_count = len(page.text.split())
            print(f"[SPLIT PAGES] Page {page.page_number}: {word_count} words")

        return pages

    def _join_sentences_with_paragraphs(
        self,
        sentence_units: List[Tuple[str, bool]]
    ) -> str:
        """
        Join sentences back together, preserving paragraph breaks.

        Args:
            sentence_units: List of (sentence_text, is_paragraph_end) tuples

        Returns:
            Joined text with paragraph breaks preserved
        """
        if not sentence_units:
            return ""

        result_parts = []
        current_paragraph = []

        for sentence, is_para_end in sentence_units:
            current_paragraph.append(sentence)

            if is_para_end:
                # End of paragraph - join sentences with spaces and add to result
                result_parts.append(' '.join(current_paragraph))
                current_paragraph = []

        # Handle any remaining sentences (shouldn't happen if data is well-formed)
        if current_paragraph:
            result_parts.append(' '.join(current_paragraph))

        # Join paragraphs with double newlines
        return '\n\n'.join(result_parts).strip()

    async def _extract_and_profile_characters(
        self,
        pages: List[StoryPage],
        full_story_text: str
    ) -> List[CharacterProfile]:
        """
        Extract characters and create detailed profiles.

        Args:
            pages: Story pages to extract characters from
            full_story_text: Full story text for context

        Returns:
            List of CharacterProfile objects with detailed information
        """
        profiles = []

        if not pages:
            return profiles

        try:
            # Extract basic character information
            print("[STORY GENERATOR] Starting character extraction...")
            characters = await self.character_extractor.extract_characters(pages)
            print(f"[STORY GENERATOR] Extracted {len(characters)} basic characters")

            # Create detailed profile for each character
            for character in characters:
                try:
                    print(f"[STORY GENERATOR] Creating profile for: {character.name}")
                    profile = await self.character_extractor.create_character_profile(
                        character,
                        story_context=full_story_text
                    )
                    profiles.append(profile)
                    print(f"[STORY GENERATOR] Profile created for: {profile.name} ({profile.species})")
                except Exception as e:
                    # If profile creation fails, skip this character
                    # but continue with others
                    print(f"[STORY GENERATOR] Failed to create profile for {character.name}: {e}")
                    continue

        except Exception as e:
            # If character extraction fails completely, return empty list
            # Story can still be valid without character information
            print(f"[STORY GENERATOR] Character extraction failed completely: {e}")
            import traceback
            traceback.print_exc()
            pass

        return profiles

    async def extract_characters_from_story(
        self,
        pages: List[StoryPage],
        full_story_text: str
    ) -> List[CharacterProfile]:
        """
        Public method to extract characters from an existing story on demand.

        This is called from the Characters tab when user clicks "Identify Characters".

        Args:
            pages: Story pages to extract characters from
            full_story_text: Full story text for context

        Returns:
            List of CharacterProfile objects with detailed information
        """
        return await self._extract_and_profile_characters(pages, full_story_text)
