"""
Visual Consistency Routes for REST API.

Handles endpoints for art bible and character reference generation,
enabling visual consistency across story illustrations.
"""

import asyncio
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest

from src.models.character import CharacterProfile

# Create blueprint
visual_bp = Blueprint('visual_consistency', __name__)


def run_async(coroutine):
    """Helper to run async functions in Flask routes."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


@visual_bp.route('/art-bible/generate-prompt', methods=['POST'])
def generate_art_bible_prompt():
    """
    POST /api/visual-consistency/art-bible/generate-prompt

    Generate a prompt for creating an art bible reference image.

    Request body:
    {
        "art_style": str (required),
        "genre": str (optional),
        "story_title": str (optional),
        "additional_notes": str (optional)
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
        if 'art_style' not in data:
            return jsonify({'error': 'Missing required field: art_style'}), 400

        art_style = data['art_style']
        genre = data.get('genre')
        story_title = data.get('story_title')
        additional_notes = data.get('additional_notes')

        # Get prompt builder
        prompt_builder = current_app.config.get('PROMPT_BUILDER')
        if not prompt_builder:
            from src.domain.prompt_builder import PromptBuilder
            prompt_builder = PromptBuilder()

        # Create art bible with generated prompt
        art_bible = prompt_builder.create_art_bible(
            art_style=art_style,
            genre=genre,
            story_title=story_title,
            additional_notes=additional_notes
        )

        return jsonify({
            'prompt': art_bible.prompt,
            'art_style': art_bible.art_style,
            'style_notes': art_bible.style_notes
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating art bible prompt: {e}")
        return jsonify({'error': f'Failed to generate prompt: {str(e)}'}), 500


@visual_bp.route('/art-bible/generate-image', methods=['POST'])
def generate_art_bible_image():
    """
    POST /api/visual-consistency/art-bible/generate-image

    Generate an art bible reference image using the provided prompt.

    Request body:
    {
        "prompt": str (required),
        "art_style": str (required)
    }

    Returns:
        200: Image generated successfully
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
        if 'prompt' not in data:
            return jsonify({'error': 'Missing required field: prompt'}), 400
        if 'art_style' not in data:
            return jsonify({'error': 'Missing required field: art_style'}), 400

        prompt = data['prompt']
        art_style = data['art_style']

        # Get image client
        image_client = current_app.config['SERVICES']['image_client']

        # Generate art bible image
        image_url = run_async(image_client.generate_image(
            prompt=prompt,
            size='1792x1024',  # Wider format for art bible/style guide
            quality='hd'  # Higher quality for reference
        ))

        return jsonify({
            'image_url': image_url,
            'prompt': prompt,
            'art_style': art_style
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating art bible image: {e}")
        return jsonify({'error': f'Failed to generate image: {str(e)}'}), 500


@visual_bp.route('/character-reference/generate-prompt', methods=['POST'])
def generate_character_reference_prompt():
    """
    POST /api/visual-consistency/character-reference/generate-prompt

    Generate a prompt for creating a character reference image.

    Request body:
    {
        "character": {
            "name": str,
            "species": str,
            "physical_description": str,
            "clothing": str (optional),
            "distinctive_features": str (optional),
            "personality_traits": str (optional)
        },
        "art_style": str (required),
        "include_turnaround": bool (optional, default: true)
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
        if 'character' not in data:
            return jsonify({'error': 'Missing required field: character'}), 400
        if 'art_style' not in data:
            return jsonify({'error': 'Missing required field: art_style'}), 400

        character_data = data['character']
        art_style = data['art_style']
        include_turnaround = data.get('include_turnaround', True)

        # Create CharacterProfile object
        character = CharacterProfile(
            name=character_data.get('name', ''),
            species=character_data.get('species'),
            physical_description=character_data.get('physical_description'),
            clothing=character_data.get('clothing'),
            distinctive_features=character_data.get('distinctive_features'),
            personality_traits=character_data.get('personality_traits')
        )

        # Get prompt builder
        prompt_builder = current_app.config.get('PROMPT_BUILDER')
        if not prompt_builder:
            from src.domain.prompt_builder import PromptBuilder
            prompt_builder = PromptBuilder()

        # Create character reference with generated prompt
        char_ref = prompt_builder.create_character_reference(
            character=character,
            art_style=art_style,
            include_turnaround=include_turnaround
        )

        return jsonify({
            'character_name': char_ref.character_name,
            'prompt': char_ref.prompt,
            'species': char_ref.species,
            'physical_description': char_ref.physical_description,
            'clothing': char_ref.clothing,
            'distinctive_features': char_ref.distinctive_features
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating character reference prompt: {e}")
        return jsonify({'error': f'Failed to generate prompt: {str(e)}'}), 500


@visual_bp.route('/character-reference/generate-image', methods=['POST'])
def generate_character_reference_image():
    """
    POST /api/visual-consistency/character-reference/generate-image

    Generate a character reference image using the provided prompt.

    Request body:
    {
        "prompt": str (required),
        "character_name": str (required),
        "include_turnaround": bool (optional, default: true),
        "art_bible_url": str (optional) - URL to art bible image for style consistency
    }

    Returns:
        200: Image generated successfully
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
        if 'prompt' not in data:
            return jsonify({'error': 'Missing required field: prompt'}), 400
        if 'character_name' not in data:
            return jsonify({'error': 'Missing required field: character_name'}), 400

        prompt = data['prompt']
        character_name = data['character_name']
        include_turnaround = data.get('include_turnaround', True)
        art_bible_url = data.get('art_bible_url')  # Optional art bible reference

        # Get image client
        image_client = current_app.config['SERVICES']['image_client']

        # Generate character reference image
        # Use square format for single portrait or wide format for turnaround
        size = '1792x1024' if include_turnaround else '1024x1024'

        # If art bible URL is provided, use it as a reference for consistency
        if art_bible_url:
            image_url = run_async(image_client.generate_image_with_references(
                prompt=prompt,
                reference_image_urls=[art_bible_url],
                size=size,
                quality='hd'  # Higher quality for reference
            ))
        else:
            image_url = run_async(image_client.generate_image(
                prompt=prompt,
                size=size,
                quality='hd'  # Higher quality for reference
            ))

        return jsonify({
            'image_url': image_url,
            'character_name': character_name,
            'prompt': prompt
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating character reference image: {e}")
        return jsonify({'error': f'Failed to generate image: {str(e)}'}), 500
