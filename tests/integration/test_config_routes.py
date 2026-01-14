"""
Integration tests for Config Routes.
Write these tests BEFORE implementing the routes (TDD approach).

Tests the REST API endpoints for configuration management.
"""

import pytest
from unittest.mock import patch


@pytest.fixture
def app():
    """Create Flask app for testing"""
    from src.app import create_app
    from src.models.config import (
        AppConfig, AIProviderConfig, TextProvider, ImageProvider,
        OllamaConfig, StoryParameters, DefaultValues
    )

    # Create test config
    test_config = AppConfig(
        ai_providers=AIProviderConfig(
            text_provider=TextProvider.OLLAMA,
            image_provider=ImageProvider.DALLE3,
            ollama=OllamaConfig(
                base_url="http://localhost:11434",
                model="test-model",
                timeout=60
            )
        ),
        parameters=StoryParameters(
            languages=["English", "Spanish"],
            complexities=["simple", "intermediate"],
            vocabulary_levels=["basic", "advanced"],
            age_groups=["3-5", "6-8"],
            page_counts=[3, 5, 8],
            genres=["adventure", "fantasy"],
            art_styles=["cartoon", "watercolor"]
        ),
        defaults=DefaultValues(
            language="English",
            complexity="simple",
            vocabulary_diversity="basic",
            age_group="3-5",
            num_pages=5,
            genre="adventure",
            art_style="cartoon"
        )
    )

    app = create_app(config=test_config)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestConfigRoutes:
    """Integration tests for config routes"""

    def test_get_config(self, client, app):
        """Test GET /api/config - retrieve application configuration"""
        response = client.get('/api/config')

        assert response.status_code == 200
        data = response.get_json()

        # Verify AI providers config
        assert 'ai_providers' in data
        assert data['ai_providers']['text_provider'] == 'ollama'
        assert data['ai_providers']['image_provider'] == 'dall-e-3'

        # Verify parameters
        assert 'parameters' in data
        assert 'English' in data['parameters']['languages']
        assert 'Spanish' in data['parameters']['languages']
        assert 'adventure' in data['parameters']['genres']

        # Verify defaults
        assert 'defaults' in data
        assert data['defaults']['language'] == 'English'
        assert data['defaults']['num_pages'] == 5

    def test_get_parameters(self, client, app):
        """Test GET /api/config/parameters - get story parameters"""
        response = client.get('/api/config/parameters')

        assert response.status_code == 200
        data = response.get_json()

        assert 'languages' in data
        assert 'complexities' in data
        assert 'vocabulary_levels' in data
        assert 'age_groups' in data
        assert 'page_counts' in data
        assert 'genres' in data
        assert 'art_styles' in data

        assert data['languages'] == ["English", "Spanish"]
        assert data['page_counts'] == [3, 5, 8]

    def test_get_defaults(self, client, app):
        """Test GET /api/config/defaults - get default values"""
        response = client.get('/api/config/defaults')

        assert response.status_code == 200
        data = response.get_json()

        assert data['language'] == 'English'
        assert data['complexity'] == 'simple'
        assert data['vocabulary_diversity'] == 'basic'
        assert data['age_group'] == '3-5'
        assert data['num_pages'] == 5
        assert data['genre'] == 'adventure'
        assert data['art_style'] == 'cartoon'

    def test_get_ai_providers(self, client, app):
        """Test GET /api/config/ai-providers - get AI provider configuration"""
        response = client.get('/api/config/ai-providers')

        assert response.status_code == 200
        data = response.get_json()

        assert data['text_provider'] == 'ollama'
        assert data['image_provider'] == 'dall-e-3'
        assert 'ollama' in data
        assert data['ollama']['base_url'] == 'http://localhost:11434'
        assert data['ollama']['model'] == 'test-model'
