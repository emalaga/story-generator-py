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
from typing import List, Optional

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
        # ~1.5 tokens per word + buffer for formatting (page headers, etc.)
        words_per_page = metadata.words_per_page or 50
        total_words_needed = metadata.num_pages * words_per_page
        # Add 50% buffer for formatting and safety
        max_tokens = int(total_words_needed * 1.5 * 1.5)
        # Ensure minimum of 1000 tokens and cap at 8000
        max_tokens = max(1000, min(max_tokens, 8000))

        print(f"[STORY GENERATOR] Requesting {metadata.num_pages} pages x {words_per_page} words = {total_words_needed} words")
        print(f"[STORY GENERATOR] Setting max_tokens to {max_tokens}")

        story_text = await self.ai_client.generate_text(
            prompt,
            temperature=0.8,
            max_tokens=max_tokens
        )

        # Debug: Show generated story text
        print("="*80)
        print("[STORY GENERATOR] AI Generated Story Text:")
        print("="*80)
        print(f"Length: {len(story_text)} characters")
        print(f"First 500 chars: {story_text[:500]}")
        print("="*80)

        # Step 3: Parse story into pages
        pages = self._parse_story_pages(story_text)

        # Debug: Show parsing results
        print(f"[STORY GENERATOR] Parsed {len(pages)} pages from story text")
        if len(pages) == 0:
            print("[STORY GENERATOR] WARNING: No pages were parsed!")
            print("[STORY GENERATOR] This usually means the AI response format doesn't match expected pattern")
        for i, page in enumerate(pages[:3]):
            print(f"[STORY GENERATOR] Page {page.page_number} preview: {page.text[:100]}...")

        # Characters are now extracted on-demand via the Characters tab
        # Return story without characters - they'll be added later when user requests

        # Create and return complete story
        return Story(
            id=str(uuid.uuid4()),
            metadata=metadata,
            pages=pages,
            characters=[]
        )

    def _parse_story_pages(self, story_text: str) -> List[StoryPage]:
        """
        Parse AI-generated story text into individual pages.

        Handles various formats in multiple languages:
        - "Page 1:\nText here\n\nPage 2:..." (English)
        - "Página 1:\nText here\n\nPágina 2:..." (Spanish)

        Args:
            story_text: Raw story text from AI

        Returns:
            List of StoryPage objects
        """
        pages = []

        print(f"[PARSE PAGES] Starting parse, story length: {len(story_text)}")

        # Split by "Page N:" or "Página N:" pattern
        # This regex matches both English "Page 1:" and Spanish "Página 1:"
        page_pattern = r'(?:Page|Página)\s+(\d+):\s*'
        page_splits = re.split(page_pattern, story_text, flags=re.IGNORECASE)

        print(f"[PARSE PAGES] Regex split resulted in {len(page_splits)} parts")
        print(f"[PARSE PAGES] First 3 parts: {page_splits[:3]}")

        # Remove any text before first page marker (if it exists and is not a number)
        if len(page_splits) > 0 and page_splits[0].strip():
            # Check if first element is NOT a digit (would be page number)
            if not page_splits[0].strip().isdigit():
                print(f"[PARSE PAGES] Removing intro text: {page_splits[0][:100]}...")
                page_splits = page_splits[1:]

        # Process pairs of (page_number, page_text)
        i = 0
        while i < len(page_splits) - 1:
            try:
                page_number = int(page_splits[i].strip())
                page_text = page_splits[i + 1].strip()

                print(f"[PARSE PAGES] Processing pair {i}: page_number={page_number}, text_length={len(page_text)}")

                if page_text:  # Only add non-empty pages
                    page = StoryPage(
                        page_number=page_number,
                        text=page_text
                    )
                    pages.append(page)
                    print(f"[PARSE PAGES] Added page {page_number}")
                else:
                    print(f"[PARSE PAGES] Skipped empty page {page_number}")
                i += 2
            except (ValueError, IndexError) as e:
                # Skip malformed page entries
                print(f"[PARSE PAGES] Error at index {i}: {e}, value: {page_splits[i] if i < len(page_splits) else 'OUT OF RANGE'}")
                i += 1
                continue

        print(f"[PARSE PAGES] Finished parsing, total pages: {len(pages)}")
        return pages

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
