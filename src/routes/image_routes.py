"""
Image Routes for REST API.

Handles endpoints for image generation and saving.
"""

import asyncio
import base64
import httpx
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app, send_from_directory
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

    Uses conversation session for visual consistency with art bible and characters.

    Request body:
    {
        "scene_description": str (required),
        "art_style": str (optional),
        "characters": List[dict] (optional),
        "session_id": str (optional) - existing session ID for continuation
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
        if 'scene_description' not in data:
            return jsonify({'error': 'Missing required field: scene_description'}), 400

        # Get image client and generator service
        image_client = current_app.config['SERVICES']['image_client']
        image_generator = current_app.config['SERVICES']['image_generator']

        # Get parameters
        scene_description = data['scene_description']
        art_style = data.get('art_style', 'cartoon')
        session_id = data.get('session_id')
        story_title = data.get('story_title', '')
        # Accept either 'characters' or 'character_profiles'
        characters_data = data.get('character_profiles', data.get('characters', []))

        # Parse character profiles
        from src.models.character import CharacterProfile
        from src.models.story import Story, StoryMetadata, StoryPage
        from src.models.art_bible import ArtBible, CharacterReference

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

        # Parse art bible if present (for session recovery context)
        art_bible = None
        if 'art_bible' in data and data['art_bible']:
            art_bible_data = data['art_bible']
            art_bible = ArtBible(
                prompt=art_bible_data.get('prompt', ''),
                image_url=art_bible_data.get('image_url'),
                art_style=art_bible_data.get('art_style', art_style),
                style_notes=art_bible_data.get('style_notes'),
                color_palette=art_bible_data.get('color_palette'),
                lighting_style=art_bible_data.get('lighting_style'),
                brush_technique=art_bible_data.get('brush_technique')
            )

        # Parse character references if present (for session recovery context)
        character_references = []
        if 'character_references' in data and data['character_references']:
            for char_ref_data in data['character_references']:
                char_ref = CharacterReference(
                    character_name=char_ref_data.get('character_name', ''),
                    prompt=char_ref_data.get('prompt', ''),
                    image_url=char_ref_data.get('image_url'),
                    species=char_ref_data.get('species'),
                    physical_description=char_ref_data.get('physical_description'),
                    clothing=char_ref_data.get('clothing'),
                    distinctive_features=char_ref_data.get('distinctive_features')
                )
                character_references.append(char_ref)

        # Create a Story object for session management
        story = Story(
            id=story_id,
            metadata=StoryMetadata(
                title=story_title,
                language='en',
                complexity='simple',
                vocabulary_diversity='simple',
                age_group='4-8',
                num_pages=1,
                art_style=art_style
            ),
            pages=[StoryPage(page_number=page_num, text=scene_description)],
            characters=character_profiles,
            art_bible=art_bible,
            character_references=character_references if character_references else None,
            image_session_id=session_id
        )

        # If we have a session ID, load it into the client
        if session_id:
            image_client.set_session_id(story_id, session_id)

        # Log for debugging
        current_app.logger.info(f"Generating image for page {page_num} with {len(character_profiles)} characters")
        current_app.logger.info(f"  Session ID: {session_id or 'None (will create new)'}")

        # Check if a custom prompt was provided (user edited the prompt)
        custom_prompt = data.get('custom_prompt')

        if custom_prompt:
            # Use the custom prompt directly without regenerating
            current_app.logger.info(f"  Using custom prompt (length: {len(custom_prompt)})")
            import sys
            sys.stdout.flush()

            # Ensure session exists
            print(f"[DEBUG] About to call ensure_session for story_id={story_id}", flush=True)
            current_app.logger.info(f"  Calling ensure_session...")
            sys.stdout.flush()
            try:
                print(f"[DEBUG] Inside try block, calling run_async(ensure_session)", flush=True)
                run_async(image_generator.ensure_session(story))
                print(f"[DEBUG] ensure_session returned, session_id={story.image_session_id}", flush=True)
                current_app.logger.info(f"  ensure_session completed, session_id: {story.image_session_id}")
            except Exception as e:
                print(f"[DEBUG] ensure_session EXCEPTION: {type(e).__name__}: {e}", flush=True)
                current_app.logger.error(f"  ensure_session FAILED: {e}", exc_info=True)
                raise

            # Generate image directly with custom prompt
            print(f"[DEBUG] About to call generate_image", flush=True)
            current_app.logger.info(f"  Calling generate_image with custom prompt...")
            try:
                print(f"[DEBUG] Inside try block, calling run_async(generate_image)", flush=True)
                image_url = run_async(image_client.generate_image(
                    story_id,
                    custom_prompt,
                    size='1024x1024',
                    quality='high'
                ))
                print(f"[DEBUG] generate_image returned, URL length={len(image_url) if image_url else 0}", flush=True)
                current_app.logger.info(f"  generate_image completed, URL length: {len(image_url) if image_url else 0}")
            except Exception as e:
                print(f"[DEBUG] generate_image EXCEPTION: {type(e).__name__}: {e}", flush=True)
                current_app.logger.error(f"  generate_image FAILED: {e}", exc_info=True)
                raise

            # Update session ID in story
            story.image_session_id = image_client.get_session_id(story_id)
        else:
            # Generate image using conversation session (builds prompt automatically)
            current_app.logger.info(f"  Generating with automatic prompt building")
            image_url = run_async(image_generator.generate_image_for_page(
                story,
                scene_description,
                character_profiles,
                art_style
            ))

        # Get updated session ID
        new_session_id = image_client.get_session_id(story_id)

        # Log what we're returning
        current_app.logger.info(f"  Image URL returned: {image_url[:100] if image_url else 'None'}...")
        current_app.logger.info(f"  New session ID: {new_session_id}")

        return jsonify({
            'image_url': image_url,
            'page_number': page_num,
            'session_id': new_session_id  # Return session ID for persistence
        }), 200

    except ValueError as e:
        current_app.logger.error(f"ValueError generating image: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating image: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@image_bp.route('/save', methods=['POST'])
def save_image():
    """
    POST /api/images/save - Download and save an image locally

    Request body:
    {
        "image_url": str (required),
        "project_id": str (required),
        "image_type": str (required) - "art_bible", "character", or "page",
        "filename": str (required) - filename to save as
    }

    Returns:
        200: Image saved successfully with local path
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
        required_fields = ['image_url', 'project_id', 'image_type', 'filename']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        image_url = data['image_url']
        project_id = data['project_id']
        image_type = data['image_type']
        filename = data['filename']

        # Validate image_type
        valid_types = ['art_bible', 'character', 'page']
        if image_type not in valid_types:
            return jsonify({'error': f'Invalid image_type. Must be one of: {", ".join(valid_types)}'}), 400

        # Get project repository to access image directories
        project_repo = current_app.config['REPOSITORIES']['project']

        # Get the project's images directory
        project_images_dir = project_repo.get_project_images_dir(project_id)

        # Determine subdirectory based on image type
        if image_type == 'art_bible':
            save_dir = project_images_dir / 'art_bible'
        elif image_type == 'character':
            save_dir = project_images_dir / 'characters'
        else:  # page
            save_dir = project_images_dir / 'pages'

        # Full path for the saved image
        save_path = save_dir / filename

        # Check if it's a base64 data URL or a regular URL
        if image_url.startswith('data:'):
            # Parse base64 data URL: data:image/png;base64,<data>
            try:
                # Split header from data
                header, encoded_data = image_url.split(',', 1)
                image_data = base64.b64decode(encoded_data)
            except Exception as e:
                return jsonify({'error': f'Failed to decode base64 image: {str(e)}'}), 400
        else:
            # Download the image from URL
            async def download_image():
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(image_url)
                    if response.status_code != 200:
                        raise Exception(f'Failed to download image: HTTP {response.status_code}')
                    return response.content

            image_data = run_async(download_image())

        with open(save_path, 'wb') as f:
            f.write(image_data)

        # Return the relative path from the storage directory
        # This will be used for loading images later
        # Map image_type to the actual directory name
        type_to_dir = {
            'art_bible': 'art_bible',
            'character': 'characters',
            'page': 'pages'
        }
        relative_path = f'images/{project_id}/{type_to_dir[image_type]}/{filename}'

        return jsonify({
            'success': True,
            'local_path': relative_path,
            'saved_to': str(save_path)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error saving image: {e}")
        return jsonify({'error': f'Failed to save image: {str(e)}'}), 500


@image_bp.route('/<path:filepath>', methods=['GET'])
def serve_saved_image(filepath):
    """
    GET /api/images/<filepath>

    Serve a saved image from the local storage.
    Filepath should be relative to the images storage directory.
    Example: /api/images/project-id/pages/page_1.png

    Returns:
        200: Image file
        404: Image not found
    """
    try:
        project_repo = current_app.config['REPOSITORIES']['project']
        images_dir = project_repo.images_dir

        # Security check: ensure the path doesn't escape the images directory
        requested_path = (images_dir / filepath).resolve()
        if not str(requested_path).startswith(str(images_dir.resolve())):
            return jsonify({'error': 'Invalid path'}), 403

        # Get the directory and filename
        file_path = Path(filepath)
        directory = images_dir / file_path.parent
        filename = file_path.name

        return send_from_directory(directory, filename)

    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error serving image: {e}")
        return jsonify({'error': f'Failed to serve image: {str(e)}'}), 500


@image_bp.route('/delete', methods=['POST'])
def delete_image():
    """
    POST /api/images/delete - Delete a saved image

    Request body:
    {
        "image_path": str (required) - relative path like "images/project-id/type/filename.png"
    }

    Returns:
        200: Image deleted successfully
        400: Invalid request
        404: Image not found
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
        if 'image_path' not in data:
            return jsonify({'error': 'Missing required field: image_path'}), 400

        image_path = data['image_path']

        # Get project repository to access image directories
        project_repo = current_app.config['REPOSITORIES']['project']
        images_dir = project_repo.images_dir

        # Construct full path
        # image_path format: "images/project-id/type/filename.png"
        # We need to remove the leading "images/" since images_dir is already the images directory
        if image_path.startswith('images/'):
            relative_path = image_path[7:]  # Remove "images/" prefix
        else:
            relative_path = image_path

        full_path = images_dir / relative_path

        # Security check: ensure the path doesn't escape the images directory
        resolved_path = full_path.resolve()
        if not str(resolved_path).startswith(str(images_dir.resolve())):
            return jsonify({'error': 'Invalid path'}), 403

        # Check if file exists
        if not full_path.exists():
            return jsonify({'error': 'Image not found'}), 404

        # Delete the file
        full_path.unlink()

        current_app.logger.info(f"Deleted image: {image_path}")

        return jsonify({
            'success': True,
            'deleted_path': image_path
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error deleting image: {e}")
        return jsonify({'error': f'Failed to delete image: {str(e)}'}), 500
