"""
Project Routes for REST API.

Handles endpoints for project management (save, load, list, delete).
"""

import io
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.exceptions import BadRequest
from datetime import datetime

from src.models.project import Project, ProjectStatus
from src.models.story import Story, StoryMetadata, StoryPage, PDFOptions, CoverPage
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

        # Parse PDF options if present
        pdf_options = None
        if story_data.get('pdf_options') is not None:
            pdf_opts_data = story_data['pdf_options']
            pdf_options = PDFOptions(
                font=pdf_opts_data.get('font', 'Helvetica'),
                font_size=pdf_opts_data.get('font_size', 12),
                layout=pdf_opts_data.get('layout', 'portrait'),
                page_size=pdf_opts_data.get('page_size', 'letter'),
                image_placement=pdf_opts_data.get('image_placement', 'top'),
                image_size=pdf_opts_data.get('image_size', 'medium'),
                include_title_page=pdf_opts_data.get('include_title_page', True),
                show_page_numbers=pdf_opts_data.get('show_page_numbers', True)
            )

        # Parse cover page if present
        cover_page = None
        if story_data.get('cover_page') is not None:
            cover_page_data = story_data['cover_page']
            cover_page = CoverPage(
                image_prompt=cover_page_data.get('image_prompt'),
                image_url=cover_page_data.get('image_url'),
                local_image_path=cover_page_data.get('local_image_path')
            )

        # Create Story object
        story = Story(
            id=story_data.get('id', ''),
            metadata=metadata,
            pages=pages,
            characters=characters,
            art_bible=art_bible,
            character_references=character_references if character_references else None,
            cover_page=cover_page,
            image_session_id=story_data.get('image_session_id'),
            pdf_options=pdf_options,
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
                'cover_page': {
                    'image_prompt': project.story.cover_page.image_prompt,
                    'image_url': project.story.cover_page.image_url,
                    'local_image_path': project.story.cover_page.local_image_path
                } if project.story.cover_page else None,
                'image_session_id': project.story.image_session_id,
                'pdf_options': {
                    'font': project.story.pdf_options.font,
                    'font_size': project.story.pdf_options.font_size,
                    'layout': project.story.pdf_options.layout,
                    'page_size': project.story.pdf_options.page_size,
                    'image_placement': project.story.pdf_options.image_placement,
                    'image_size': project.story.pdf_options.image_size,
                    'include_title_page': project.story.pdf_options.include_title_page,
                    'show_page_numbers': project.story.pdf_options.show_page_numbers
                } if project.story.pdf_options else None,
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


@project_bp.route('/<project_id>/rename', methods=['PUT'])
def rename_project(project_id):
    """
    PUT /api/projects/:id/rename - Rename a project

    Request body:
    {
        "name": str (required)
    }

    Returns:
        200: Project renamed successfully
        400: Invalid request
        404: Project not found
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
        if 'name' not in data or not data['name'].strip():
            return jsonify({'error': 'Missing required field: name'}), 400

        new_name = data['name'].strip()

        # Get project repository
        project_repo = current_app.config['REPOSITORIES']['project']

        # Get existing project
        project = project_repo.get(project_id)
        if project is None:
            return jsonify({'error': 'Project not found'}), 404

        # Update the project name
        project.name = new_name
        project.updated_at = datetime.now()

        # Also update the story title to match
        project.story.metadata = StoryMetadata(
            title=new_name,
            language=project.story.metadata.language,
            complexity=project.story.metadata.complexity,
            vocabulary_diversity=project.story.metadata.vocabulary_diversity,
            age_group=project.story.metadata.age_group,
            num_pages=project.story.metadata.num_pages,
            genre=project.story.metadata.genre,
            art_style=project.story.metadata.art_style,
            user_prompt=project.story.metadata.user_prompt,
            words_per_page=project.story.metadata.words_per_page
        )

        # Save the updated project
        project_repo.update(project_id, project)

        return jsonify({
            'id': project_id,
            'name': new_name,
            'message': 'Project renamed successfully'
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error renaming project: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@project_bp.route('/<project_id>/pdf', methods=['POST'])
def generate_pdf(project_id):
    """
    POST /api/projects/:id/pdf - Generate a PDF for a project

    Request body:
    {
        "font": str (optional, default "Helvetica"),
        "font_size": int (optional, default 12),
        "layout": str (optional, "portrait" or "landscape"),
        "page_size": str (optional, "letter", "a4", "a5"),
        "image_placement": str (optional, "top", "bottom", "left", "right", "inner", "outer"),
        "image_size": str (optional, "small", "medium", "large", "full"),
        "include_title_page": bool (optional, default True),
        "show_page_numbers": bool (optional, default True)
    }

    Returns:
        200: PDF generated successfully with download URL
        404: Project not found
        500: Server error
    """
    try:
        # Import reportlab components
        from reportlab.lib.pagesizes import letter, A4, A5, landscape
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
        from reportlab.lib import colors
        from src.utils.font_manager import get_font_manager

        # Get project repository
        project_repo = current_app.config['REPOSITORIES']['project']

        # Retrieve project
        project = project_repo.get(project_id)
        if project is None:
            return jsonify({'error': 'Project not found'}), 404

        # Get PDF options from request
        data = request.get_json() or {}
        pdf_mode = data.get('pdf_mode', 'text-next-to-image')
        requested_font = data.get('font', 'Helvetica')
        font_size = int(data.get('font_size', 12))
        font_color_str = data.get('font_color', 'black')

        # Get font manager and ensure font is available
        font_manager = get_font_manager()
        font = font_manager.ensure_font_available(requested_font)
        layout = data.get('layout', 'portrait')
        page_size_str = data.get('page_size', 'letter')
        image_placement = data.get('image_placement', 'top')
        image_size_str = data.get('image_size', 'medium')
        text_placement = data.get('text_placement', 'top-left')
        include_title_page = data.get('include_title_page', True)
        show_page_numbers = data.get('show_page_numbers', True)

        # Get cover-specific options (defaults to page options if not specified)
        cover_font_requested = data.get('cover_font', requested_font)
        cover_font = font_manager.ensure_font_available(cover_font_requested)
        cover_font_size = int(data.get('cover_font_size', font_size))
        cover_font_color_str = data.get('cover_font_color', font_color_str)
        cover_text_placement = data.get('cover_text_placement', text_placement)

        # Map font colors
        font_color_map = {
            'black': colors.black,
            'white': colors.white,
            'dark-gray': colors.Color(0.3, 0.3, 0.3),
            'navy': colors.Color(0, 0, 0.5),
            'dark-green': colors.Color(0, 0.4, 0),
            'dark-red': colors.Color(0.6, 0, 0)
        }
        font_color = font_color_map.get(font_color_str, colors.black)
        cover_font_color = font_color_map.get(cover_font_color_str, colors.black)

        # Determine page size
        page_size_map = {
            'letter': letter,
            'a4': A4,
            'a5': A5
        }
        page_size = page_size_map.get(page_size_str.lower(), letter)

        # Apply landscape if requested
        if layout == 'landscape':
            page_size = landscape(page_size)

        # Get story
        story = project.story

        # For text-over-image mode, use the actual image dimensions as page size
        if pdf_mode == 'text-over-image':
            # Get the first page's image to determine dimensions
            if story.pages and story.pages[0].local_image_path:
                images_dir = project_repo.images_dir
                img_path = story.pages[0].local_image_path
                if img_path.startswith('images/'):
                    img_path = img_path[7:]
                full_img_path = images_dir / img_path

                if full_img_path.exists():
                    try:
                        # Load the image to get its dimensions
                        from PIL import Image as PILImage
                        with PILImage.open(str(full_img_path)) as pil_img:
                            # Get image dimensions in pixels
                            img_width_px, img_height_px = pil_img.size
                            # Convert to points (1 inch = 72 points, assume 72 DPI)
                            page_size = (img_width_px, img_height_px)
                            current_app.logger.info(f"Using image dimensions as page size: {img_width_px}x{img_height_px} points")
                    except Exception as e:
                        current_app.logger.warning(f"Could not read image dimensions: {e}. Using default page size.")

        # Create PDF buffer
        pdf_buffer = io.BytesIO()

        # Create the PDF document using BaseDocTemplate for both modes
        doc = BaseDocTemplate(
            pdf_buffer,
            pagesize=page_size
        )

        # Create frame based on mode
        if pdf_mode == 'text-over-image':
            # Frame with absolutely no padding for full bleed
            frame = Frame(
                0, 0,  # x1, y1 (bottom-left corner)
                page_size[0], page_size[1],  # width, height (full page)
                leftPadding=0,
                rightPadding=0,
                topPadding=0,
                bottomPadding=0
            )
        else:
            # Standard frame with margins
            margin = 0.75 * inch
            frame = Frame(
                margin, margin,  # x1, y1
                page_size[0] - 2 * margin, page_size[1] - 2 * margin,  # width, height
                leftPadding=0,
                rightPadding=0,
                topPadding=0,
                bottomPadding=0
            )

        # Create page template with the frame and page number callback
        page_template = PageTemplate(
            id='MainTemplate',
            frames=[frame],
            onPage=lambda canvas, doc: add_page_number(canvas, doc)
        )
        doc.addPageTemplates([page_template])

        # Create styles
        styles = getSampleStyleSheet()

        # Custom title style (uses cover-specific options)
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=cover_font,
            fontSize=cover_font_size * 2,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=cover_font_color
        )

        # Custom body style with font color
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontName=font,
            fontSize=font_size,
            leading=font_size * 1.5,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            textColor=font_color
        )

        # Custom page number style
        page_num_style = ParagraphStyle(
            'PageNum',
            parent=styles['Normal'],
            fontName=font,
            fontSize=font_size - 2,
            alignment=TA_CENTER,
            textColor=font_color
        )

        # Page numbering callback - tracks current page for story pages
        page_counter = {'current': 0, 'title_pages': 1 if include_title_page else 0}

        # Dictionary to store background images for text-over-image mode
        # Maps story page number to image path
        page_background_images = {}

        def add_page_number(canvas, doc):
            """Add background image (if text-over-image mode) and page number at bottom center."""
            # Draw background image if in text-over-image mode
            if pdf_mode == 'text-over-image':
                current_page = canvas.getPageNumber()
                story_page_num = current_page - page_counter['title_pages']

                # Handle title page (page 1) - use key 0 for cover background
                if current_page == 1 and 0 in page_background_images:
                    img_path = page_background_images[0]
                    try:
                        canvas.drawImage(img_path, 0, 0,
                                       width=page_size[0],
                                       height=page_size[1],
                                       preserveAspectRatio=False)
                    except Exception as e:
                        current_app.logger.warning(f"Could not draw cover background image: {e}")
                # Handle story pages
                elif story_page_num > 0 and story_page_num in page_background_images:
                    img_path = page_background_images[story_page_num]
                    try:
                        # Draw image at full page size with no margins
                        canvas.drawImage(img_path, 0, 0,
                                       width=page_size[0],
                                       height=page_size[1],
                                       preserveAspectRatio=False)
                    except Exception as e:
                        current_app.logger.warning(f"Could not draw background image: {e}")

            # Add page number
            if not show_page_numbers:
                return

            # Calculate actual story page number (excluding title page)
            page_num = canvas.getPageNumber()
            if page_num <= page_counter['title_pages']:
                # Don't show page numbers on title page
                return

            story_page_num = page_num - page_counter['title_pages']

            # Draw page number at bottom center
            canvas.saveState()
            canvas.setFont(font, font_size - 2)

            # Set font color
            if font_color_str == 'white':
                canvas.setFillColor(colors.white)
            elif font_color_str == 'dark-gray':
                canvas.setFillColor(colors.Color(0.3, 0.3, 0.3))
            elif font_color_str == 'navy':
                canvas.setFillColor(colors.Color(0, 0, 0.5))
            elif font_color_str == 'dark-green':
                canvas.setFillColor(colors.Color(0, 0.4, 0))
            elif font_color_str == 'dark-red':
                canvas.setFillColor(colors.Color(0.6, 0, 0))
            else:
                canvas.setFillColor(colors.black)

            # Position at bottom center
            text = f"— {story_page_num} —"
            text_width = canvas.stringWidth(text, font, font_size - 2)
            x = (page_size[0] - text_width) / 2
            y = 0.5 * inch  # Half inch from bottom

            canvas.drawString(x, y, text)
            canvas.restoreState()

        # Build story content
        story_content = []

        # Calculate image dimensions based on image_size setting
        if pdf_mode == 'text-over-image':
            # Full page size with no margins
            page_width = page_size[0]
            page_height = page_size[1]
        else:
            # Account for margins in text-next-to-image mode
            page_width = page_size[0] - 1.5 * inch
            page_height = page_size[1] - 1.5 * inch

        # Image size map: (width_scale, height_scale)
        image_size_map = {
            'small': (0.30, 0.25),     # 30% width, 25% height
            'medium': (0.45, 0.40),    # 45% width, 40% height
            'large': (0.60, 0.55),     # 60% width, 55% height
            'xlarge': (0.75, 0.70),    # 75% width, 70% height
            'full': (0.90, 0.85)       # 90% width, 85% height
        }
        image_scales = image_size_map.get(image_size_str, (0.45, 0.40))
        image_width_scale = image_scales[0]
        image_height_scale = image_scales[1]

        # Title page
        if include_title_page:
            # Determine which image to use for the cover:
            # 1. Prefer cover page image if available
            # 2. Fall back to art bible image
            cover_image_path = None
            full_cover_img_path = None

            if story.cover_page and story.cover_page.local_image_path:
                cover_image_path = story.cover_page.local_image_path
                current_app.logger.info("Using cover page image for title page")
            elif story.art_bible and story.art_bible.local_image_path:
                cover_image_path = story.art_bible.local_image_path
                current_app.logger.info("Using art bible image for title page (no cover available)")

            if cover_image_path:
                images_dir = project_repo.images_dir
                img_path = cover_image_path
                if img_path.startswith('images/'):
                    img_path = img_path[7:]
                full_cover_img_path = images_dir / img_path

            # Handle differently based on PDF mode
            if pdf_mode == 'text-over-image' and full_cover_img_path and full_cover_img_path.exists():
                # TEXT-OVER-IMAGE MODE: Use cover as background, overlay title
                page_background_images[0] = str(full_cover_img_path)

                # Create title style for overlay
                title_overlay_style = ParagraphStyle(
                    'TitleOverlay',
                    parent=title_style,
                    fontName=cover_font,
                    fontSize=cover_font_size * 2,
                    textColor=cover_font_color,
                    alignment=TA_CENTER,
                    leftIndent=40,
                    rightIndent=40
                )

                title_para = Paragraph(story.metadata.title, title_overlay_style)
                text_padding = 40

                # Position title based on cover_text_placement
                if cover_text_placement in ['top-left', 'top-right']:
                    # Title at top
                    story_content.append(Spacer(1, text_padding))
                    story_content.append(title_para)
                else:  # bottom-left, bottom-right
                    # Title at bottom - push title down 75% of page height
                    # (title is short, so we want it near bottom, not leaving room for long text)
                    bottom_spacer = page_height * 0.75
                    story_content.append(Spacer(1, bottom_spacer))
                    story_content.append(title_para)

                story_content.append(PageBreak())
            else:
                # TEXT-NEXT-TO-IMAGE MODE: Standard layout
                story_content.append(Spacer(1, 2 * inch))
                story_content.append(Paragraph(story.metadata.title, title_style))
                story_content.append(Spacer(1, 0.5 * inch))

                if full_cover_img_path and full_cover_img_path.exists():
                    try:
                        img = Image(str(full_cover_img_path))
                        cover_image_scale = 0.7 if story.cover_page else 0.5
                        img_width = min(page_width * cover_image_scale, img.drawWidth)
                        scale = img_width / img.drawWidth
                        img.drawWidth = img_width
                        img.drawHeight = img.drawHeight * scale
                        story_content.append(img)
                    except Exception as e:
                        current_app.logger.warning(f"Could not add cover/art bible image: {e}")

                story_content.append(PageBreak())

        # Story pages
        for page in story.pages:
            page_elements = []

            # Get page image if available
            page_image = None
            full_img_path = None
            if page.local_image_path:
                images_dir = project_repo.images_dir
                img_path = page.local_image_path
                if img_path.startswith('images/'):
                    img_path = img_path[7:]
                full_img_path = images_dir / img_path

                if full_img_path.exists():
                    try:
                        page_image = Image(str(full_img_path))
                        # Image will be scaled after we determine placement
                    except Exception as e:
                        current_app.logger.warning(f"Could not add page image: {e}")
                        page_image = None

            # Create text paragraph
            text_para = Paragraph(page.text, body_style)

            # Handle different image placements
            if page_image:
                # Check if this is text-over-image mode
                if image_placement == 'background':
                    # TEXT-OVER-IMAGE MODE: Store background image, add only text flowables
                    # Store the image path for drawing in onPage callback
                    if full_img_path:
                        story_page_num = page.page_number
                        page_background_images[story_page_num] = str(full_img_path)

                        # Create a special style for text-over-image
                        text_overlay_style = ParagraphStyle(
                            'TextOverlay',
                            parent=body_style,
                            fontName=font,
                            fontSize=font_size,
                            leading=font_size * 1.5,
                            textColor=font_color,
                            alignment=TA_LEFT,
                            leftIndent=40,
                            rightIndent=40
                        )

                        # Create text paragraph with overlay style
                        text_overlay = Paragraph(page.text, text_overlay_style)

                        # Position text using spacers based on text_placement
                        # We need to position the text in the correct corner of the page
                        text_padding = 40  # Padding from edges

                        # Allow text to use up to 80% of the page height
                        # For bottom positions, the spacer should only take 20% max
                        max_spacer_for_bottom = page_height * 0.20  # 20% for spacer, 80% for text

                        if text_placement == 'top-left':
                            # Add small top spacer, text will be left-aligned
                            page_elements.append(Spacer(1, text_padding))
                            page_elements.append(text_overlay)
                        elif text_placement == 'top-right':
                            # Add small top spacer, use right-aligned style
                            right_aligned_style = ParagraphStyle(
                                'TextOverlayRight',
                                parent=text_overlay_style,
                                alignment=TA_LEFT,  # Will use table for right positioning
                            )
                            text_overlay_right = Paragraph(page.text, right_aligned_style)
                            page_elements.append(Spacer(1, text_padding))
                            # Use table to right-align
                            table = Table([['', text_overlay_right]], colWidths=[page_width/2, page_width/2])
                            table.setStyle(TableStyle([
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                            ]))
                            page_elements.append(table)
                        elif text_placement == 'bottom-left':
                            # Add spacer to push text toward bottom
                            # Use only 20% for spacer, leaving 80% for text
                            page_elements.append(Spacer(1, max_spacer_for_bottom))
                            page_elements.append(text_overlay)
                        else:  # bottom-right
                            # Add spacer to push text toward bottom, use right alignment
                            right_aligned_style = ParagraphStyle(
                                'TextOverlayBottomRight',
                                parent=text_overlay_style,
                                alignment=TA_LEFT,
                            )
                            text_overlay_right = Paragraph(page.text, right_aligned_style)
                            # Use only 20% for spacer, leaving 80% for text
                            page_elements.append(Spacer(1, max_spacer_for_bottom))
                            # Use table to right-align
                            table = Table([['', text_overlay_right]], colWidths=[page_width/2, page_width/2])
                            table.setStyle(TableStyle([
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                            ]))
                            page_elements.append(table)

                else:
                    # TEXT-NEXT-TO-IMAGE MODE: Standard image placement
                    # Determine actual placement for inner/outer
                    actual_placement = image_placement
                    if image_placement == 'inner':
                        # Inner: left on even pages, right on odd pages
                        actual_placement = 'left' if page.page_number % 2 == 0 else 'right'
                    elif image_placement == 'outer':
                        # Outer: right on even pages, left on odd pages
                        actual_placement = 'right' if page.page_number % 2 == 0 else 'left'

                    # Scale image based on placement type
                    if actual_placement in ['left', 'right']:
                        # For side-by-side layouts, limit image to 50% of page width max
                        # and ensure it fits within page height
                        max_img_width = min(page_width * 0.5, page_width * image_width_scale * 0.65)
                        max_img_height = page_height * 0.7  # Conservative height for side-by-side
                        scale = min(max_img_width / page_image.drawWidth,
                                    max_img_height / page_image.drawHeight)
                        page_image.drawWidth = page_image.drawWidth * scale
                        page_image.drawHeight = page_image.drawHeight * scale
                    else:
                        # For top/bottom layouts, use full width/height scales
                        max_img_width = page_width * image_width_scale
                        max_img_height = page_height * image_height_scale
                        scale = min(max_img_width / page_image.drawWidth,
                                    max_img_height / page_image.drawHeight)
                        page_image.drawWidth = page_image.drawWidth * scale
                        page_image.drawHeight = page_image.drawHeight * scale

                    if actual_placement == 'top':
                        page_elements.append(page_image)
                        page_elements.append(Spacer(1, 20))
                        page_elements.append(text_para)
                    elif actual_placement == 'bottom':
                        page_elements.append(text_para)
                        page_elements.append(Spacer(1, 20))
                        page_elements.append(page_image)
                    elif actual_placement == 'left':
                        # Create table with image on left, text on right
                        # Ensure column widths don't exceed page width
                        spacing = 0.2 * inch  # Reduced spacing between columns
                        img_col_width = page_image.drawWidth
                        text_col_width = page_width - img_col_width - spacing

                        # Safety check: ensure text column has minimum width
                        if text_col_width < 2 * inch:
                            # Image is too wide, scale it down
                            target_img_width = page_width - 2 * inch - spacing
                            text_col_width = 2 * inch
                            # Only scale down, never up
                            if target_img_width < page_image.drawWidth:
                                scale_factor = target_img_width / page_image.drawWidth
                                page_image.drawWidth = target_img_width
                                page_image.drawHeight = page_image.drawHeight * scale_factor
                            img_col_width = page_image.drawWidth

                        # CRITICAL: Final safety check - ensure image height NEVER exceeds frame
                        # This must run after all width adjustments
                        if page_image.drawHeight > page_height:
                            height_scale = page_height / page_image.drawHeight
                            page_image.drawHeight = page_height
                            page_image.drawWidth = page_image.drawWidth * height_scale
                            img_col_width = page_image.drawWidth
                            text_col_width = page_width - img_col_width - spacing

                        # Absolute final check: ensure dimensions fit in frame with safety margin
                        # Use 90% to account for table cell internal spacing/overhead
                        max_safe_height = page_height * 0.90
                        if page_image.drawHeight > max_safe_height:
                            safety_scale = max_safe_height / page_image.drawHeight
                            page_image.drawHeight = max_safe_height
                            page_image.drawWidth = page_image.drawWidth * safety_scale
                            img_col_width = page_image.drawWidth
                            text_col_width = page_width - img_col_width - spacing

                        table_data = [[page_image, text_para]]
                        col_widths = [img_col_width, text_col_width]
                        table = Table(table_data, colWidths=col_widths)
                        table.setStyle(TableStyle([
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LEFTPADDING', (0, 0), (0, 0), 0),
                            ('RIGHTPADDING', (0, 0), (0, 0), 8),
                            ('LEFTPADDING', (1, 0), (1, 0), 8),
                            ('RIGHTPADDING', (1, 0), (1, 0), 0),
                        ]))
                        page_elements.append(table)
                    elif actual_placement == 'right':
                        # Create table with text on left, image on right
                        # Ensure column widths don't exceed page width
                        spacing = 0.2 * inch  # Reduced spacing between columns
                        img_col_width = page_image.drawWidth
                        text_col_width = page_width - img_col_width - spacing

                        # Safety check: ensure text column has minimum width
                        if text_col_width < 2 * inch:
                            # Image is too wide, scale it down
                            target_img_width = page_width - 2 * inch - spacing
                            text_col_width = 2 * inch
                            # Only scale down, never up
                            if target_img_width < page_image.drawWidth:
                                scale_factor = target_img_width / page_image.drawWidth
                                page_image.drawWidth = target_img_width
                                page_image.drawHeight = page_image.drawHeight * scale_factor
                            img_col_width = page_image.drawWidth

                        # CRITICAL: Final safety check - ensure image height NEVER exceeds frame
                        # This must run after all width adjustments
                        if page_image.drawHeight > page_height:
                            height_scale = page_height / page_image.drawHeight
                            page_image.drawHeight = page_height
                            page_image.drawWidth = page_image.drawWidth * height_scale
                            img_col_width = page_image.drawWidth
                            text_col_width = page_width - img_col_width - spacing

                        # Absolute final check: ensure dimensions fit in frame with safety margin
                        # Use 90% to account for table cell internal spacing/overhead
                        max_safe_height = page_height * 0.90
                        if page_image.drawHeight > max_safe_height:
                            safety_scale = max_safe_height / page_image.drawHeight
                            page_image.drawHeight = max_safe_height
                            page_image.drawWidth = page_image.drawWidth * safety_scale
                            img_col_width = page_image.drawWidth
                            text_col_width = page_width - img_col_width - spacing

                        table_data = [[text_para, page_image]]
                        col_widths = [text_col_width, img_col_width]
                        table = Table(table_data, colWidths=col_widths)
                        table.setStyle(TableStyle([
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LEFTPADDING', (0, 0), (0, 0), 0),
                            ('RIGHTPADDING', (0, 0), (0, 0), 8),
                            ('LEFTPADDING', (1, 0), (1, 0), 8),
                            ('RIGHTPADDING', (1, 0), (1, 0), 0),
                        ]))
                        page_elements.append(table)
            else:
                # No image, just add text
                page_elements.append(text_para)

            # Add all elements for this page
            story_content.extend(page_elements)

            # Add page break between pages
            story_content.append(PageBreak())

        # Build PDF - BaseDocTemplate uses onPage callback from PageTemplate
        doc.build(story_content)

        # Reset buffer position
        pdf_buffer.seek(0)

        # Save PDF to project's directory
        pdf_filename = f"{story.metadata.title.replace(' ', '_')[:30]}_story.pdf"
        pdf_dir = project_repo.get_project_images_dir(project_id)
        pdf_path = pdf_dir / pdf_filename

        with open(pdf_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())

        # Return the URL to download the PDF
        pdf_url = f"/api/projects/{project_id}/pdf/download/{pdf_filename}"

        return jsonify({
            'success': True,
            'pdf_url': pdf_url,
            'filename': pdf_filename
        }), 200

    except ImportError:
        return jsonify({'error': 'PDF generation requires reportlab. Install with: pip install reportlab'}), 500
    except Exception as e:
        current_app.logger.error(f"Error generating PDF: {e}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500


@project_bp.route('/<project_id>/pdf/download/<filename>', methods=['GET'])
def download_pdf(project_id, filename):
    """
    GET /api/projects/:id/pdf/download/:filename - Download generated PDF

    Returns:
        200: PDF file
        404: PDF not found
        500: Server error
    """
    try:
        # Get project repository
        project_repo = current_app.config['REPOSITORIES']['project']

        # Get the PDF path
        pdf_dir = project_repo.get_project_images_dir(project_id)
        pdf_path = pdf_dir / filename

        # Security check: ensure the path doesn't escape the project directory
        resolved_path = pdf_path.resolve()
        if not str(resolved_path).startswith(str(pdf_dir.resolve())):
            return jsonify({'error': 'Invalid path'}), 403

        if not pdf_path.exists():
            return jsonify({'error': 'PDF not found'}), 404

        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"Error downloading PDF: {e}")
        return jsonify({'error': f'Failed to download PDF: {str(e)}'}), 500
