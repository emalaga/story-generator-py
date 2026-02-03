"""
Image Routes for REST API.

Handles endpoints for image generation and saving.
"""

import asyncio
import base64
import time
import httpx
from datetime import datetime
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


async def save_image_to_disk(image_url: str, project_id: str, image_type: str, filename: str) -> str:
    """
    Save an image to disk and return the relative path.

    Args:
        image_url: The image URL or base64 data URL
        project_id: The project/story ID
        image_type: Type of image ('art_bible', 'character', 'page')
        filename: The filename to save as

    Returns:
        Relative path to the saved image (e.g., 'images/project-id/pages/filename.png')
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
        "session_id": str (optional) - existing session ID for continuation,
        "size": str (optional) - Image size (default: 1024x1024),
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
        # Get size and quality from request, with defaults
        image_size = data.get('size', '1024x1024')
        image_quality = data.get('quality', 'low')
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
            print(f"[DEBUG] About to call generate_image_with_cost", flush=True)
            image_model = data.get('image_model', 'gpt-image-1')
            current_app.logger.info(f"  Calling generate_image_with_cost with custom prompt, size={image_size}, quality={image_quality}, model={image_model}...")
            try:
                print(f"[DEBUG] Inside try block, calling run_async(generate_image_with_cost)", flush=True)
                result = run_async(image_client.generate_image_with_cost(
                    story_id,
                    custom_prompt,
                    size=image_size,
                    quality=image_quality,
                    model_name=image_model
                ))
                image_url = result['image_url']
                image_cost = result.get('cost')
                print(f"[DEBUG] generate_image_with_cost returned, URL length={len(image_url) if image_url else 0}, cost={image_cost}", flush=True)
                current_app.logger.info(f"  generate_image_with_cost completed, URL length: {len(image_url) if image_url else 0}, cost: {image_cost}")
            except Exception as e:
                print(f"[DEBUG] generate_image_with_cost EXCEPTION: {type(e).__name__}: {e}", flush=True)
                current_app.logger.error(f"  generate_image_with_cost FAILED: {e}", exc_info=True)
                raise

            # Update session ID in story
            story.image_session_id = image_client.get_session_id(story_id)
        else:
            # Generate image using conversation session (builds prompt automatically)
            # Note: This path doesn't return cost information yet
            current_app.logger.info(f"  Generating with automatic prompt building, size={image_size}, quality={image_quality}")
            image_url = run_async(image_generator.generate_image_for_page(
                story,
                scene_description,
                character_profiles,
                art_style,
                size=image_size,
                quality=image_quality
            ))
            image_cost = None  # Cost not available for automatic prompt generation

        # Get updated session ID
        new_session_id = image_client.get_session_id(story_id)

        # Log what we're returning
        current_app.logger.info(f"  Image URL returned: {image_url[:100] if image_url else 'None'}...")
        current_app.logger.info(f"  New session ID: {new_session_id}")

        # Save the image to disk
        filename = f'page_{page_num}_{int(time.time() * 1000)}.png'
        local_path = run_async(save_image_to_disk(image_url, story_id, 'page', filename))
        current_app.logger.info(f"  Page image saved to: {local_path}")

        # Update the project file with the new image path and metadata
        try:
            project_repo = current_app.config['REPOSITORIES']['project']
            project = project_repo.get(story_id)
            if project and project.story and project.story.pages:
                # Find the page and update its image path and metadata
                for page in project.story.pages:
                    if page.page_number == page_num:
                        # Create version entry for the new image
                        image_model = data.get('image_model', 'gpt-image-1')
                        generated_at = datetime.now()
                        version_entry = {
                            'path': local_path,
                            'model': image_model,
                            'generated_at': generated_at.isoformat(),
                            'resolution': image_size,
                            'cost': image_cost,
                            'prompt': custom_prompt
                        }

                        # Initialize versions list if needed, preserving existing image
                        if not page.image_versions:
                            page.image_versions = []
                            # Migrate existing image to versions list if present
                            if page.local_image_path:
                                existing_version = {
                                    'path': page.local_image_path,
                                    'model': page.image_model,
                                    'generated_at': page.image_generated_at.isoformat() if page.image_generated_at else None,
                                    'resolution': page.image_resolution,
                                    'cost': page.image_cost,
                                    'prompt': page.image_prompt
                                }
                                page.image_versions.append(existing_version)
                        page.image_versions.append(version_entry)

                        # Set the new image as active
                        page.local_image_path = local_path
                        # Also save the prompt if we have a custom one
                        if custom_prompt:
                            page.image_prompt = custom_prompt
                        # Save image generation metadata for active version
                        page.image_model = image_model
                        page.image_generated_at = generated_at
                        page.image_resolution = image_size
                        page.image_cost = image_cost
                        current_app.logger.info(f"  Page {page_num} now has {len(page.image_versions)} version(s)")
                        break
                project.story.image_session_id = new_session_id
                project_repo.save(project)
                current_app.logger.info(f"  Project updated with page image path and metadata")
        except Exception as e:
            current_app.logger.warning(f"  Failed to update project with page image: {e}")

        return jsonify({
            'local_image_path': local_path,
            'page_number': page_num,
            'session_id': new_session_id,  # Return session ID for persistence
            'image_cost': image_cost  # Estimated cost in USD
        }), 200

    except ValueError as e:
        current_app.logger.error(f"ValueError generating image: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating image: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@image_bp.route('/stories/<story_id>/cover', methods=['POST'])
def generate_cover_image(story_id):
    """
    POST /api/images/stories/:id/cover - Generate cover image for the story

    Uses conversation session for visual consistency with art bible and characters.

    Request body:
    {
        "custom_prompt": str (required) - the cover prompt,
        "art_style": str (optional),
        "characters": List[dict] (optional),
        "session_id": str (optional) - existing session ID for continuation,
        "size": str (optional) - Image size (default: 1024x1024),
        "quality": str (optional) - Image quality/detail (default: low)
    }

    Returns:
        200: Cover image generated successfully with session_id
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

        # Get image client and generator service
        image_client = current_app.config['SERVICES']['image_client']
        image_generator = current_app.config['SERVICES']['image_generator']

        # Get parameters
        custom_prompt = data.get('custom_prompt', '')
        if not custom_prompt:
            return jsonify({'error': 'Missing required field: custom_prompt'}), 400

        art_style = data.get('art_style', 'cartoon')
        session_id = data.get('session_id')
        story_title = data.get('story_title', '')
        # Get size and quality from request, with defaults
        image_size = data.get('size', '1024x1024')
        image_quality = data.get('quality', 'low')
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
            pages=[],
            characters=character_profiles,
            art_bible=art_bible,
            character_references=character_references if character_references else None,
            image_session_id=session_id
        )

        # If we have a session ID, load it into the client
        if session_id:
            image_client.set_session_id(story_id, session_id)

        # Log for debugging
        current_app.logger.info(f"Generating cover image with {len(character_profiles)} characters")
        current_app.logger.info(f"  Session ID: {session_id or 'None (will create new)'}")

        # Ensure session exists
        run_async(image_generator.ensure_session(story))
        current_app.logger.info(f"  ensure_session completed, session_id: {story.image_session_id}")

        # Generate cover image directly with custom prompt
        image_model = data.get('image_model', 'gpt-image-1')
        current_app.logger.info(f"  Calling generate_image_with_cost with cover prompt, size={image_size}, quality={image_quality}, model={image_model}...")
        result = run_async(image_client.generate_image_with_cost(
            story_id,
            custom_prompt,
            size=image_size,
            quality=image_quality,
            model_name=image_model
        ))
        image_url = result['image_url']
        image_cost = result.get('cost')
        current_app.logger.info(f"  generate_image_with_cost completed, URL length: {len(image_url) if image_url else 0}, cost: {image_cost}")

        # Get updated session ID
        new_session_id = image_client.get_session_id(story_id)

        # Save the image to disk
        filename = f'cover_{int(time.time() * 1000)}.png'
        local_path = run_async(save_image_to_disk(image_url, story_id, 'page', filename))
        current_app.logger.info(f"  Cover image saved to: {local_path}")

        # Update the project file with the new cover image path and metadata
        try:
            from src.models.story import CoverPage
            project_repo = current_app.config['REPOSITORIES']['project']
            project = project_repo.get(story_id)
            if project and project.story:
                # Initialize cover_page if not present
                if not project.story.cover_page:
                    project.story.cover_page = CoverPage()

                # Create version entry for the new image
                image_model = data.get('image_model', 'gpt-image-1')
                generated_at = datetime.now()
                version_entry = {
                    'path': local_path,
                    'model': image_model,
                    'generated_at': generated_at.isoformat(),
                    'resolution': image_size,
                    'cost': image_cost,
                    'prompt': custom_prompt
                }

                # Initialize versions list if needed, preserving existing image
                if not project.story.cover_page.image_versions:
                    project.story.cover_page.image_versions = []
                    # Migrate existing image to versions list if present
                    if project.story.cover_page.local_image_path:
                        existing_version = {
                            'path': project.story.cover_page.local_image_path,
                            'model': project.story.cover_page.image_model,
                            'generated_at': project.story.cover_page.image_generated_at.isoformat() if project.story.cover_page.image_generated_at else None,
                            'resolution': project.story.cover_page.image_resolution,
                            'cost': project.story.cover_page.image_cost,
                            'prompt': project.story.cover_page.image_prompt
                        }
                        project.story.cover_page.image_versions.append(existing_version)
                project.story.cover_page.image_versions.append(version_entry)

                # Set the new image as active
                project.story.cover_page.local_image_path = local_path
                project.story.cover_page.image_prompt = custom_prompt
                # Save image generation metadata for active version
                project.story.cover_page.image_model = image_model
                project.story.cover_page.image_generated_at = generated_at
                project.story.cover_page.image_resolution = image_size
                project.story.cover_page.image_cost = image_cost
                project.story.image_session_id = new_session_id
                project_repo.save(project)
                current_app.logger.info(f"  Project updated with cover image path and metadata (version {len(project.story.cover_page.image_versions)})")
        except Exception as e:
            current_app.logger.warning(f"  Failed to update project with cover image: {e}")

        return jsonify({
            'local_image_path': local_path,
            'session_id': new_session_id,  # Return session ID for persistence
            'image_cost': image_cost  # Estimated cost in USD
        }), 200

    except ValueError as e:
        current_app.logger.error(f"ValueError generating cover image: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating cover image: {e}", exc_info=True)
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


@image_bp.route('/stories/<story_id>/art-bible/set-active', methods=['POST'])
def set_active_art_bible_version(story_id):
    """
    POST /api/images/stories/:id/art-bible/set-active - Set active art bible image version

    Request body:
    {
        "image_path": str (required) - path of the version to set as active
    }

    Returns:
        200: Active version updated
        400: Invalid request
        404: Story or version not found
        500: Server error
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        if 'image_path' not in data:
            return jsonify({'error': 'Missing required field: image_path'}), 400

        image_path = data['image_path']

        project_repo = current_app.config['REPOSITORIES']['project']
        project = project_repo.get(story_id)

        if not project or not project.story:
            return jsonify({'error': 'Story not found'}), 404

        if not project.story.art_bible:
            return jsonify({'error': 'Art bible not found'}), 404

        # Find the version in the versions list
        if not project.story.art_bible.image_versions:
            return jsonify({'error': 'No versions available'}), 404

        version = next(
            (v for v in project.story.art_bible.image_versions if v['path'] == image_path),
            None
        )
        if not version:
            return jsonify({'error': 'Version not found'}), 404

        # Update the active image
        project.story.art_bible.local_image_path = version['path']
        project.story.art_bible.image_model = version.get('model')
        project.story.art_bible.image_resolution = version.get('resolution')
        project.story.art_bible.image_cost = version.get('cost')
        if version.get('generated_at'):
            from datetime import datetime
            try:
                project.story.art_bible.image_generated_at = datetime.fromisoformat(version['generated_at'])
            except (ValueError, TypeError):
                pass

        project_repo.save(project)
        current_app.logger.info(f"Set active art bible version to: {image_path}")

        return jsonify({
            'success': True,
            'active_path': image_path
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting active art bible version: {e}")
        return jsonify({'error': f'Failed to set active version: {str(e)}'}), 500


@image_bp.route('/stories/<story_id>/characters/<character_name>/set-active', methods=['POST'])
def set_active_character_version(story_id, character_name):
    """
    POST /api/images/stories/:id/characters/:name/set-active - Set active character reference version

    Request body:
    {
        "image_path": str (required) - path of the version to set as active
    }

    Returns:
        200: Active version updated
        400: Invalid request
        404: Story, character, or version not found
        500: Server error
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        if 'image_path' not in data:
            return jsonify({'error': 'Missing required field: image_path'}), 400

        image_path = data['image_path']

        project_repo = current_app.config['REPOSITORIES']['project']
        project = project_repo.get(story_id)

        if not project or not project.story:
            return jsonify({'error': 'Story not found'}), 404

        if not project.story.character_references:
            return jsonify({'error': 'No character references found'}), 404

        # URL decode the character name
        from urllib.parse import unquote
        character_name = unquote(character_name)

        # Find the character reference
        char_ref = next(
            (ref for ref in project.story.character_references if ref.character_name == character_name),
            None
        )
        if not char_ref:
            return jsonify({'error': f'Character "{character_name}" not found'}), 404

        # Find the version in the versions list
        if not char_ref.image_versions:
            return jsonify({'error': 'No versions available'}), 404

        version = next(
            (v for v in char_ref.image_versions if v['path'] == image_path),
            None
        )
        if not version:
            return jsonify({'error': 'Version not found'}), 404

        # Update the active image
        char_ref.local_image_path = version['path']
        char_ref.image_model = version.get('model')
        char_ref.image_resolution = version.get('resolution')
        char_ref.image_cost = version.get('cost')
        if version.get('generated_at'):
            from datetime import datetime
            try:
                char_ref.image_generated_at = datetime.fromisoformat(version['generated_at'])
            except (ValueError, TypeError):
                pass

        project_repo.save(project)
        current_app.logger.info(f"Set active character reference version for {character_name} to: {image_path}")

        return jsonify({
            'success': True,
            'active_path': image_path,
            'character_name': character_name
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting active character version: {e}")
        return jsonify({'error': f'Failed to set active version: {str(e)}'}), 500


@image_bp.route('/stories/<story_id>/pages/<int:page_num>/set-active', methods=['POST'])
def set_active_page_version(story_id, page_num):
    """
    POST /api/images/stories/:id/pages/:page_num/set-active - Set active page image version

    Request body:
    {
        "image_path": str (required) - path of the version to set as active
    }

    Returns:
        200: Active version updated
        400: Invalid request
        404: Story, page, or version not found
        500: Server error
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        if 'image_path' not in data:
            return jsonify({'error': 'Missing required field: image_path'}), 400

        image_path = data['image_path']

        project_repo = current_app.config['REPOSITORIES']['project']
        project = project_repo.get(story_id)

        if not project or not project.story:
            return jsonify({'error': 'Story not found'}), 404

        if not project.story.pages:
            return jsonify({'error': 'No pages found'}), 404

        # Find the page
        page = next(
            (p for p in project.story.pages if p.page_number == page_num),
            None
        )
        if not page:
            return jsonify({'error': f'Page {page_num} not found'}), 404

        # Find the version in the versions list
        if not page.image_versions:
            return jsonify({'error': 'No versions available'}), 404

        version = next(
            (v for v in page.image_versions if v['path'] == image_path),
            None
        )
        if not version:
            return jsonify({'error': 'Version not found'}), 404

        # Update the active image
        page.local_image_path = version['path']
        page.image_model = version.get('model')
        page.image_resolution = version.get('resolution')
        page.image_cost = version.get('cost')
        if version.get('prompt'):
            page.image_prompt = version['prompt']
        if version.get('generated_at'):
            from datetime import datetime
            try:
                page.image_generated_at = datetime.fromisoformat(version['generated_at'])
            except (ValueError, TypeError):
                pass

        project_repo.save(project)
        current_app.logger.info(f"Set active page {page_num} version to: {image_path}")

        return jsonify({
            'success': True,
            'active_path': image_path,
            'page_number': page_num
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting active page version: {e}")
        return jsonify({'error': f'Failed to set active version: {str(e)}'}), 500


@image_bp.route('/stories/<story_id>/cover/set-active', methods=['POST'])
def set_active_cover_version(story_id):
    """
    POST /api/images/stories/:id/cover/set-active - Set active cover image version

    Request body:
    {
        "image_path": str (required) - path of the version to set as active
    }

    Returns:
        200: Active version updated
        400: Invalid request
        404: Story, cover, or version not found
        500: Server error
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        if 'image_path' not in data:
            return jsonify({'error': 'Missing required field: image_path'}), 400

        image_path = data['image_path']

        project_repo = current_app.config['REPOSITORIES']['project']
        project = project_repo.get(story_id)

        if not project or not project.story:
            return jsonify({'error': 'Story not found'}), 404

        if not project.story.cover_page:
            return jsonify({'error': 'Cover page not found'}), 404

        # Find the version in the versions list
        if not project.story.cover_page.image_versions:
            return jsonify({'error': 'No versions available'}), 404

        version = next(
            (v for v in project.story.cover_page.image_versions if v['path'] == image_path),
            None
        )
        if not version:
            return jsonify({'error': 'Version not found'}), 404

        # Update the active image
        project.story.cover_page.local_image_path = version['path']
        project.story.cover_page.image_model = version.get('model')
        project.story.cover_page.image_resolution = version.get('resolution')
        project.story.cover_page.image_cost = version.get('cost')
        if version.get('prompt'):
            project.story.cover_page.image_prompt = version['prompt']
        if version.get('generated_at'):
            from datetime import datetime
            try:
                project.story.cover_page.image_generated_at = datetime.fromisoformat(version['generated_at'])
            except (ValueError, TypeError):
                pass

        project_repo.save(project)
        current_app.logger.info(f"Set active cover version to: {image_path}")

        return jsonify({
            'success': True,
            'active_path': image_path
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error setting active cover version: {e}")
        return jsonify({'error': f'Failed to set active version: {str(e)}'}), 500
