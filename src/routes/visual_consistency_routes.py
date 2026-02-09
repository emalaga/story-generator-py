"""
Visual Consistency Routes for REST API.

Handles endpoints for art bible and character reference generation,
enabling visual consistency across story illustrations using conversation sessions.
"""

import asyncio
import base64
import time
import httpx
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest

from src.models.character import CharacterProfile
from src.utils.ai_logger import log_ai_call

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


async def save_image_to_disk(image_url: str, project_id: str, image_type: str, filename: str) -> str:
    """
    Save an image to disk and return the relative path.

    Args:
        image_url: The image URL or base64 data URL
        project_id: The project/story ID
        image_type: Type of image ('art_bible', 'character', 'page')
        filename: The filename to save as

    Returns:
        Relative path to the saved image (e.g., 'images/project-id/art_bible/filename.png')
    """
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
            header, encoded_data = image_url.split(',', 1)
            image_data = base64.b64decode(encoded_data)
        except Exception as e:
            raise ValueError(f'Failed to decode base64 image: {str(e)}')
    else:
        # Download the image from URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            if response.status_code != 200:
                raise Exception(f'Failed to download image: HTTP {response.status_code}')
            image_data = response.content

    # Save the image
    with open(save_path, 'wb') as f:
        f.write(image_data)

    # Map image_type to the actual directory name
    type_to_dir = {
        'art_bible': 'art_bible',
        'character': 'characters',
        'page': 'pages'
    }
    relative_path = f'images/{project_id}/{type_to_dir[image_type]}/{filename}'

    return relative_path


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
        "quality": str (optional) - Image quality/detail (default: low),
        "reference_images": list[str] (optional) - Paths to character reference images to use
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

        # Get character references if provided (includes character_name and image_path)
        character_references = data.get('character_references', [])
        reference_images_data = []

        # Load character reference images and convert to base64
        if character_references:
            import os
            # Get the base images directory from project repository
            project_repo = current_app.config['REPOSITORIES']['project']
            images_dir = project_repo.images_dir

            for char_ref in character_references:
                try:
                    image_path = char_ref.get('image_path', '')
                    character_name = char_ref.get('character_name', 'Unknown Character')

                    print(f"[DEBUG] Art Bible - Processing character reference: name='{character_name}', path='{image_path}'", flush=True)

                    if not image_path:
                        print(f"[DEBUG]   SKIPPING: empty image_path", flush=True)
                        continue

                    # Strip leading / and images/ prefix to get relative path within images_dir
                    relative_path = image_path.lstrip('/')
                    if relative_path.startswith('images/'):
                        relative_path = relative_path[7:]  # Remove "images/" prefix

                    # Construct full path using the images directory
                    full_path = str(images_dir / relative_path)
                    print(f"[DEBUG]   images_dir: {images_dir}", flush=True)
                    print(f"[DEBUG]   relative_path: {relative_path}", flush=True)
                    print(f"[DEBUG]   full_path: {full_path}", flush=True)
                    print(f"[DEBUG]   exists: {os.path.exists(full_path)}", flush=True)

                    if os.path.exists(full_path):
                        with open(full_path, 'rb') as f:
                            image_data = f.read()
                            image_size_kb = len(image_data) / 1024
                            print(f"[DEBUG]   Image loaded: {image_size_kb:.1f} KB", flush=True)

                            # Determine mime type
                            if full_path.lower().endswith('.png'):
                                mime_type = 'image/png'
                            elif full_path.lower().endswith('.gif'):
                                mime_type = 'image/gif'
                            elif full_path.lower().endswith('.webp'):
                                mime_type = 'image/webp'
                            else:
                                mime_type = 'image/jpeg'
                            base64_data = base64.b64encode(image_data).decode('utf-8')
                            print(f"[DEBUG]   Base64 length: {len(base64_data)} chars", flush=True)

                            reference_images_data.append({
                                'data': base64_data,
                                'mime_type': mime_type,
                                'character_name': character_name
                            })
                            current_app.logger.info(f"Loaded reference image for character '{character_name}': {image_path} ({image_size_kb:.1f} KB)")
                    else:
                        print(f"[DEBUG]   ERROR: File not found!", flush=True)
                        current_app.logger.warning(f"Reference image not found for '{character_name}': {image_path}")
                except Exception as e:
                    print(f"[DEBUG]   EXCEPTION: {type(e).__name__}: {e}", flush=True)
                    current_app.logger.warning(f"Failed to load reference image: {e}")

            print(f"[DEBUG] Total reference_images_data for art bible: {len(reference_images_data)}", flush=True)

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
        image_model = data.get('image_model', 'gpt-image-1')
        num_refs = len(reference_images_data)
        current_app.logger.info(f"Generating art bible image for story {story_id} with size={size}, quality={quality}, model={image_model}, character_references={num_refs}")
        result = run_async(image_client.generate_image_with_cost(
            story_id=story_id,
            prompt=prompt,
            size=size,
            quality=quality,
            model_name=image_model,
            reference_images=reference_images_data if reference_images_data else None
        ))
        image_url = result['image_url']
        image_cost = result.get('cost')

        # Get updated session ID
        session_id = image_client.get_session_id(story_id)
        current_app.logger.info(f"Art bible image generated: URL length={len(image_url) if image_url else 0}, session_id={session_id}, cost={image_cost}")

        # Log the AI call
        ref_image_paths = [ref.get('image_path', '') for ref in character_references] if character_references else []
        log_ai_call(
            call_type='art_bible',
            model=image_model,
            prompt=prompt,
            payload={'size': size, 'quality': quality, 'art_style': art_style},
            response_summary=f'Generated art bible image for "{story_title or story_id}"',
            reference_images=ref_image_paths,
            cost=image_cost,
            project_id=story_id
        )

        # Save the image to disk
        filename = f'art_bible_{int(time.time() * 1000)}.png'
        local_path = run_async(save_image_to_disk(image_url, story_id, 'art_bible', filename))
        current_app.logger.info(f"Art bible image saved to: {local_path}")

        # Update the project file with the new image path and metadata
        try:
            project_repo = current_app.config['REPOSITORIES']['project']
            project = project_repo.get(story_id)
            if project and project.story:
                if not project.story.art_bible:
                    from src.models.art_bible import ArtBible
                    project.story.art_bible = ArtBible(prompt=prompt, art_style=art_style)

                # Create version entry for the new image
                image_model = data.get('image_model', 'gpt-image-1')
                generated_at = datetime.now()
                version_entry = {
                    'path': local_path,
                    'model': image_model,
                    'generated_at': generated_at.isoformat(),
                    'resolution': size,
                    'cost': image_cost
                }

                # Initialize versions list if needed, preserving existing image
                if not project.story.art_bible.image_versions:
                    project.story.art_bible.image_versions = []
                    # Migrate existing image to versions list if present
                    if project.story.art_bible.local_image_path:
                        existing_version = {
                            'path': project.story.art_bible.local_image_path,
                            'model': project.story.art_bible.image_model,
                            'generated_at': project.story.art_bible.image_generated_at.isoformat() if project.story.art_bible.image_generated_at else None,
                            'resolution': project.story.art_bible.image_resolution,
                            'cost': project.story.art_bible.image_cost
                        }
                        project.story.art_bible.image_versions.append(existing_version)
                project.story.art_bible.image_versions.append(version_entry)

                # Set the new image as active
                project.story.art_bible.local_image_path = local_path
                project.story.art_bible.prompt = prompt
                # Save image generation metadata for active version
                project.story.art_bible.image_model = image_model
                project.story.art_bible.image_generated_at = generated_at
                project.story.art_bible.image_resolution = size
                project.story.art_bible.image_cost = image_cost
                project.story.image_session_id = session_id
                project_repo.save(project)
                current_app.logger.info(f"Project updated with art bible image path and metadata (version {len(project.story.art_bible.image_versions)})")
        except Exception as e:
            current_app.logger.warning(f"Failed to update project with art bible: {e}")

        # Mark context as initialized so Image Generation tab can reuse this session
        image_client.mark_context_initialized(story_id)
        current_app.logger.info(f"Context marked as initialized for story {story_id}")

        return jsonify({
            'local_image_path': local_path,
            'prompt': prompt,
            'art_style': art_style,
            'session_id': session_id,  # Return session ID for persistence
            'image_cost': image_cost  # Estimated cost in USD
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
        image_model = data.get('image_model', 'gpt-image-1')
        current_app.logger.info(f"Generating character image with size={size}, quality={quality}, model={image_model}")
        result = run_async(image_client.generate_image_with_cost(
            story_id=story_id,
            prompt=prompt,
            size=size,
            quality=quality,
            model_name=image_model
        ))
        image_url = result['image_url']
        image_cost = result.get('cost')

        # Get updated session ID
        session_id = image_client.get_session_id(story_id)
        current_app.logger.info(f"Character reference image generated: URL length={len(image_url) if image_url else 0}, session_id={session_id}, cost={image_cost}")

        # Log the AI call
        log_ai_call(
            call_type='character_image',
            model=image_model,
            prompt=prompt,
            payload={'size': size, 'quality': quality, 'character_name': character_name, 'include_turnaround': include_turnaround},
            response_summary=f'Generated character reference image for "{character_name}"',
            cost=image_cost,
            project_id=story_id
        )

        # Save the image to disk
        # Sanitize character name for filename
        safe_char_name = character_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f'character_{safe_char_name}_{int(time.time() * 1000)}.png'
        local_path = run_async(save_image_to_disk(image_url, story_id, 'character', filename))
        current_app.logger.info(f"Character reference image saved to: {local_path}")

        # Update the project file with the new image path and metadata
        try:
            project_repo = current_app.config['REPOSITORIES']['project']
            project = project_repo.get(story_id)
            if project and project.story:
                # Find or create the character reference
                if not project.story.character_references:
                    project.story.character_references = []

                # Create version entry for the new image
                image_model = data.get('image_model', 'gpt-image-1')
                generated_at = datetime.now()
                version_entry = {
                    'path': local_path,
                    'model': image_model,
                    'generated_at': generated_at.isoformat(),
                    'resolution': size,
                    'cost': image_cost
                }

                existing_ref = next(
                    (ref for ref in project.story.character_references if ref.character_name == character_name),
                    None
                )
                if existing_ref:
                    # Initialize versions list if needed, preserving existing image
                    if not existing_ref.image_versions:
                        existing_ref.image_versions = []
                        # Migrate existing image to versions list if present
                        if existing_ref.local_image_path:
                            existing_version = {
                                'path': existing_ref.local_image_path,
                                'model': existing_ref.image_model,
                                'generated_at': existing_ref.image_generated_at.isoformat() if existing_ref.image_generated_at else None,
                                'resolution': existing_ref.image_resolution,
                                'cost': existing_ref.image_cost
                            }
                            existing_ref.image_versions.append(existing_version)
                    existing_ref.image_versions.append(version_entry)

                    # Set the new image as active
                    existing_ref.local_image_path = local_path
                    existing_ref.prompt = prompt
                    # Save image generation metadata for active version
                    existing_ref.image_model = image_model
                    existing_ref.image_generated_at = generated_at
                    existing_ref.image_resolution = size
                    existing_ref.image_cost = image_cost
                    version_count = len(existing_ref.image_versions)
                else:
                    from src.models.art_bible import CharacterReference
                    new_ref = CharacterReference(
                        character_name=character_name,
                        prompt=prompt,
                        local_image_path=local_path,
                        image_model=image_model,
                        image_generated_at=generated_at,
                        image_resolution=size,
                        image_cost=image_cost,
                        image_versions=[version_entry]
                    )
                    project.story.character_references.append(new_ref)
                    version_count = 1

                project.story.image_session_id = session_id
                project_repo.save(project)
                current_app.logger.info(f"Project updated with character reference image path and metadata (version {version_count})")
        except Exception as e:
            current_app.logger.warning(f"Failed to update project with character reference: {e}")

        # Mark context as initialized so Image Generation tab can reuse this session
        image_client.mark_context_initialized(story_id)
        current_app.logger.info(f"Context marked as initialized for story {story_id}")

        return jsonify({
            'local_image_path': local_path,
            'character_name': character_name,
            'prompt': prompt,
            'session_id': session_id,  # Return session ID for persistence
            'image_cost': image_cost  # Estimated cost in USD
        }), 200

    except ValueError as e:
        current_app.logger.error(f"ValueError generating character reference image: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating character reference image: {e}", exc_info=True)
        return jsonify({'error': f'Failed to generate image: {str(e)}'}), 500


@visual_bp.route('/art-bible/upload', methods=['POST'])
def upload_art_bible():
    """
    POST /api/visual-consistency/art-bible/upload

    Upload a custom art bible reference image.

    Request: multipart/form-data
        - file: Image file (required)
        - story_id: str (required)
        - art_style: str (optional)

    Returns:
        200: Image uploaded successfully
        400: Invalid request
        500: Server error
    """
    try:
        # Validate file
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate story_id
        story_id = request.form.get('story_id')
        if not story_id:
            return jsonify({'error': 'Missing required field: story_id'}), 400

        art_style = request.form.get('art_style', 'custom')

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}), 400

        # Get project repository to access image directories
        project_repo = current_app.config['REPOSITORIES']['project']

        # Get the project's images directory
        project_images_dir = project_repo.get_project_images_dir(story_id)
        save_dir = project_images_dir / 'art_bible'

        # Generate filename with timestamp
        filename = f'art_bible_custom_{int(time.time() * 1000)}.{file_ext}'
        save_path = save_dir / filename

        # Save the file
        file.save(str(save_path))

        # Build relative path
        local_path = f'images/{story_id}/art_bible/{filename}'
        current_app.logger.info(f"Custom art bible image uploaded to: {local_path}")

        # Update the project file with the new image path
        try:
            project = project_repo.get(story_id)
            if project and project.story:
                if not project.story.art_bible:
                    from src.models.art_bible import ArtBible
                    project.story.art_bible = ArtBible(prompt='Custom uploaded image', art_style=art_style)

                # Create version entry for the uploaded image
                version_entry = {
                    'path': local_path,
                    'model': 'uploaded',
                    'generated_at': datetime.now().isoformat(),
                    'resolution': None,
                    'cost': None
                }

                # Initialize versions list if needed, preserving existing image
                if not project.story.art_bible.image_versions:
                    project.story.art_bible.image_versions = []
                    # Migrate existing image to versions list if present
                    if project.story.art_bible.local_image_path:
                        existing_version = {
                            'path': project.story.art_bible.local_image_path,
                            'model': project.story.art_bible.image_model,
                            'generated_at': project.story.art_bible.image_generated_at.isoformat() if project.story.art_bible.image_generated_at else None,
                            'resolution': project.story.art_bible.image_resolution,
                            'cost': project.story.art_bible.image_cost
                        }
                        project.story.art_bible.image_versions.append(existing_version)
                project.story.art_bible.image_versions.append(version_entry)

                # Set the uploaded image as active
                project.story.art_bible.local_image_path = local_path
                project.story.art_bible.art_style = art_style
                project_repo.save(project)
                current_app.logger.info(f"Project updated with custom art bible image path (version {len(project.story.art_bible.image_versions)})")
        except Exception as e:
            current_app.logger.warning(f"Failed to update project with art bible: {e}")

        return jsonify({
            'local_image_path': local_path,
            'art_style': art_style,
            'message': 'Art bible image uploaded successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error uploading art bible image: {e}", exc_info=True)
        return jsonify({'error': f'Failed to upload image: {str(e)}'}), 500


@visual_bp.route('/character-reference/upload', methods=['POST'])
def upload_character_reference():
    """
    POST /api/visual-consistency/character-reference/upload

    Upload a custom character reference image.

    Request: multipart/form-data
        - file: Image file (required)
        - story_id: str (required)
        - character_name: str (required)

    Returns:
        200: Image uploaded successfully
        400: Invalid request
        500: Server error
    """
    try:
        # Validate file
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate required fields
        story_id = request.form.get('story_id')
        if not story_id:
            return jsonify({'error': 'Missing required field: story_id'}), 400

        character_name = request.form.get('character_name')
        if not character_name:
            return jsonify({'error': 'Missing required field: character_name'}), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}), 400

        # Get project repository to access image directories
        project_repo = current_app.config['REPOSITORIES']['project']

        # Get the project's images directory
        project_images_dir = project_repo.get_project_images_dir(story_id)
        save_dir = project_images_dir / 'characters'

        # Sanitize character name for filename
        safe_char_name = character_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f'character_{safe_char_name}_custom_{int(time.time() * 1000)}.{file_ext}'
        save_path = save_dir / filename

        # Save the file
        file.save(str(save_path))

        # Build relative path
        local_path = f'images/{story_id}/characters/{filename}'
        current_app.logger.info(f"Custom character reference image uploaded to: {local_path}")

        # Update the project file with the new image path
        try:
            project = project_repo.get(story_id)
            if project and project.story:
                # Find or create the character reference
                if not project.story.character_references:
                    project.story.character_references = []

                # Create version entry for the uploaded image
                version_entry = {
                    'path': local_path,
                    'model': 'uploaded',
                    'generated_at': datetime.now().isoformat(),
                    'resolution': None,
                    'cost': None
                }

                existing_ref = next(
                    (ref for ref in project.story.character_references if ref.character_name == character_name),
                    None
                )
                if existing_ref:
                    # Initialize versions list if needed, preserving existing image
                    if not existing_ref.image_versions:
                        existing_ref.image_versions = []
                        # Migrate existing image to versions list if present
                        if existing_ref.local_image_path:
                            existing_version = {
                                'path': existing_ref.local_image_path,
                                'model': existing_ref.image_model,
                                'generated_at': existing_ref.image_generated_at.isoformat() if existing_ref.image_generated_at else None,
                                'resolution': existing_ref.image_resolution,
                                'cost': existing_ref.image_cost
                            }
                            existing_ref.image_versions.append(existing_version)
                    existing_ref.image_versions.append(version_entry)

                    # Set the uploaded image as active
                    existing_ref.local_image_path = local_path
                    existing_ref.prompt = 'Custom uploaded image'
                    version_count = len(existing_ref.image_versions)
                else:
                    from src.models.art_bible import CharacterReference
                    new_ref = CharacterReference(
                        character_name=character_name,
                        prompt='Custom uploaded image',
                        local_image_path=local_path,
                        image_versions=[version_entry]
                    )
                    project.story.character_references.append(new_ref)
                    version_count = 1

                project_repo.save(project)
                current_app.logger.info(f"Project updated with custom character reference image path (version {version_count})")
        except Exception as e:
            current_app.logger.warning(f"Failed to update project with character reference: {e}")

        return jsonify({
            'local_image_path': local_path,
            'character_name': character_name,
            'message': 'Character reference image uploaded successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error uploading character reference image: {e}", exc_info=True)
        return jsonify({'error': f'Failed to upload image: {str(e)}'}), 500


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


@visual_bp.route('/session/status', methods=['GET'])
def get_session_status():
    """
    GET /api/visual-consistency/session/status?story_id=xxx

    Check the session status for a story.

    Query params:
        story_id: str (required)

    Returns:
        200: Session status
        400: Invalid request
    """
    story_id = request.args.get('story_id')
    if not story_id:
        return jsonify({'error': 'Missing required query param: story_id'}), 400

    image_client = current_app.config['SERVICES']['image_client']

    session_id = image_client.get_session_id(story_id)
    context_initialized = image_client.is_context_initialized(story_id)

    return jsonify({
        'story_id': story_id,
        'has_session': session_id is not None,
        'session_id': session_id,
        'context_initialized': context_initialized
    }), 200


@visual_bp.route('/session/rebuild', methods=['POST'])
def rebuild_session():
    """
    POST /api/visual-consistency/session/rebuild

    Rebuild the visual context (art bible + character references) for a story.
    This will regenerate images to establish the session context.

    Request body:
    {
        "story_id": str (required)
    }

    Returns:
        200: Context rebuilt successfully
        400: Invalid request
        404: Story not found
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

        # Get services
        image_client = current_app.config['SERVICES']['image_client']
        image_generator = current_app.config['SERVICES']['image_generator']
        project_repo = current_app.config['REPOSITORIES']['project']

        # Load the project to get story details
        project = project_repo.get(story_id)
        if not project or not project.story:
            return jsonify({'error': 'Story not found'}), 404

        story = project.story

        # Clear any existing session and context flag
        image_client.clear_session(story_id)

        current_app.logger.info(f"Rebuilding visual context for story {story_id}")

        # Rebuild visual context
        session_id = run_async(image_generator.rebuild_visual_context(story))

        # Mark context as initialized
        image_client.mark_context_initialized(story_id)

        # Update story with new session ID and save
        story.image_session_id = session_id
        project_repo.save(project)

        current_app.logger.info(f"Visual context rebuilt, new session_id: {session_id}")

        return jsonify({
            'session_id': session_id,
            'story_id': story_id,
            'context_initialized': True,
            'message': 'Visual context rebuilt successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error rebuilding session: {e}", exc_info=True)
        return jsonify({'error': f'Failed to rebuild visual context: {str(e)}'}), 500


@visual_bp.route('/stories/<story_id>/art-bible/copy', methods=['POST'])
def copy_art_bible_from_library(story_id):
    """
    POST /api/visual-consistency/stories/<story_id>/art-bible/copy

    Copy an art bible from another project to the current project.

    Request body:
    {
        "source_project_id": str (required),
        "image_path": str (required) - path to the source image,
        "art_style": str (optional),
        "prompt": str (optional)
    }

    Returns:
        200: Art bible copied successfully
        400: Invalid request
        404: Source or target project not found
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
        if 'source_project_id' not in data:
            return jsonify({'error': 'Missing required field: source_project_id'}), 400
        if 'image_path' not in data:
            return jsonify({'error': 'Missing required field: image_path'}), 400

        source_project_id = data['source_project_id']
        source_image_path = data['image_path']
        art_style = data.get('art_style', 'custom')
        prompt = data.get('prompt', '')

        # Get project repository
        project_repo = current_app.config['REPOSITORIES']['project']

        # Load target project
        target_project = project_repo.get(story_id)
        if not target_project or not target_project.story:
            return jsonify({'error': 'Target project not found'}), 404

        # Load source project to verify image exists
        source_project = project_repo.get(source_project_id)
        if not source_project:
            return jsonify({'error': 'Source project not found'}), 404

        # Build the full source path
        storage_dir = project_repo.storage_dir
        source_full_path = storage_dir / source_image_path

        if not source_full_path.exists():
            return jsonify({'error': 'Source image not found'}), 404

        # Get target project's images directory
        target_images_dir = project_repo.get_project_images_dir(story_id)
        target_art_bible_dir = target_images_dir / 'art_bible'

        # Generate new filename with timestamp
        import shutil
        file_ext = source_full_path.suffix or '.png'
        filename = f'art_bible_copied_{int(time.time() * 1000)}{file_ext}'
        target_path = target_art_bible_dir / filename

        # Copy the image file
        shutil.copy2(source_full_path, target_path)

        # Build relative path for storage
        local_path = f'images/{story_id}/art_bible/{filename}'
        current_app.logger.info(f"Art bible copied from {source_image_path} to {local_path}")

        # Update target project with the copied art bible
        if not target_project.story.art_bible:
            from src.models.art_bible import ArtBible
            target_project.story.art_bible = ArtBible(prompt=prompt, art_style=art_style)

        # Create version entry for the copied image
        version_entry = {
            'path': local_path,
            'model': 'copied',
            'generated_at': datetime.now().isoformat(),
            'resolution': None,
            'cost': None
        }

        # Initialize versions list if needed
        if not target_project.story.art_bible.image_versions:
            target_project.story.art_bible.image_versions = []
            # Migrate existing image to versions list if present
            if target_project.story.art_bible.local_image_path:
                existing_version = {
                    'path': target_project.story.art_bible.local_image_path,
                    'model': target_project.story.art_bible.image_model,
                    'generated_at': target_project.story.art_bible.image_generated_at.isoformat() if target_project.story.art_bible.image_generated_at else None,
                    'resolution': target_project.story.art_bible.image_resolution,
                    'cost': target_project.story.art_bible.image_cost
                }
                target_project.story.art_bible.image_versions.append(existing_version)
        target_project.story.art_bible.image_versions.append(version_entry)

        # Set the copied image as active
        target_project.story.art_bible.local_image_path = local_path
        target_project.story.art_bible.prompt = prompt
        target_project.story.art_bible.art_style = art_style
        target_project.story.art_bible.image_model = 'copied'
        target_project.story.art_bible.image_generated_at = datetime.now()

        # Save the updated project
        project_repo.save(target_project)

        return jsonify({
            'local_image_path': local_path,
            'prompt': prompt,
            'art_style': art_style,
            'message': 'Art bible copied successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error copying art bible: {e}", exc_info=True)
        return jsonify({'error': f'Failed to copy art bible: {str(e)}'}), 500


@visual_bp.route('/stories/<story_id>/characters/copy', methods=['POST'])
def copy_character_from_library(story_id):
    """
    POST /api/visual-consistency/stories/<story_id>/characters/copy

    Copy a character reference from another project to the current project.

    Request body:
    {
        "source_project_id": str (required),
        "image_path": str (required) - path to the source image,
        "character_name": str (required),
        "prompt": str (optional),
        "species": str (optional),
        "physical_description": str (optional),
        "clothing": str (optional),
        "distinctive_features": str (optional)
    }

    Returns:
        200: Character copied successfully
        400: Invalid request
        404: Source or target project not found
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
        if 'source_project_id' not in data:
            return jsonify({'error': 'Missing required field: source_project_id'}), 400
        if 'image_path' not in data:
            return jsonify({'error': 'Missing required field: image_path'}), 400
        if 'character_name' not in data:
            return jsonify({'error': 'Missing required field: character_name'}), 400

        source_project_id = data['source_project_id']
        source_image_path = data['image_path']
        character_name = data['character_name']
        prompt = data.get('prompt', '')
        species = data.get('species', '')
        physical_description = data.get('physical_description', '')
        clothing = data.get('clothing', '')
        distinctive_features = data.get('distinctive_features', '')

        # Get project repository
        project_repo = current_app.config['REPOSITORIES']['project']

        # Load target project
        target_project = project_repo.get(story_id)
        if not target_project or not target_project.story:
            return jsonify({'error': 'Target project not found'}), 404

        # Load source project to verify image exists
        source_project = project_repo.get(source_project_id)
        if not source_project:
            return jsonify({'error': 'Source project not found'}), 404

        # Build the full source path
        storage_dir = project_repo.storage_dir
        source_full_path = storage_dir / source_image_path

        if not source_full_path.exists():
            return jsonify({'error': 'Source image not found'}), 404

        # Get target project's images directory
        target_images_dir = project_repo.get_project_images_dir(story_id)
        target_characters_dir = target_images_dir / 'characters'

        # Generate new filename with timestamp
        import shutil
        file_ext = source_full_path.suffix or '.png'
        safe_char_name = character_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f'character_{safe_char_name}_copied_{int(time.time() * 1000)}{file_ext}'
        target_path = target_characters_dir / filename

        # Copy the image file
        shutil.copy2(source_full_path, target_path)

        # Build relative path for storage
        local_path = f'images/{story_id}/characters/{filename}'
        current_app.logger.info(f"Character {character_name} copied from {source_image_path} to {local_path}")

        # Update target project with the copied character reference
        if not target_project.story.character_references:
            target_project.story.character_references = []

        # Create version entry for the copied image
        version_entry = {
            'path': local_path,
            'model': 'copied',
            'generated_at': datetime.now().isoformat(),
            'resolution': None,
            'cost': None
        }

        # Check if character already exists in target project
        existing_ref = next(
            (ref for ref in target_project.story.character_references if ref.character_name == character_name),
            None
        )

        if existing_ref:
            # Initialize versions list if needed
            if not existing_ref.image_versions:
                existing_ref.image_versions = []
                if existing_ref.local_image_path:
                    existing_version = {
                        'path': existing_ref.local_image_path,
                        'model': existing_ref.image_model,
                        'generated_at': existing_ref.image_generated_at.isoformat() if existing_ref.image_generated_at else None,
                        'resolution': existing_ref.image_resolution,
                        'cost': existing_ref.image_cost
                    }
                    existing_ref.image_versions.append(existing_version)
            existing_ref.image_versions.append(version_entry)

            # Update with copied data
            existing_ref.local_image_path = local_path
            existing_ref.prompt = prompt
            existing_ref.species = species
            existing_ref.physical_description = physical_description
            existing_ref.clothing = clothing
            existing_ref.distinctive_features = distinctive_features
            existing_ref.image_model = 'copied'
            existing_ref.image_generated_at = datetime.now()
        else:
            # Create new character reference
            from src.models.art_bible import CharacterReference
            new_ref = CharacterReference(
                character_name=character_name,
                prompt=prompt,
                species=species,
                physical_description=physical_description,
                clothing=clothing,
                distinctive_features=distinctive_features,
                local_image_path=local_path,
                image_model='copied',
                image_generated_at=datetime.now(),
                image_versions=[version_entry]
            )
            target_project.story.character_references.append(new_ref)

        # Also add the character to story.characters if not present
        if not target_project.story.characters:
            target_project.story.characters = []

        existing_char = next(
            (char for char in target_project.story.characters if char.name == character_name),
            None
        )
        if not existing_char:
            from src.models.character import CharacterProfile
            new_char = CharacterProfile(
                name=character_name,
                species=species,
                physical_description=physical_description,
                clothing=clothing,
                distinctive_features=distinctive_features
            )
            target_project.story.characters.append(new_char)

        # Save the updated project
        project_repo.save(target_project)

        return jsonify({
            'local_image_path': local_path,
            'character_name': character_name,
            'prompt': prompt,
            'message': 'Character copied successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error copying character: {e}", exc_info=True)
        return jsonify({'error': f'Failed to copy character: {str(e)}'}), 500
