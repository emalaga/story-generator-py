"""
Visual Consistency Routes for REST API.

Handles endpoints for art bible and character reference generation,
enabling visual consistency across story illustrations using conversation sessions.
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
    This starts or continues a conversation session for the story.

    Request body:
    {
        "prompt": str (required),
        "art_style": str (required),
        "story_id": str (required) - ID of the story for session tracking,
        "size": str (optional) - Image size (default: 1536x1024),
        "quality": str (optional) - Image quality/detail (default: low)
    }

    Returns:
        200: Image generated successfully with session_id
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
        if 'story_id' not in data:
            return jsonify({'error': 'Missing required field: story_id'}), 400

        prompt = data['prompt']
        art_style = data['art_style']
        story_id = data['story_id']
        story_title = data.get('story_title', '')
        # Get size and quality from request, with defaults
        size = data.get('size', '1536x1024')
        quality = data.get('quality', 'low')

        # Get image client
        image_client = current_app.config['SERVICES']['image_client']

        # Start or get session for this story
        session_id = image_client.get_session_id(story_id)
        if not session_id:
            # Start new session
            session_id = run_async(image_client.start_session(
                story_id=story_id,
                art_style=art_style,
                story_title=story_title
            ))

        # Generate art bible image within the conversation session
        current_app.logger.info(f"Generating art bible image for story {story_id} with size={size}, quality={quality}")
        image_url = run_async(image_client.generate_image(
            story_id=story_id,
            prompt=prompt,
            size=size,
            quality=quality
        ))

        # Get updated session ID
        session_id = image_client.get_session_id(story_id)
        current_app.logger.info(f"Art bible image generated: URL length={len(image_url) if image_url else 0}, session_id={session_id}")

        return jsonify({
            'image_url': image_url,
            'prompt': prompt,
            'art_style': art_style,
            'session_id': session_id  # Return session ID for persistence
        }), 200

    except ValueError as e:
        current_app.logger.error(f"ValueError generating art bible image: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating art bible image: {e}", exc_info=True)
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
    Uses the conversation session to maintain consistency with the art bible.

    Request body:
    {
        "prompt": str (required),
        "character_name": str (required),
        "story_id": str (required) - ID of the story for session tracking,
        "include_turnaround": bool (optional, default: true),
        "size": str (optional) - Image size (default: based on include_turnaround),
        "quality": str (optional) - Image quality/detail (default: low)
    }

    Returns:
        200: Image generated successfully with session_id
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
        if 'story_id' not in data:
            return jsonify({'error': 'Missing required field: story_id'}), 400

        prompt = data['prompt']
        character_name = data['character_name']
        story_id = data['story_id']
        include_turnaround = data.get('include_turnaround', True)
        # Get size and quality from request, with defaults
        # Default size depends on include_turnaround if not explicitly provided
        default_size = '1536x1024' if include_turnaround else '1024x1024'
        size = data.get('size', default_size)
        quality = data.get('quality', 'low')

        # Get image client
        image_client = current_app.config['SERVICES']['image_client']

        # Check if session exists, if not start one
        existing_session = image_client.get_session_id(story_id)
        current_app.logger.info(f"Generating character reference for {character_name}, story_id={story_id}")
        current_app.logger.info(f"Existing session: {existing_session}")

        if not existing_session:
            # Need to start a session first - get art_style from request or use default
            art_style = data.get('art_style', 'cartoon')
            current_app.logger.info(f"Starting new session with art_style={art_style}")
            run_async(image_client.start_session(
                story_id=story_id,
                art_style=art_style,
                story_title=data.get('story_title', '')
            ))

        # Generate character reference image using conversation session
        # The session already contains art bible context, so no need for reference images
        current_app.logger.info(f"Generating character image with size={size}, quality={quality}")
        image_url = run_async(image_client.generate_image(
            story_id=story_id,
            prompt=prompt,
            size=size,
            quality=quality
        ))

        # Get updated session ID
        session_id = image_client.get_session_id(story_id)
        current_app.logger.info(f"Character reference image generated: URL length={len(image_url) if image_url else 0}, session_id={session_id}")

        return jsonify({
            'image_url': image_url,
            'character_name': character_name,
            'prompt': prompt,
            'session_id': session_id  # Return session ID for persistence
        }), 200

    except ValueError as e:
        current_app.logger.error(f"ValueError generating character reference image: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating character reference image: {e}", exc_info=True)
        return jsonify({'error': f'Failed to generate image: {str(e)}'}), 500


@visual_bp.route('/session/start', methods=['POST'])
def start_session():
    """
    POST /api/visual-consistency/session/start

    Start a new conversation session for a story.

    Request body:
    {
        "story_id": str (required),
        "art_style": str (required),
        "story_title": str (optional)
    }

    Returns:
        200: Session started successfully
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
        if 'story_id' not in data:
            return jsonify({'error': 'Missing required field: story_id'}), 400
        if 'art_style' not in data:
            return jsonify({'error': 'Missing required field: art_style'}), 400

        story_id = data['story_id']
        art_style = data['art_style']
        story_title = data.get('story_title', '')

        # Get image client
        image_client = current_app.config['SERVICES']['image_client']

        # Clear any existing session
        image_client.clear_session(story_id)

        # Start new session
        session_id = run_async(image_client.start_session(
            story_id=story_id,
            art_style=art_style,
            story_title=story_title
        ))

        return jsonify({
            'session_id': session_id,
            'story_id': story_id
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error starting session: {e}")
        return jsonify({'error': f'Failed to start session: {str(e)}'}), 500


@visual_bp.route('/session/clear', methods=['POST'])
def clear_session():
    """
    POST /api/visual-consistency/session/clear

    Clear the conversation session for a story.

    Request body:
    {
        "story_id": str (required)
    }

    Returns:
        200: Session cleared successfully
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
        if 'story_id' not in data:
            return jsonify({'error': 'Missing required field: story_id'}), 400

        story_id = data['story_id']

        # Get image client
        image_client = current_app.config['SERVICES']['image_client']

        # Clear session
        image_client.clear_session(story_id)

        return jsonify({
            'message': 'Session cleared',
            'story_id': story_id
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error clearing session: {e}")
        return jsonify({'error': f'Failed to clear session: {str(e)}'}), 500
