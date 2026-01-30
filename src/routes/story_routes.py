"""
Story Routes for REST API.

Handles endpoints for story generation and management.
"""

import asyncio
import threading
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest

from src.models.story import StoryMetadata

# Create blueprint
story_bp = Blueprint('stories', __name__)

# In-memory storage for background generation tasks
# Key: task_id, Value: dict with status, result, error, created_at
_generation_tasks = {}

# In-memory storage for background character extraction tasks
_character_extraction_tasks = {}


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


@story_bp.route('', methods=['POST'])
def create_story():
    """
    POST /api/stories - Create a new story

    Request body:
    {
        "title": str (required),
        "language": str (optional),
        "complexity": str (optional),
        "vocabulary_diversity": str (optional),
        "age_group": str (optional),
        "num_pages": int (optional),
        "genre": str (optional),
        "art_style": str (optional),
        "theme": str (optional),
        "custom_prompt": str (optional)
    }

    Returns:
        201: Story created successfully
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
        if 'title' not in data:
            return jsonify({'error': 'Missing required field: title'}), 400

        # Get app config for defaults
        app_config = current_app.config['APP_CONFIG']
        defaults = app_config.defaults

        # Build metadata with defaults
        metadata = StoryMetadata(
            title=data['title'],
            language=data.get('language', defaults.language),
            complexity=data.get('complexity', defaults.complexity),
            vocabulary_diversity=data.get('vocabulary_diversity', defaults.vocabulary_diversity),
            age_group=data.get('age_group', defaults.age_group),
            num_pages=data.get('num_pages', defaults.num_pages),
            genre=data.get('genre', defaults.genre),
            art_style=data.get('art_style', defaults.art_style),
            user_prompt=data.get('custom_prompt'),
            words_per_page=data.get('words_per_page', 50)
        )

        # Get optional parameters
        theme = data.get('theme')
        custom_prompt = data.get('custom_prompt')
        text_model = data.get('text_model')

        # Get the default story generator service
        story_generator = current_app.config['SERVICES']['story_generator']

        # If a specific text model is selected, create a custom story generator
        if text_model:
            from src.ai.ai_factory import AIClientFactory
            from src.domain.character_extractor import CharacterExtractor
            from src.domain.prompt_builder import PromptBuilder
            from src.services.story_generator import StoryGeneratorService

            print(f"[STORY ROUTES] Using custom text model: {text_model}")
            try:
                text_client = AIClientFactory.create_text_client_for_model(app_config, text_model)
                prompt_builder = PromptBuilder(ai_client=text_client)
                character_extractor = CharacterExtractor(text_client)
                story_generator = StoryGeneratorService(
                    ai_client=text_client,
                    prompt_builder=prompt_builder,
                    character_extractor=character_extractor
                )
            except ValueError as e:
                print(f"[STORY ROUTES] Failed to create custom client: {e}, using default")

        # Generate story (async)
        story = run_async(story_generator.generate_story(
            metadata,
            theme=theme,
            custom_prompt=custom_prompt
        ))

        # Debug logging
        print(f"[STORY ROUTES] Story generated: ID={story.id}")
        print(f"[STORY ROUTES] Pages: {len(story.pages)}")
        print(f"[STORY ROUTES] Characters: {len(story.characters) if story.characters else 0}")
        if len(story.pages) == 0:
            print("="*80)
            print("[STORY ROUTES] ERROR: Story has 0 pages!")
            print("="*80)
        for i, page in enumerate(story.pages[:3]):  # Show first 3 pages
            print(f"[STORY ROUTES] Page {page.page_number}: {page.text[:100]}...")

        # Auto-save story as a project to disk
        # This ensures recovery if the response doesn't reach the client
        from src.models.project import Project, ProjectStatus
        project_repo = current_app.config['REPOSITORIES']['project']

        project = Project(
            id=story.id,  # Use story ID as project ID for consistency
            name=metadata.title,
            story=story,
            status=ProjectStatus.STORY_GENERATED,
            character_profiles=list(story.characters) if story.characters else []
        )
        project_repo.save(project)
        print(f"[STORY ROUTES] Auto-saved project to disk: ID={project.id}")

        # Convert to JSON-serializable dict
        response = {
            'id': story.id,
            'project_id': project.id,  # Include project_id so client knows it's saved
            'metadata': {
                'title': story.metadata.title,
                'language': story.metadata.language,
                'complexity': story.metadata.complexity,
                'vocabulary_diversity': story.metadata.vocabulary_diversity,
                'age_group': story.metadata.age_group,
                'num_pages': story.metadata.num_pages,
                'words_per_page': story.metadata.words_per_page,
                'genre': story.metadata.genre,
                'art_style': story.metadata.art_style,
                'user_prompt': story.metadata.user_prompt
            },
            'pages': [
                {
                    'page_number': page.page_number,
                    'text': page.text,
                    'image_url': page.image_url,
                    'image_prompt': page.image_prompt
                }
                for page in story.pages
            ],
            'characters': [
                {
                    'name': char.name,
                    'species': char.species,
                    'physical_description': char.physical_description,
                    'clothing': char.clothing,
                    'distinctive_features': char.distinctive_features,
                    'personality_traits': char.personality_traits
                }
                for char in (story.characters or [])
            ],
            'vocabulary': story.vocabulary,
            'created_at': story.created_at.isoformat(),
            'updated_at': story.updated_at.isoformat()
        }

        return jsonify(response), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error creating story: {e}\n{error_details}")
        # Return more specific error message to help with debugging
        return jsonify({'error': f'Failed to generate story: {str(e)}'}), 500


def _run_story_generation_in_background(task_id, app, data, app_config, defaults):
    """
    Background worker function for story generation.
    Runs in a separate thread to avoid blocking the main request.
    """
    with app.app_context():
        try:
            _generation_tasks[task_id]['status'] = 'running'

            # Build metadata
            metadata = StoryMetadata(
                title=data['title'],
                language=data.get('language', defaults.language),
                complexity=data.get('complexity', defaults.complexity),
                vocabulary_diversity=data.get('vocabulary_diversity', defaults.vocabulary_diversity),
                age_group=data.get('age_group', defaults.age_group),
                num_pages=data.get('num_pages', defaults.num_pages),
                genre=data.get('genre', defaults.genre),
                art_style=data.get('art_style', defaults.art_style),
                user_prompt=data.get('custom_prompt'),
                words_per_page=data.get('words_per_page', 50)
            )

            theme = data.get('theme')
            custom_prompt = data.get('custom_prompt')
            text_model = data.get('text_model')

            # Get the default story generator service
            story_generator = app.config['SERVICES']['story_generator']

            # If a specific text model is selected, create a custom story generator
            if text_model:
                from src.ai.ai_factory import AIClientFactory
                from src.domain.character_extractor import CharacterExtractor
                from src.domain.prompt_builder import PromptBuilder
                from src.services.story_generator import StoryGeneratorService

                print(f"[STORY ROUTES ASYNC] Using custom text model: {text_model}")
                try:
                    text_client = AIClientFactory.create_text_client_for_model(app_config, text_model)
                    prompt_builder = PromptBuilder(ai_client=text_client)
                    character_extractor = CharacterExtractor(text_client)
                    story_generator = StoryGeneratorService(
                        ai_client=text_client,
                        prompt_builder=prompt_builder,
                        character_extractor=character_extractor
                    )
                except ValueError as e:
                    print(f"[STORY ROUTES ASYNC] Failed to create custom client: {e}, using default")

            # Generate story
            story = run_async(story_generator.generate_story(
                metadata,
                theme=theme,
                custom_prompt=custom_prompt
            ))

            print(f"[STORY ROUTES ASYNC] Story generated: ID={story.id}")
            print(f"[STORY ROUTES ASYNC] Pages: {len(story.pages)}")

            # Auto-save story as a project
            from src.models.project import Project, ProjectStatus
            project_repo = app.config['REPOSITORIES']['project']

            project = Project(
                id=story.id,
                name=metadata.title,
                story=story,
                status=ProjectStatus.STORY_GENERATED,
                character_profiles=list(story.characters) if story.characters else []
            )
            project_repo.save(project)
            print(f"[STORY ROUTES ASYNC] Auto-saved project: ID={project.id}")

            # Build response
            result = {
                'id': story.id,
                'project_id': project.id,
                'metadata': {
                    'title': story.metadata.title,
                    'language': story.metadata.language,
                    'complexity': story.metadata.complexity,
                    'vocabulary_diversity': story.metadata.vocabulary_diversity,
                    'age_group': story.metadata.age_group,
                    'num_pages': story.metadata.num_pages,
                    'words_per_page': story.metadata.words_per_page,
                    'genre': story.metadata.genre,
                    'art_style': story.metadata.art_style,
                    'user_prompt': story.metadata.user_prompt
                },
                'pages': [
                    {
                        'page_number': page.page_number,
                        'text': page.text,
                        'image_url': page.image_url,
                        'image_prompt': page.image_prompt
                    }
                    for page in story.pages
                ],
                'characters': [
                    {
                        'name': char.name,
                        'species': char.species,
                        'physical_description': char.physical_description,
                        'clothing': char.clothing,
                        'distinctive_features': char.distinctive_features,
                        'personality_traits': char.personality_traits
                    }
                    for char in (story.characters or [])
                ],
                'vocabulary': story.vocabulary,
                'created_at': story.created_at.isoformat(),
                'updated_at': story.updated_at.isoformat()
            }

            _generation_tasks[task_id]['status'] = 'completed'
            _generation_tasks[task_id]['result'] = result
            _generation_tasks[task_id]['completed_at'] = datetime.now().isoformat()

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[STORY ROUTES ASYNC] Error: {e}\n{error_details}")
            _generation_tasks[task_id]['status'] = 'error'
            _generation_tasks[task_id]['error'] = str(e)
            _generation_tasks[task_id]['completed_at'] = datetime.now().isoformat()


@story_bp.route('/async', methods=['POST'])
def create_story_async():
    """
    POST /api/stories/async - Start story generation in background

    Returns immediately with a task_id that can be polled for status.

    Request body: Same as POST /api/stories

    Returns:
        202: Generation started, returns task_id
        400: Invalid request
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        try:
            data = request.get_json()
        except BadRequest:
            return jsonify({'error': 'Invalid JSON'}), 400

        if 'title' not in data:
            return jsonify({'error': 'Missing required field: title'}), 400

        # Generate task ID
        task_id = str(uuid.uuid4())

        # Get app config
        app_config = current_app.config['APP_CONFIG']
        defaults = app_config.defaults

        # Store task info
        _generation_tasks[task_id] = {
            'status': 'pending',
            'result': None,
            'error': None,
            'created_at': datetime.now().isoformat(),
            'completed_at': None,
            'title': data['title']
        }

        # Start background thread
        # Need to pass app reference for context
        app = current_app._get_current_object()
        thread = threading.Thread(
            target=_run_story_generation_in_background,
            args=(task_id, app, data, app_config, defaults)
        )
        thread.daemon = True
        thread.start()

        print(f"[STORY ROUTES] Started async generation task: {task_id}")

        return jsonify({
            'task_id': task_id,
            'status': 'pending',
            'message': 'Story generation started'
        }), 202

    except Exception as e:
        return jsonify({'error': f'Failed to start generation: {str(e)}'}), 500


@story_bp.route('/status/<task_id>', methods=['GET'])
def get_generation_status(task_id):
    """
    GET /api/stories/status/<task_id> - Check story generation status

    Returns:
        200: Status info (pending, running, completed, error)
        404: Task not found
    """
    if task_id not in _generation_tasks:
        return jsonify({'error': 'Task not found'}), 404

    task = _generation_tasks[task_id]

    response = {
        'task_id': task_id,
        'status': task['status'],
        'created_at': task['created_at'],
        'completed_at': task['completed_at']
    }

    if task['status'] == 'completed':
        response['result'] = task['result']
        # Clean up old tasks (keep for 5 minutes after completion)
        # In production, you'd want a proper cleanup mechanism
    elif task['status'] == 'error':
        response['error'] = task['error']

    return jsonify(response), 200


@story_bp.route('/extract-characters', methods=['POST'])
def extract_characters():
    """
    POST /api/stories/extract-characters - Extract characters from story pages

    Request body:
    {
        "pages": [
            {"page_number": int, "text": str},
            ...
        ],
        "text_model": str (optional) - Model to use in format "provider:model"
    }

    Returns:
        200: Characters extracted successfully
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
        if 'pages' not in data or not data['pages']:
            return jsonify({'error': 'Missing required field: pages'}), 400

        # Import StoryPage here to avoid circular imports
        from src.models.story import StoryPage

        # Convert page data to StoryPage objects
        pages = []
        for page_data in data['pages']:
            page = StoryPage(
                page_number=page_data.get('page_number', 0),
                text=page_data.get('text', '')
            )
            pages.append(page)

        # Combine all page texts for full story context
        full_story_text = '\n\n'.join([f"Page {p.page_number}:\n{p.text}" for p in pages])

        # Get optional text_model parameter
        text_model = data.get('text_model')

        # Get the default story generator service
        story_generator = current_app.config['SERVICES']['story_generator']

        # If a specific text model is selected, create a custom story generator
        if text_model:
            from src.ai.ai_factory import AIClientFactory
            from src.domain.character_extractor import CharacterExtractor
            from src.domain.prompt_builder import PromptBuilder
            from src.services.story_generator import StoryGeneratorService

            app_config = current_app.config['APP_CONFIG']
            print(f"[STORY ROUTES] Using custom text model for character extraction: {text_model}")
            try:
                text_client = AIClientFactory.create_text_client_for_model(app_config, text_model)
                prompt_builder = PromptBuilder(ai_client=text_client)
                character_extractor = CharacterExtractor(text_client)
                story_generator = StoryGeneratorService(
                    ai_client=text_client,
                    prompt_builder=prompt_builder,
                    character_extractor=character_extractor
                )
            except ValueError as e:
                print(f"[STORY ROUTES] Failed to create custom client: {e}, using default")

        # Extract characters (async)
        characters = run_async(story_generator.extract_characters_from_story(
            pages,
            full_story_text
        ))

        # Convert to JSON-serializable format
        response = {
            'characters': [
                {
                    'name': char.name,
                    'species': char.species,
                    'physical_description': char.physical_description,
                    'clothing': char.clothing,
                    'distinctive_features': char.distinctive_features,
                    'personality_traits': char.personality_traits
                }
                for char in characters
            ]
        }

        print(f"[STORY ROUTES] Extracted {len(characters)} characters on demand")

        return jsonify(response), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error extracting characters: {e}\n{error_details}")
        return jsonify({'error': f'Failed to extract characters: {str(e)}'}), 500


def _run_character_extraction_in_background(task_id, app, data, app_config):
    """
    Background worker function for character extraction.
    Runs in a separate thread to avoid blocking the main request.
    """
    with app.app_context():
        try:
            _character_extraction_tasks[task_id]['status'] = 'running'

            # Import StoryPage here to avoid circular imports
            from src.models.story import StoryPage

            # Convert page data to StoryPage objects
            pages = []
            for page_data in data['pages']:
                page = StoryPage(
                    page_number=page_data.get('page_number', 0),
                    text=page_data.get('text', '')
                )
                pages.append(page)

            # Combine all page texts for full story context
            full_story_text = '\n\n'.join([f"Page {p.page_number}:\n{p.text}" for p in pages])

            text_model = data.get('text_model')
            project_id = data.get('project_id')

            # Get the default story generator service
            story_generator = app.config['SERVICES']['story_generator']

            # If a specific text model is selected, create a custom story generator
            if text_model:
                from src.ai.ai_factory import AIClientFactory
                from src.domain.character_extractor import CharacterExtractor
                from src.domain.prompt_builder import PromptBuilder
                from src.services.story_generator import StoryGeneratorService

                print(f"[STORY ROUTES ASYNC] Using custom text model for character extraction: {text_model}")
                try:
                    text_client = AIClientFactory.create_text_client_for_model(app_config, text_model)
                    prompt_builder = PromptBuilder(ai_client=text_client)
                    character_extractor = CharacterExtractor(text_client)
                    story_generator = StoryGeneratorService(
                        ai_client=text_client,
                        prompt_builder=prompt_builder,
                        character_extractor=character_extractor
                    )
                except ValueError as e:
                    print(f"[STORY ROUTES ASYNC] Failed to create custom client: {e}, using default")

            # Extract characters
            characters = run_async(story_generator.extract_characters_from_story(
                pages,
                full_story_text
            ))

            print(f"[STORY ROUTES ASYNC] Extracted {len(characters)} characters")

            # Save characters to project if project_id is provided
            if project_id:
                try:
                    project_repo = app.config['REPOSITORIES']['project']
                    project = project_repo.get(project_id)
                    if project:
                        # Update story characters
                        project.story.characters = characters
                        project.character_profiles = list(characters)
                        project.updated_at = datetime.now()
                        project_repo.update(project_id, project)
                        print(f"[STORY ROUTES ASYNC] Saved characters to project: {project_id}")
                except Exception as e:
                    print(f"[STORY ROUTES ASYNC] Failed to save characters to project: {e}")

            # Build response
            result = {
                'characters': [
                    {
                        'name': char.name,
                        'species': char.species,
                        'physical_description': char.physical_description,
                        'clothing': char.clothing,
                        'distinctive_features': char.distinctive_features,
                        'personality_traits': char.personality_traits
                    }
                    for char in characters
                ]
            }

            _character_extraction_tasks[task_id]['status'] = 'completed'
            _character_extraction_tasks[task_id]['result'] = result
            _character_extraction_tasks[task_id]['completed_at'] = datetime.now().isoformat()

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[STORY ROUTES ASYNC] Character extraction error: {e}\n{error_details}")
            _character_extraction_tasks[task_id]['status'] = 'error'
            _character_extraction_tasks[task_id]['error'] = str(e)
            _character_extraction_tasks[task_id]['completed_at'] = datetime.now().isoformat()


@story_bp.route('/extract-characters/async', methods=['POST'])
def extract_characters_async():
    """
    POST /api/stories/extract-characters/async - Start character extraction in background

    Returns immediately with a task_id that can be polled for status.

    Request body:
    {
        "pages": [...],
        "text_model": str (optional),
        "project_id": str (optional) - If provided, saves characters to the project
    }

    Returns:
        202: Extraction started, returns task_id
        400: Invalid request
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        try:
            data = request.get_json()
        except BadRequest:
            return jsonify({'error': 'Invalid JSON'}), 400

        if 'pages' not in data or not data['pages']:
            return jsonify({'error': 'Missing required field: pages'}), 400

        # Generate task ID
        task_id = str(uuid.uuid4())

        # Get app config
        app_config = current_app.config['APP_CONFIG']

        # Store task info
        _character_extraction_tasks[task_id] = {
            'status': 'pending',
            'result': None,
            'error': None,
            'created_at': datetime.now().isoformat(),
            'completed_at': None
        }

        # Start background thread
        app = current_app._get_current_object()
        thread = threading.Thread(
            target=_run_character_extraction_in_background,
            args=(task_id, app, data, app_config)
        )
        thread.daemon = True
        thread.start()

        print(f"[STORY ROUTES] Started async character extraction task: {task_id}")

        return jsonify({
            'task_id': task_id,
            'status': 'pending',
            'message': 'Character extraction started'
        }), 202

    except Exception as e:
        return jsonify({'error': f'Failed to start character extraction: {str(e)}'}), 500


@story_bp.route('/extract-characters/status/<task_id>', methods=['GET'])
def get_character_extraction_status(task_id):
    """
    GET /api/stories/extract-characters/status/<task_id> - Check character extraction status

    Returns:
        200: Status info (pending, running, completed, error)
        404: Task not found
    """
    if task_id not in _character_extraction_tasks:
        return jsonify({'error': 'Task not found'}), 404

    task = _character_extraction_tasks[task_id]

    response = {
        'task_id': task_id,
        'status': task['status'],
        'created_at': task['created_at'],
        'completed_at': task['completed_at']
    }

    if task['status'] == 'completed':
        response['result'] = task['result']
    elif task['status'] == 'error':
        response['error'] = task['error']

    return jsonify(response), 200


@story_bp.route('/<story_id>', methods=['GET'])
def get_story(story_id):
    """
    GET /api/stories/:id - Retrieve a story by ID

    Returns:
        200: Story found
        404: Story not found
        500: Server error
    """
    try:
        # Get config repository
        config_repo = current_app.config['REPOSITORIES']['config']

        # Retrieve story metadata (synchronous method)
        metadata = config_repo.get(story_id)

        if metadata is None:
            return jsonify({'error': 'Story not found'}), 404

        # Return story data
        return jsonify({
            'id': story_id,
            'metadata': {
                'title': metadata.title,
                'language': metadata.language,
                'complexity': metadata.complexity,
                'vocabulary_diversity': metadata.vocabulary_diversity,
                'age_group': metadata.age_group,
                'num_pages': metadata.num_pages,
                'words_per_page': metadata.words_per_page,
                'genre': metadata.genre,
                'art_style': metadata.art_style,
                'user_prompt': metadata.user_prompt
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error retrieving story: {e}")
        return jsonify({'error': 'Internal server error'}), 500
