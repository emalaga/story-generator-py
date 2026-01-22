"""
Project Routes for REST API.

Handles endpoints for project management (save, load, list, delete).
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest
from datetime import datetime

from src.models.project import Project, ProjectStatus
from src.models.story import Story, StoryMetadata, StoryPage
from src.models.character import CharacterProfile
from src.models.image_prompt import ImagePrompt
from src.models.art_bible import ArtBible, CharacterReference

# Create blueprint
project_bp = Blueprint('projects', __name__)


@project_bp.route('', methods=['GET'])
def list_projects():
    """
    GET /api/projects - List all projects with metadata

    Returns:
        200: List of project metadata (id, name, title, created_at, updated_at)
        500: Server error
    """
    try:
        # Get project repository
        project_repo = current_app.config['REPOSITORIES']['project']

        # Get all projects with metadata
        projects = project_repo.list_all()

        return jsonify(projects), 200

    except Exception as e:
        current_app.logger.error(f"Error listing projects: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@project_bp.route('', methods=['POST'])
def create_project():
    """
    POST /api/projects - Save a new project

    Request body:
    {
        "id": str (required),
        "name": str (required),
        "story": Story (required),
        "status": str (required),
        "character_profiles": List[CharacterProfile] (optional),
        "image_prompts": List[ImagePrompt] (optional)
    }

    Returns:
        201: Project saved successfully
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
        required_fields = ['id', 'name', 'story', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Parse story data
        story_data = data['story']

        # Parse metadata
        metadata_data = story_data.get('metadata', {})
        metadata = StoryMetadata(
            title=metadata_data.get('title', ''),
            language=metadata_data.get('language', 'English'),
            complexity=metadata_data.get('complexity', 'simple'),
            vocabulary_diversity=metadata_data.get('vocabulary_diversity', 'basic'),
            age_group=metadata_data.get('age_group', '3-5'),
            num_pages=metadata_data.get('num_pages', 5),
            genre=metadata_data.get('genre'),
            art_style=metadata_data.get('art_style'),
            user_prompt=metadata_data.get('user_prompt'),
            words_per_page=metadata_data.get('words_per_page', 50)
        )

        # Parse pages
        pages = []
        for page_data in story_data.get('pages', []):
            page = StoryPage(
                page_number=page_data.get('page_number', 1),
                text=page_data.get('text', ''),
                image_url=page_data.get('image_url'),
                image_prompt=page_data.get('image_prompt'),
                local_image_path=page_data.get('local_image_path')
            )
            pages.append(page)

        # Parse characters
        characters = []
        for char_data in story_data.get('characters', []):
            character = CharacterProfile(
                name=char_data.get('name', ''),
                species=char_data.get('species'),
                physical_description=char_data.get('physical_description'),
                clothing=char_data.get('clothing'),
                distinctive_features=char_data.get('distinctive_features'),
                personality_traits=char_data.get('personality_traits')
            )
            characters.append(character)

        # Parse art bible if present
        art_bible = None
        if story_data.get('art_bible') is not None:
            art_bible_data = story_data['art_bible']
            art_bible = ArtBible(
                prompt=art_bible_data.get('prompt', ''),
                image_url=art_bible_data.get('image_url'),
                local_image_path=art_bible_data.get('local_image_path'),
                art_style=art_bible_data.get('art_style', 'cartoon'),
                style_notes=art_bible_data.get('style_notes'),
                color_palette=art_bible_data.get('color_palette'),
                lighting_style=art_bible_data.get('lighting_style'),
                brush_technique=art_bible_data.get('brush_technique')
            )

        # Parse character references if present
        character_references = []
        for char_ref_data in story_data.get('character_references', []):
            char_ref = CharacterReference(
                character_name=char_ref_data.get('character_name', ''),
                prompt=char_ref_data.get('prompt', ''),
                image_url=char_ref_data.get('image_url'),
                local_image_path=char_ref_data.get('local_image_path'),
                species=char_ref_data.get('species'),
                physical_description=char_ref_data.get('physical_description'),
                clothing=char_ref_data.get('clothing'),
                distinctive_features=char_ref_data.get('distinctive_features')
            )
            character_references.append(char_ref)

        # Create Story object
        story = Story(
            id=story_data.get('id', ''),
            metadata=metadata,
            pages=pages,
            characters=characters,
            art_bible=art_bible,
            character_references=character_references if character_references else None,
            image_session_id=story_data.get('image_session_id'),
            vocabulary=story_data.get('vocabulary', [])
        )

        # Parse character profiles (if different from story characters)
        character_profiles = []
        for profile_data in data.get('character_profiles', []):
            profile = CharacterProfile(
                name=profile_data.get('name', ''),
                species=profile_data.get('species'),
                physical_description=profile_data.get('physical_description'),
                clothing=profile_data.get('clothing'),
                distinctive_features=profile_data.get('distinctive_features'),
                personality_traits=profile_data.get('personality_traits')
            )
            character_profiles.append(profile)

        # Parse image prompts
        image_prompts = []
        for prompt_data in data.get('image_prompts', []):
            prompt = ImagePrompt(
                page_number=prompt_data.get('page_number', 1),
                prompt_text=prompt_data.get('prompt_text', ''),
                characters=prompt_data.get('characters', []),
                scene_description=prompt_data.get('scene_description'),
                art_style=prompt_data.get('art_style')
            )
            image_prompts.append(prompt)

        # Create Project object
        project = Project(
            id=data['id'],
            name=data['name'],
            story=story,
            status=ProjectStatus(data['status']),
            character_profiles=character_profiles,
            image_prompts=image_prompts
        )

        # Get project repository and save
        project_repo = current_app.config['REPOSITORIES']['project']
        project_id = project_repo.save(project)

        # Return success response
        response = {
            'id': project_id,
            'name': project.name,
            'status': project.status.value
        }

        return jsonify(response), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error saving project: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@project_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    GET /api/projects/:id - Retrieve a project by ID

    Returns:
        200: Project found
        404: Project not found
        500: Server error
    """
    try:
        # Get project repository
        project_repo = current_app.config['REPOSITORIES']['project']

        # Retrieve project
        project = project_repo.get(project_id)

        if project is None:
            return jsonify({'error': 'Project not found'}), 404

        # Convert to JSON-serializable dict
        response = {
            'id': project.id,
            'name': project.name,
            'status': project.status.value,
            'story': {
                'id': project.story.id,
                'metadata': {
                    'title': project.story.metadata.title,
                    'language': project.story.metadata.language,
                    'complexity': project.story.metadata.complexity,
                    'vocabulary_diversity': project.story.metadata.vocabulary_diversity,
                    'age_group': project.story.metadata.age_group,
                    'num_pages': project.story.metadata.num_pages,
                    'words_per_page': project.story.metadata.words_per_page,
                    'genre': project.story.metadata.genre,
                    'art_style': project.story.metadata.art_style,
                    'user_prompt': project.story.metadata.user_prompt
                },
                'pages': [
                    {
                        'page_number': page.page_number,
                        'text': page.text,
                        'image_url': page.image_url,
                        'image_prompt': page.image_prompt,
                        'local_image_path': page.local_image_path
                    }
                    for page in project.story.pages
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
                    for char in (project.story.characters or [])
                ],
                'art_bible': {
                    'prompt': project.story.art_bible.prompt,
                    'image_url': project.story.art_bible.image_url,
                    'local_image_path': project.story.art_bible.local_image_path,
                    'art_style': project.story.art_bible.art_style,
                    'style_notes': project.story.art_bible.style_notes,
                    'color_palette': project.story.art_bible.color_palette,
                    'lighting_style': project.story.art_bible.lighting_style,
                    'brush_technique': project.story.art_bible.brush_technique
                } if project.story.art_bible else None,
                'character_references': [
                    {
                        'character_name': char_ref.character_name,
                        'prompt': char_ref.prompt,
                        'image_url': char_ref.image_url,
                        'local_image_path': char_ref.local_image_path,
                        'species': char_ref.species,
                        'physical_description': char_ref.physical_description,
                        'clothing': char_ref.clothing,
                        'distinctive_features': char_ref.distinctive_features
                    }
                    for char_ref in (project.story.character_references or [])
                ],
                'image_session_id': project.story.image_session_id,
                'vocabulary': project.story.vocabulary,
                'created_at': project.story.created_at.isoformat(),
                'updated_at': project.story.updated_at.isoformat()
            },
            'character_profiles': [
                {
                    'name': profile.name,
                    'species': profile.species,
                    'physical_description': profile.physical_description,
                    'clothing': profile.clothing,
                    'distinctive_features': profile.distinctive_features,
                    'personality_traits': profile.personality_traits
                }
                for profile in project.character_profiles
            ],
            'image_prompts': [
                {
                    'page_number': prompt.page_number,
                    'prompt_text': prompt.prompt_text,
                    'characters': prompt.characters,
                    'scene_description': prompt.scene_description,
                    'art_style': prompt.art_style
                }
                for prompt in project.image_prompts
            ],
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat()
        }

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Error retrieving project: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@project_bp.route('/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    DELETE /api/projects/:id - Delete a project

    Returns:
        204: Project deleted successfully
        404: Project not found
        500: Server error
    """
    try:
        # Get project repository
        project_repo = current_app.config['REPOSITORIES']['project']

        # Delete project
        project_repo.delete(project_id)

        return '', 204

    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error deleting project: {e}")
        return jsonify({'error': 'Internal server error'}), 500
