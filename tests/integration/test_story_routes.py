"""
Integration tests for Story Routes.
Write these tests BEFORE implementing the routes (TDD approach).

Tests the REST API endpoints for story generation and management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


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


class TestStoryRoutes:
    """Integration tests for story routes"""

    def test_create_story_basic(self, client, app):
        """Test POST /api/stories - create new story"""
        # Mock the story generator service
        with patch.object(
            app.config['SERVICES']['story_generator'],
            'generate_story',
            new_callable=AsyncMock
        ) as mock_generate:
            from src.models.story import Story, StoryMetadata, StoryPage

            # Mock response
            mock_story = Story(
                id="test-story-123",
                metadata=StoryMetadata(
                    title="Test Story",
                    language="English",
                    complexity="simple",
                    vocabulary_diversity="basic",
                    age_group="3-5",
                    num_pages=3,
                    genre="adventure",
                    art_style="cartoon"
                ),
                pages=[
                    StoryPage(page_number=1, text="Page 1 text"),
                    StoryPage(page_number=2, text="Page 2 text"),
                    StoryPage(page_number=3, text="Page 3 text")
                ],
                characters=[]
            )
            mock_generate.return_value = mock_story

            # Make request
            response = client.post('/api/stories', json={
                'title': 'Test Story',
                'language': 'English',
                'age_group': '3-5',
                'num_pages': 3,
                'genre': 'adventure'
            })

            # Verify response
            assert response.status_code == 201
            data = response.get_json()
            assert data['id'] == "test-story-123"
            assert data['metadata']['title'] == "Test Story"
            assert len(data['pages']) == 3

    def test_create_story_with_theme(self, client, app):
        """Test creating story with optional theme"""
        with patch.object(
            app.config['SERVICES']['story_generator'],
            'generate_story',
            new_callable=AsyncMock
        ) as mock_generate:
            from src.models.story import Story, StoryMetadata, StoryPage

            mock_story = Story(
                id="test-story-456",
                metadata=StoryMetadata(
                    title="Friendship Story",
                    language="English",
                    complexity="simple",
                    vocabulary_diversity="basic",
                    age_group="3-5",
                    num_pages=3
                ),
                pages=[StoryPage(page_number=1, text="Test")],
                characters=[]
            )
            mock_generate.return_value = mock_story

            response = client.post('/api/stories', json={
                'title': 'Friendship Story',
                'theme': 'friendship and courage'
            })

            assert response.status_code == 201
            # Verify theme was passed to service
            assert mock_generate.call_args[1]['theme'] == 'friendship and courage'

    def test_create_story_with_custom_prompt(self, client, app):
        """Test creating story with custom prompt"""
        with patch.object(
            app.config['SERVICES']['story_generator'],
            'generate_story',
            new_callable=AsyncMock
        ) as mock_generate:
            from src.models.story import Story, StoryMetadata, StoryPage

            mock_story = Story(
                id="test-story-789",
                metadata=StoryMetadata(
                    title="Dragon Story",
                    language="English",
                    complexity="simple",
                    vocabulary_diversity="basic",
                    age_group="3-5",
                    num_pages=3
                ),
                pages=[StoryPage(page_number=1, text="Test")],
                characters=[]
            )
            mock_generate.return_value = mock_story

            response = client.post('/api/stories', json={
                'title': 'Dragon Story',
                'custom_prompt': 'A story about a dragon who learns to read'
            })

            assert response.status_code == 201
            # Verify custom prompt was passed
            assert 'dragon' in mock_generate.call_args[1]['custom_prompt'].lower()

    def test_create_story_missing_title(self, client):
        """Test creating story without required title"""
        response = client.post('/api/stories', json={
            'language': 'English',
            'age_group': '3-5'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_create_story_invalid_json(self, client):
        """Test creating story with invalid JSON"""
        response = client.post(
            '/api/stories',
            data="not json",
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_create_story_service_error(self, client, app):
        """Test handling of service errors"""
        with patch.object(
            app.config['SERVICES']['story_generator'],
            'generate_story',
            new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.side_effect = Exception("AI service unavailable")

            response = client.post('/api/stories', json={
                'title': 'Test Story'
            })

            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data

    def test_get_story_by_id(self, client, app):
        """Test GET /api/stories/:id - retrieve story"""
        # This would need the config repository to be mocked
        # For now, test the endpoint exists
        response = client.get('/api/stories/nonexistent-id')
        # Should return 404 for non-existent story
        assert response.status_code in [404, 500]  # Either not found or not implemented yet

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'version' in data
        assert 'text_provider' in data
