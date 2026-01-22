"""
Flask application for story generator API.

This module sets up the Flask application with CORS, error handlers,
configuration loading, and dependency injection for services.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from flask_cors import CORS

from src.ai.ai_factory import AIClientFactory
from src.ai.stub_image_client import StubImageClient
from src.ai.gpt_image_client import GPTImageClient
from src.domain.character_extractor import CharacterExtractor
from src.domain.prompt_builder import PromptBuilder
from src.models.config import (
    AppConfig,
    AIProviderConfig,
    TextProvider,
    ImageProvider,
    OllamaConfig,
    OpenAIConfig,
    ClaudeConfig,
    StoryParameters,
    DefaultValues
)
from src.repositories.config_repository import ConfigRepository
from src.repositories.image_repository import ImageRepository
from src.repositories.project_repository import ProjectRepository
from src.services.story_generator import StoryGeneratorService
from src.services.image_generator import ImageGeneratorService
from src.services.project_orchestrator import ProjectOrchestrator


def load_config() -> AppConfig:
    """
    Load application configuration from JSON files.

    Loads config.json, parameters.json, and defaults.json from the
    data/config directory and creates an AppConfig instance.

    Returns:
        AppConfig with all settings loaded

    Raises:
        FileNotFoundError: If config files are missing
        ValueError: If config files are invalid
    """
    # Get project root directory
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "data" / "config"

    # Load main config
    config_path = config_dir / "config.json"
    with open(config_path, 'r') as f:
        config_data = json.load(f)

    # Load parameters
    params_path = config_dir / "parameters.json"
    with open(params_path, 'r') as f:
        params_data = json.load(f)

    # Load defaults
    defaults_path = config_dir / "defaults.json"
    with open(defaults_path, 'r') as f:
        defaults_data = json.load(f)

    # Create provider configs
    ollama_config = None
    if "ollama" in config_data:
        ollama_config = OllamaConfig(**config_data["ollama"])

    openai_config = None
    if "openai" in config_data:
        # Get API key from environment variable if not in config
        openai_data = config_data["openai"].copy()
        if not openai_data.get("api_key"):
            openai_data["api_key"] = os.getenv('OPENAI_API_KEY', '')
        openai_config = OpenAIConfig(**openai_data)

    claude_config = None
    if "claude" in config_data:
        # Get API key from environment variable if not in config
        claude_data = config_data["claude"].copy()
        if not claude_data.get("api_key"):
            claude_data["api_key"] = os.getenv('ANTHROPIC_API_KEY', '')
        claude_config = ClaudeConfig(**claude_data)

    # Create AI provider config
    ai_providers = AIProviderConfig(
        text_provider=TextProvider(config_data["text_provider"]),
        image_provider=ImageProvider(config_data["image_provider"]),
        ollama=ollama_config,
        openai=openai_config,
        claude=claude_config
    )

    # Create story parameters
    parameters = StoryParameters(**params_data)

    # Create default values
    defaults = DefaultValues(**defaults_data)

    # Create and return app config
    return AppConfig(
        ai_providers=ai_providers,
        parameters=parameters,
        defaults=defaults
    )


def create_app(config: AppConfig = None) -> Flask:
    """
    Create and configure Flask application.

    Sets up CORS, error handlers, routes, and dependency injection.

    Args:
        config: Optional AppConfig (loads from files if not provided)

    Returns:
        Configured Flask application
    """
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Load configuration
    if config is None:
        config = load_config()

    # Store config in app
    app.config['APP_CONFIG'] = config

    # Enable CORS for all routes
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Get project root for storage paths
    project_root = Path(__file__).parent.parent
    storage_dir = project_root / "data" / "storage"

    # Initialize repositories
    config_repo = ConfigRepository(storage_dir=str(storage_dir / "configs"))
    image_repo = ImageRepository(storage_dir=str(storage_dir / "images"))
    project_repo = ProjectRepository(storage_dir=str(storage_dir / "projects"))

    # Initialize AI clients
    text_client = AIClientFactory.create_text_client(config)

    # Initialize image client based on configuration
    image_provider = config.ai_providers.image_provider
    if image_provider in ["gpt-image-1", "dall-e-2", "dall-e-3"]:
        # Use OpenAI for image generation (GPT-Image or legacy DALL-E)
        if config.ai_providers.openai is None:
            print("Warning: OpenAI image model selected but OpenAI config is missing. Using stub image client.")
            image_client = StubImageClient()
        elif not config.ai_providers.openai.api_key and not os.getenv('OPENAI_API_KEY'):
            print("Warning: OpenAI image model selected but OPENAI_API_KEY not found. Using stub image client.")
            image_client = StubImageClient()
        else:
            image_client = GPTImageClient(config.ai_providers.openai, model=image_provider)
            print(f"Using {image_provider} for image generation")
    else:
        # Use stub image client for other providers or development
        print(f"Using stub image client (configured provider: {image_provider})")
        image_client = StubImageClient()

    # Initialize domain services
    prompt_builder = PromptBuilder(ai_client=text_client)
    character_extractor = CharacterExtractor(text_client)

    # Initialize service layer
    story_generator = StoryGeneratorService(
        ai_client=text_client,
        prompt_builder=prompt_builder,
        character_extractor=character_extractor
    )

    # Image generator with stub client
    image_generator = ImageGeneratorService(
        image_client=image_client,
        prompt_builder=prompt_builder
    )

    # Project orchestrator with all services
    project_orchestrator = ProjectOrchestrator(
        story_generator=story_generator,
        image_generator=image_generator,
        project_repository=project_repo
    )

    # Store services in app context for route access
    app.config['REPOSITORIES'] = {
        'config': config_repo,
        'image': image_repo,
        'project': project_repo
    }

    app.config['SERVICES'] = {
        'story_generator': story_generator,
        'image_generator': image_generator,
        'project_orchestrator': project_orchestrator,
        'image_client': image_client
    }

    # Store prompt builder for prompt generation API
    app.config['PROMPT_BUILDER'] = prompt_builder

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors"""
        return jsonify({'error': 'Bad request'}), 400

    # Main web interface route
    @app.route('/', methods=['GET'])
    def index():
        """Serve the main web interface"""
        return render_template('index.html')

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'text_provider': config.ai_providers.text_provider.value
        })

    # Register route blueprints
    from src.routes.story_routes import story_bp
    from src.routes.project_routes import project_bp
    from src.routes.config_routes import config_bp
    from src.routes.image_routes import image_bp
    from src.routes.prompt_routes import prompt_bp
    from src.routes.visual_consistency_routes import visual_bp

    app.register_blueprint(story_bp, url_prefix='/api/stories')
    app.register_blueprint(project_bp, url_prefix='/api/projects')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(image_bp, url_prefix='/api/images')
    app.register_blueprint(prompt_bp, url_prefix='/api/prompts')
    app.register_blueprint(visual_bp, url_prefix='/api/visual-consistency')

    return app


if __name__ == '__main__':
    """Run the Flask development server"""
    app = create_app()

    # Get port from environment variable, default to 5001 (5000 often conflicts with AirPlay on macOS)
    port = int(os.getenv('FLASK_PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() in ('true', '1', 'yes')

    print(f"Starting Flask app on port {port}...")
    app.run(debug=debug, host='0.0.0.0', port=port)
