"""
Prompt Builder for creating AI prompts for story and image generation.

This module builds prompts for AI text generation (stories) and image generation,
incorporating story parameters, character profiles, and formatting requirements.
"""

from typing import List, Optional

from src.models.character import CharacterProfile
from src.models.story import StoryMetadata


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

        # Number of pages
        prompt_parts.append(
            f"The story should have exactly {metadata.num_pages} pages, "
            f"with each page containing 2-4 sentences appropriate for the age group."
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
            # Fallback: simple truncation if no AI client available
            return scene_text[:200]

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

IMPORTANT:
- Use ONLY the character information provided - do not make assumptions about gender, appearance, or other details
- Refer to characters by their exact names and species
- Do not add details not present in the story text

Ignore:
- Narrative commentary
- Internal thoughts
- Abstract concepts that can't be visualized

Return ONLY a concise scene description (30-50 words) that an illustrator could draw."""

        prompt = f"""Analyze this children's story page and describe the main scene to illustrate:{character_context}

Story page text:
{scene_text}

Return only the scene description, nothing else."""

        try:
            summary = await self.ai_client.generate_text(
                prompt,
                system_message=system_message,
                temperature=0.3
            )
            return summary.strip()
        except Exception:
            # Fallback to truncation if AI fails
            return scene_text[:200]

    def build_image_prompt(
        self,
        scene_description: str,
        character_profiles: List[CharacterProfile],
        art_style: str
    ) -> str:
        """
        Build a prompt for AI image generation.

        Creates a concise prompt optimized for GPT-Image and DALL-E, incorporating
        character profiles and scene details to ensure character consistency across
        all illustrations.

        Args:
            scene_description: Description of the scene to illustrate
            character_profiles: List of character profiles for consistency
            art_style: Artistic style (e.g., "cartoon", "watercolor", "realistic")

        Returns:
            Formatted prompt string for AI image generation (optimized for GPT-Image/DALL-E)
        """
        prompt_parts = []

        # Art style - keep it simple and clear
        prompt_parts.append(f"A {art_style} style children's book illustration showing")

        # Add main characters FIRST for consistency (limit to 2 most relevant)
        if character_profiles:
            character_descriptions = []
            # Only include the first 2 characters to keep prompt concise
            for profile in character_profiles[:2]:
                if profile.name and profile.species and profile.physical_description:
                    # Create detailed character description
                    char_desc = f"{profile.name} (a {profile.species}"
                    # Add key physical features (use smart truncation to avoid cutting words)
                    phys_desc = self._smart_truncate(profile.physical_description, 100)
                    if phys_desc:
                        char_desc += f", {phys_desc}"
                    # Add distinctive features if specified (important for consistency)
                    if profile.distinctive_features:
                        distinctive_desc = self._smart_truncate(profile.distinctive_features, 60)
                        char_desc += f", {distinctive_desc}"
                    # Add clothing if specified
                    if profile.clothing:
                        clothing_desc = self._smart_truncate(profile.clothing, 60)
                        char_desc += f", {clothing_desc}"
                    # Add personality traits if they affect appearance (e.g., "always smiling")
                    if profile.personality_traits:
                        personality_desc = self._smart_truncate(profile.personality_traits, 60)
                        char_desc += f", {personality_desc}"
                    char_desc += ")"
                    character_descriptions.append(char_desc)
                elif profile.species and profile.physical_description:
                    # Character without name but has species and description
                    phys_desc = self._smart_truncate(profile.physical_description, 100)
                    char_desc = f"a {profile.species}"
                    if phys_desc:
                        char_desc += f" ({phys_desc}"
                        # Add distinctive features if specified (important for consistency)
                        if profile.distinctive_features:
                            distinctive_desc = self._smart_truncate(profile.distinctive_features, 60)
                            char_desc += f", {distinctive_desc}"
                        # Add clothing if specified
                        if profile.clothing:
                            clothing_desc = self._smart_truncate(profile.clothing, 60)
                            char_desc += f", {clothing_desc}"
                        # Add personality traits if they affect appearance (e.g., "always smiling")
                        if profile.personality_traits:
                            personality_desc = self._smart_truncate(profile.personality_traits, 60)
                            char_desc += f", {personality_desc}"
                        char_desc += ")"
                    else:
                        char_desc += ""
                    character_descriptions.append(char_desc)

            if character_descriptions:
                prompt_parts.append(" and ".join(character_descriptions))

        # Scene description - extract key elements, limit to ~200 chars
        scene_summary = scene_description[:200] if len(scene_description) > 200 else scene_description

        # Add the scene action/setting
        prompt_parts.append(f"in this scene: {scene_summary}")

        # Simple quality instruction
        prompt_parts.append("Vibrant colors, child-friendly, professional children's book illustration style.")

        # Join with spaces and ensure under 1000 chars (well under the 4000 char limit)
        full_prompt = " ".join(prompt_parts)

        # Truncate if still too long (safety check)
        if len(full_prompt) > 1000:
            full_prompt = full_prompt[:997] + "..."

        return full_prompt
