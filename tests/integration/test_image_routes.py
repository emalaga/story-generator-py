"""
Integration tests for Image Routes.
Write these tests BEFORE implementing the routes (TDD approach).

Tests the REST API endpoints for image generation.
"""

import pytest
from unittest.mock import AsyncMock, patch


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
            languages=["English"],
            complexities=["simple"],
            vocabulary_levels=["basic"],
            age_groups=["3-5"],
            page_counts=[3, 5, 8],
            genres=["adventure"],
            art_styles=["cartoon"]
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


class TestImageRoutes:
    """Integration tests for image routes"""

    def test_generate_images_for_story(self, client, app):
        """Test POST /api/images/stories/:id - returns guidance to use project orchestrator"""
        story_id = "test-story-123"

        response = client.post(f'/api/images/stories/{story_id}')

        # This endpoint currently returns 400 guiding users to use the project orchestrator
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'project' in data['error'].lower()

    def test_generate_image_for_single_page(self, client, app):
        """Test POST /api/images/stories/:id/pages/:page_num - generate image for one page"""
        story_id = "test-story-123"
        page_num = 1

        with patch.object(
            app.config['SERVICES']['image_generator'],
            'generate_image_for_page',
            new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = "https://example.com/image.png"

            response = client.post(
                f'/api/images/stories/{story_id}/pages/{page_num}',
                json={
                    'scene_description': 'A beautiful sunset',
                    'art_style': 'watercolor'
                }
            )

            assert response.status_code == 200
            data = response.get_json()
            assert 'image_url' in data
            assert data['image_url'] == "https://example.com/image.png"

    def test_generate_image_missing_scene_description(self, client):
        """Test POST with missing scene_description"""
        story_id = "test-story-123"
        page_num = 1

        response = client.post(
            f'/api/images/stories/{story_id}/pages/{page_num}',
            json={'art_style': 'watercolor'}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_generate_images_service_error(self, client, app):
        """Test that endpoint returns 400 suggesting to use project orchestrator"""
        story_id = "test-story-123"

        response = client.post(f'/api/images/stories/{story_id}')

        # Endpoint always returns 400 guiding users to the project orchestrator
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'project' in data['error'].lower()
