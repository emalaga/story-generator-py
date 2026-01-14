"""
Prompt Routes for REST API.

Handles endpoints for generating image prompts with character consistency.
"""

import asyncio
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest

# Create blueprint
prompt_bp = Blueprint('prompts', __name__)


def run_async(coroutine):
    """Helper to run async functions in Flask routes."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


@prompt_bp.route('/image', methods=['POST'])
def generate_image_prompt():
    """
    POST /api/prompts/image - Generate an image prompt with character consistency

    Request body:
    {
        "scene_description": str (required),
        "character_profiles": list (optional),
        "art_style": str (optional)
    }

    Returns:
        200: Prompt generated successfully
        400: Invalid request
        500: Server error
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        try:
            data = request.get_json()
        except BadRequest:
            return jsonify({'error': 'Invalid JSON'}), 400

        # Validate required fields
        if 'scene_description' not in data:
            return jsonify({'error': 'Missing required field: scene_description'}), 400

        scene_description = data['scene_description']
        character_profiles = data.get('character_profiles', [])
        art_style = data.get('art_style', 'cartoon')

        # Get prompt builder from app
        prompt_builder = current_app.config.get('PROMPT_BUILDER')
        if not prompt_builder:
            # Fallback: create one if not in config
            from src.domain.prompt_builder import PromptBuilder
            prompt_builder = PromptBuilder()

        # Convert character dicts to CharacterProfile objects if needed
        from src.models.character import CharacterProfile
        character_objects = []
        for char_data in character_profiles:
            if isinstance(char_data, dict):
                character_objects.append(CharacterProfile(
                    name=char_data.get('name', ''),
                    species=char_data.get('species'),
                    physical_description=char_data.get('physical_description'),
                    clothing=char_data.get('clothing'),
                    distinctive_features=char_data.get('distinctive_features'),
                    personality_traits=char_data.get('personality_traits')
                ))
            else:
                character_objects.append(char_data)

        # Log for debugging
        current_app.logger.info(f"Generating prompt with {len(character_objects)} characters")
        for char in character_objects:
            current_app.logger.info(f"  Character: {char.name}, Species: {char.species}, Desc: {char.physical_description[:50] if char.physical_description else 'None'}")

        # Use AI to create a concise scene summary
        # Pass character profiles so AI knows not to make assumptions
        current_app.logger.info(f"Original scene text ({len(scene_description)} chars): {scene_description[:100]}...")
        scene_summary = run_async(prompt_builder.summarize_scene(
            scene_description,
            character_profiles=character_objects
        ))
        current_app.logger.info(f"AI scene summary ({len(scene_summary)} chars): {scene_summary}")

        # Generate the prompt with the AI-summarized scene
        prompt = prompt_builder.build_image_prompt(
            scene_summary,
            character_objects,
            art_style
        )

        current_app.logger.info(f"Generated prompt ({len(prompt)} chars): {prompt[:200]}...")

        return jsonify({'prompt': prompt}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating image prompt: {e}")
        return jsonify({'error': f'Failed to generate prompt: {str(e)}'}), 500
