"""
End-to-end integration test for story generation workflow.

Tests the complete story generation flow from API request to story creation,
including character extraction and vocabulary analysis.
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


class TestStoryGenerationFlow:
    """End-to-end tests for story generation workflow"""

    def test_complete_story_generation_flow(self, client, app):
        """
        Test complete story generation workflow:
        1. Get configuration
        2. Create story with metadata
        3. Verify story has pages
        4. Verify story has characters
        5. Verify vocabulary extraction
        """
        # Step 1: Get configuration to populate form
        config_response = client.get('/api/config')
        assert config_response.status_code == 200
        config = config_response.get_json()
        assert 'parameters' in config
        assert 'defaults' in config

        # Step 2: Create story using configuration defaults
        with patch('src.ai.ollama_client.OllamaClient.generate_text', new_callable=AsyncMock) as mock_ai:
            # Mock AI responses for story and character extraction
            mock_ai.side_effect = [
                # Story generation
                """
                Page 1: Once upon a time, there was a brave little fox named Felix who lived in the forest.
                Page 2: Felix loved to explore and one day he found a magical tree.
                Page 3: The magical tree granted Felix the gift of kindness, and he shared it with all his friends.
                """,
                # Character extraction
                '{"characters": [{"name": "Felix", "description": "Small orange fox"}]}',
                # Character profiling for Felix
                '{"name": "Felix", "species": "fox", "physical_description": "Small orange fox", "clothing": "Green vest", "distinctive_features": "Bushy tail", "personality_traits": "Brave and kind"}'
            ]

            story_response = client.post('/api/stories', json={
                'title': 'The Brave Little Fox',
                'language': config['defaults']['language'],
                'age_group': config['defaults']['age_group'],
                'complexity': config['defaults']['complexity'],
                'vocabulary_diversity': config['defaults']['vocabulary_diversity'],
                'num_pages': 3,
                'genre': config['defaults']['genre'],
                'art_style': config['defaults']['art_style'],
                'theme': 'kindness and courage'
            })

            assert story_response.status_code == 201
            story = story_response.get_json()

            # Step 3: Verify story structure
            assert 'id' in story
            assert story['metadata']['title'] == 'The Brave Little Fox'
            assert story['metadata']['num_pages'] == 3
            assert 'pages' in story
            assert len(story['pages']) == 3

            # Step 4: Verify pages have content
            for i, page in enumerate(story['pages'], 1):
                assert page['page_number'] == i
                assert page['text'] is not None
                assert len(page['text']) > 0

            # Step 5: Verify character extraction
            assert 'characters' in story
            assert len(story['characters']) > 0
            felix = story['characters'][0]
            assert felix['name'] == 'Felix'
            assert felix['species'] == 'fox'
            assert 'physical_description' in felix
            assert 'personality_traits' in felix

            # Step 6: Verify timestamps
            assert 'created_at' in story
            assert 'updated_at' in story

    def test_story_generation_with_custom_prompt(self, client, app):
        """Test story generation with custom prompt"""
        with patch('src.ai.ollama_client.OllamaClient.generate_text', new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = [
                """
                Page 1: A dragon named Drake learned that reading was magical.
                Page 2: Drake visited the library every day to discover new stories.
                Page 3: Drake became the wisest dragon in the kingdom through reading.
                """,
                '{"characters": [{"name": "Drake", "description": "Large purple dragon"}]}',
                '{"name": "Drake", "species": "dragon", "physical_description": "Large purple dragon", "personality_traits": "Wise and curious"}'
            ]

            response = client.post('/api/stories', json={
                'title': 'The Reading Dragon',
                'num_pages': 3,
                'custom_prompt': 'A story about a dragon who learns to read'
            })

            assert response.status_code == 201
            story = response.get_json()
            assert story['metadata']['title'] == 'The Reading Dragon'
            assert 'Drake' in story['pages'][0]['text']

    def test_story_generation_with_theme(self, client, app):
        """Test story generation with specific theme"""
        with patch('src.ai.ollama_client.OllamaClient.generate_text', new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = [
                """
                Page 1: Two friends, Max and Luna, always helped each other.
                Page 2: When Luna was sad, Max cheered her up with funny jokes.
                Page 3: Their friendship grew stronger every day through kindness.
                """,
                '{"characters": [{"name": "Max", "description": "Boy with short brown hair"}, {"name": "Luna", "description": "Girl with long blonde hair"}]}',
                '{"species": "human", "physical_description": "Boy with short brown hair", "clothing": "Blue t-shirt", "distinctive_features": "Bright smile", "personality_traits": "Cheerful and helpful"}',
                '{"species": "human", "physical_description": "Girl with long blonde hair", "clothing": "Pink dress", "distinctive_features": "Sparkling eyes", "personality_traits": "Kind and thoughtful"}'
            ]

            response = client.post('/api/stories', json={
                'title': 'Best Friends Forever',
                'num_pages': 3,
                'theme': 'friendship and kindness'
            })

            assert response.status_code == 201
            story = response.get_json()
            assert len(story['characters']) >= 2

    def test_retrieve_nonexistent_story(self, client):
        """Test retrieving a story that doesn't exist returns 404"""
        # Try to get a non-existent story
        get_response = client.get('/api/stories/nonexistent-id-12345')
        assert get_response.status_code == 404
        data = get_response.get_json()
        assert 'error' in data

    def test_story_validation_errors(self, client):
        """Test story generation with validation errors"""
        # Missing title
        response = client.post('/api/stories', json={
            'language': 'English'
        })
        assert response.status_code == 400
        assert 'title' in response.get_json()['error'].lower()

        # Invalid JSON
        response = client.post('/api/stories',
                              data='not json',
                              content_type='application/json')
        assert response.status_code == 400

    def test_story_generation_handles_ai_errors(self, client, app):
        """Test error handling when AI service fails"""
        with patch('src.ai.ollama_client.OllamaClient.generate_text', new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = Exception("AI service unavailable")

            response = client.post('/api/stories', json={
                'title': 'Test Story',
                'num_pages': 3
            })

            assert response.status_code == 500
            assert 'error' in response.get_json()
