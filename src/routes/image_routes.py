"""
Image Routes for REST API.

Handles endpoints for image generation.
"""

import asyncio
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest

# Create blueprint
image_bp = Blueprint('images', __name__)


def run_async(coroutine):
    """
    Helper to run async functions in Flask routes.

    Flask routes are synchronous but our services are async,
    so we need to run them in an event loop.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


@image_bp.route('/stories/<story_id>', methods=['POST'])
def generate_images_for_story(story_id):
    """
    POST /api/images/stories/:id - Generate images for all story pages

    Generates images for all pages in a story using the story's text,
    characters, and art style.

    Returns:
        200: Images generated successfully
        404: Story not found
        500: Server error
    """
    try:
        # This endpoint requires a full story repository to load stories
        # For now, guide users to use the project orchestrator which handles
        # the complete workflow: story generation → image generation → save project

        return jsonify({
            'error': 'Use POST /api/projects to create a complete project with images'
        }), 400

    except Exception as e:
        current_app.logger.error(f"Error generating images: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@image_bp.route('/stories/<story_id>/pages/<int:page_num>', methods=['POST'])
def generate_image_for_page(story_id, page_num):
    """
    POST /api/images/stories/:id/pages/:page_num - Generate image for single page

    Request body:
    {
        "scene_description": str (required),
        "art_style": str (optional),
        "characters": List[dict] (optional)
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
        if 'scene_description' not in data:
            return jsonify({'error': 'Missing required field: scene_description'}), 400

        # Get image generator service
        image_generator = current_app.config['SERVICES']['image_generator']

        # Get parameters
        scene_description = data['scene_description']
        art_style = data.get('art_style', 'cartoon')
        # Accept either 'characters' or 'character_profiles'
        characters_data = data.get('character_profiles', data.get('characters', []))

        # Parse character profiles
        from src.models.character import CharacterProfile
        character_profiles = []
        for char_data in characters_data:
            profile = CharacterProfile(
                name=char_data.get('name', ''),
                species=char_data.get('species'),
                physical_description=char_data.get('physical_description'),
                clothing=char_data.get('clothing'),
                distinctive_features=char_data.get('distinctive_features'),
                personality_traits=char_data.get('personality_traits')
            )
            character_profiles.append(profile)

        # Log for debugging
        current_app.logger.info(f"Generating image for page {page_num} with {len(character_profiles)} characters")
        for char in character_profiles:
            current_app.logger.info(f"  Character: {char.name}, Species: {char.species}, Desc: {char.physical_description[:50] if char.physical_description else 'None'}")

        # Generate image
        image_url = run_async(image_generator.generate_image_for_page(
            scene_description,
            character_profiles,
            art_style
        ))

        return jsonify({
            'image_url': image_url,
            'page_number': page_num
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating image: {e}")
        return jsonify({'error': 'Internal server error'}), 500
