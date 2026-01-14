"""
Config Routes for REST API.

Handles endpoints for configuration management.
"""

from flask import Blueprint, jsonify, current_app

# Create blueprint
config_bp = Blueprint('config', __name__)


@config_bp.route('', methods=['GET'])
def get_config():
    """
    GET /api/config - Get complete application configuration

    Returns:
        200: Configuration retrieved successfully
        500: Server error
    """
    try:
        # Get app config
        app_config = current_app.config['APP_CONFIG']

        # Build response
        response = {
            'ai_providers': {
                'text_provider': app_config.ai_providers.text_provider.value,
                'image_provider': app_config.ai_providers.image_provider.value,
            },
            'parameters': {
                'languages': app_config.parameters.languages,
                'complexities': app_config.parameters.complexities,
                'vocabulary_levels': app_config.parameters.vocabulary_levels,
                'age_groups': app_config.parameters.age_groups,
                'page_counts': app_config.parameters.page_counts,
                'genres': app_config.parameters.genres,
                'art_styles': app_config.parameters.art_styles
            },
            'defaults': {
                'language': app_config.defaults.language,
                'complexity': app_config.defaults.complexity,
                'vocabulary_diversity': app_config.defaults.vocabulary_diversity,
                'age_group': app_config.defaults.age_group,
                'num_pages': app_config.defaults.num_pages,
                'genre': app_config.defaults.genre,
                'art_style': app_config.defaults.art_style
            }
        }

        # Add provider-specific configs if they exist
        if app_config.ai_providers.ollama:
            response['ai_providers']['ollama'] = {
                'base_url': app_config.ai_providers.ollama.base_url,
                'model': app_config.ai_providers.ollama.model,
                'timeout': app_config.ai_providers.ollama.timeout
            }

        if app_config.ai_providers.openai:
            response['ai_providers']['openai'] = {
                'text_model': app_config.ai_providers.openai.text_model,
                'image_model': app_config.ai_providers.openai.image_model,
                'timeout': app_config.ai_providers.openai.timeout
                # Note: API key is not included for security
            }

        if app_config.ai_providers.claude:
            response['ai_providers']['claude'] = {
                'model': app_config.ai_providers.claude.model,
                'timeout': app_config.ai_providers.claude.timeout
                # Note: API key is not included for security
            }

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Error retrieving config: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@config_bp.route('/parameters', methods=['GET'])
def get_parameters():
    """
    GET /api/config/parameters - Get story parameters

    Returns:
        200: Parameters retrieved successfully
        500: Server error
    """
    try:
        # Get app config
        app_config = current_app.config['APP_CONFIG']

        # Return parameters
        response = {
            'languages': app_config.parameters.languages,
            'complexities': app_config.parameters.complexities,
            'vocabulary_levels': app_config.parameters.vocabulary_levels,
            'age_groups': app_config.parameters.age_groups,
            'page_counts': app_config.parameters.page_counts,
            'genres': app_config.parameters.genres,
            'art_styles': app_config.parameters.art_styles
        }

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Error retrieving parameters: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@config_bp.route('/defaults', methods=['GET'])
def get_defaults():
    """
    GET /api/config/defaults - Get default values

    Returns:
        200: Defaults retrieved successfully
        500: Server error
    """
    try:
        # Get app config
        app_config = current_app.config['APP_CONFIG']

        # Return defaults
        response = {
            'language': app_config.defaults.language,
            'complexity': app_config.defaults.complexity,
            'vocabulary_diversity': app_config.defaults.vocabulary_diversity,
            'age_group': app_config.defaults.age_group,
            'num_pages': app_config.defaults.num_pages,
            'genre': app_config.defaults.genre,
            'art_style': app_config.defaults.art_style
        }

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Error retrieving defaults: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@config_bp.route('/ai-providers', methods=['GET'])
def get_ai_providers():
    """
    GET /api/config/ai-providers - Get AI provider configuration

    Returns:
        200: AI provider config retrieved successfully
        500: Server error
    """
    try:
        # Get app config
        app_config = current_app.config['APP_CONFIG']

        # Build response
        response = {
            'text_provider': app_config.ai_providers.text_provider.value,
            'image_provider': app_config.ai_providers.image_provider.value,
        }

        # Add provider-specific configs if they exist
        if app_config.ai_providers.ollama:
            response['ollama'] = {
                'base_url': app_config.ai_providers.ollama.base_url,
                'model': app_config.ai_providers.ollama.model,
                'timeout': app_config.ai_providers.ollama.timeout
            }

        if app_config.ai_providers.openai:
            response['openai'] = {
                'text_model': app_config.ai_providers.openai.text_model,
                'image_model': app_config.ai_providers.openai.image_model,
                'timeout': app_config.ai_providers.openai.timeout
                # Note: API key is not included for security
            }

        if app_config.ai_providers.claude:
            response['claude'] = {
                'model': app_config.ai_providers.claude.model,
                'timeout': app_config.ai_providers.claude.timeout
                # Note: API key is not included for security
            }

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Error retrieving AI providers: {e}")
        return jsonify({'error': 'Internal server error'}), 500
