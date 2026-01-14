"""
End-to-end integration test for image generation workflow.

Tests the complete image generation flow including:
- Single page image generation
- Character consistency
- Art style application
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


class TestImageGenerationFlow:
    """End-to-end tests for image generation workflow"""

    def test_generate_single_page_image(self, client, app):
        """
        Test generating an image for a single page.

        Workflow:
        1. Call image generation endpoint with scene description
        2. Verify image URL is returned
        3. Verify image prompt includes scene description and art style
        """
        story_id = "test-story-123"
        page_num = 1

        with patch.object(
            app.config['SERVICES']['image_generator'],
            'generate_image_for_page',
            new_callable=AsyncMock
        ) as mock_generate:
            # Mock successful image generation
            mock_generate.return_value = "https://example.com/generated-image.png"

            response = client.post(
                f'/api/images/stories/{story_id}/pages/{page_num}',
                json={
                    'scene_description': 'A brave fox exploring a magical forest',
                    'art_style': 'watercolor'
                }
            )

            assert response.status_code == 200
            data = response.get_json()

            # Verify response structure
            assert 'image_url' in data
            assert 'page_number' in data
            assert data['image_url'] == "https://example.com/generated-image.png"
            assert data['page_number'] == page_num

            # Verify service was called with correct parameters
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args[0][0] == 'A brave fox exploring a magical forest'  # scene_description
            assert call_args[0][2] == 'watercolor'  # art_style

    def test_generate_image_with_characters(self, client, app):
        """
        Test generating an image with character profiles for consistency.

        Workflow:
        1. Provide character profiles in request
        2. Generate image
        3. Verify characters are included in image prompt
        """
        story_id = "test-story-456"
        page_num = 2

        with patch.object(
            app.config['SERVICES']['image_generator'],
            'generate_image_for_page',
            new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = "https://example.com/image-with-fox.png"

            response = client.post(
                f'/api/images/stories/{story_id}/pages/{page_num}',
                json={
                    'scene_description': 'Felix the fox discovers a magical tree',
                    'art_style': 'cartoon',
                    'characters': [
                        {
                            'name': 'Felix',
                            'species': 'fox',
                            'physical_description': 'Small orange fox with bright eyes',
                            'clothing': 'Green vest',
                            'distinctive_features': 'Bushy tail',
                            'personality_traits': 'Brave and curious'
                        }
                    ]
                }
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['image_url'] == "https://example.com/image-with-fox.png"

            # Verify character profiles were passed to service
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            character_profiles = call_args[0][1]  # Second argument
            assert len(character_profiles) == 1
            assert character_profiles[0].name == 'Felix'
            assert character_profiles[0].species == 'fox'

    def test_generate_image_missing_scene_description(self, client):
        """Test that missing scene_description returns 400 error"""
        story_id = "test-story-789"
        page_num = 1

        response = client.post(
            f'/api/images/stories/{story_id}/pages/{page_num}',
            json={
                'art_style': 'watercolor'
                # Missing scene_description
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'scene_description' in data['error'].lower()

    def test_generate_image_invalid_json(self, client):
        """Test that invalid JSON returns 400 error"""
        story_id = "test-story-abc"
        page_num = 1

        response = client.post(
            f'/api/images/stories/{story_id}/pages/{page_num}',
            data='not valid json',
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_generate_image_service_error(self, client, app):
        """Test error handling when image service fails"""
        story_id = "test-story-error"
        page_num = 1

        with patch.object(
            app.config['SERVICES']['image_generator'],
            'generate_image_for_page',
            new_callable=AsyncMock
        ) as mock_generate:
            # Mock service failure
            mock_generate.side_effect = Exception("Image generation service unavailable")

            response = client.post(
                f'/api/images/stories/{story_id}/pages/{page_num}',
                json={
                    'scene_description': 'A test scene',
                    'art_style': 'cartoon'
                }
            )

            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data

    def test_bulk_image_generation_returns_guidance(self, client):
        """
        Test that bulk image generation endpoint guides users to project orchestrator.

        The POST /api/images/stories/:id endpoint is intentionally not implemented
        to encourage users to use the project orchestrator for complete workflows.
        """
        story_id = "test-story-bulk"

        response = client.post(f'/api/images/stories/{story_id}')

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'project' in data['error'].lower()
